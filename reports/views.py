from collections import defaultdict
from django.conf import settings
from decimal import Decimal
from django.db import models
from datetime import date, datetime, timedelta
from django.urls import reverse_lazy
from django.utils.http import quote
from django.utils import timezone
from typing import Dict, Tuple, List
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q, Sum, Value, DecimalField, Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views import View
from django.db.models.functions import TruncMonth
from branches.models import Branch 
import json
from django.contrib.auth import get_user_model

from core import mixins
from transactions.models import TransactionEntry, Transaction
from accounting.models import Account, GroupMaster 
from reports import tables, filters, forms

from admission.models import Admission
from masters.models import Course
from employees.models import Employee
User = get_user_model()


class BalanceSheetReportView(mixins.HybridTemplateView):
    template_name = 'reports/balance_sheet_report.html'
    permission_required = "transactions.view_balancesheet"
    title = "Balance Sheet"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = "Balance Sheet Report"
        context["is_balance_sheet"] = True
        
        as_of_date_str = self.request.GET.get('as_of_date')
        if not as_of_date_str:
            as_of_date = date.today()
        else:
            try:
                as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
            except ValueError:
                as_of_date = date.today()

        # --- Branch Filtering Logic ---
        branch_filter_param = self.request.GET.get('branch_filter')
        all_branches = Branch.objects.all().order_by('name')
        
        if branch_filter_param == 'all':
            branch = None
        elif branch_filter_param:
            try:
                branch = Branch.objects.get(id=branch_filter_param)
            except Branch.DoesNotExist:
                branch = None
        else:
            # Fallback to session branch if no filter is active
            branch_id = self.request.session.get('branch')
            branch = Branch.objects.filter(id=branch_id).first() if branch_id else None

        # Get balance sheet data
        balance_sheet_data = self.get_balance_sheet_data(branch, as_of_date)
        
        # Calculate totals from account groups
        total_assets = sum([group['amount'] for group in balance_sheet_data['asset_groups']], Decimal('0'))
        total_liabilities = sum([group['amount'] for group in balance_sheet_data['liability_groups']], Decimal('0'))
        total_equity = sum([group['amount'] for group in balance_sheet_data['equity_groups']], Decimal('0'))
        
        # Calculate net profit (Purely based on Ledger entries)
        net_profit = self.calculate_net_profit(branch, as_of_date)
        
        # Total equity including net profit
        total_equity_with_profit = total_equity + net_profit
        total_liabilities_and_equity = total_liabilities + total_equity_with_profit
        
        # Net worth and balance check
        net_worth = total_assets - total_liabilities
        balance_difference = total_assets - total_liabilities_and_equity
        is_balanced = abs(balance_difference) < Decimal('0.01')
        
        # Financial ratios
        current_assets = self.get_group_total_by_locking_group(branch, as_of_date, 'CURRENT_ASSETS')
        current_liabilities = self.get_group_total_by_locking_group(branch, as_of_date, 'CURRENT_LIABILITIES')
        
        current_ratio = Decimal('0')
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
        
        cash_and_bank = (
            self.get_group_total_by_locking_group(branch, as_of_date, 'CASH_ACCOUNT') +
            self.get_group_total_by_locking_group(branch, as_of_date, 'BANK_ACCOUNT')
        )
        receivables = self.get_group_total_by_locking_group(branch, as_of_date, 'SUNDRY_DEBTORS')
        quick_assets = cash_and_bank + receivables
        
        quick_ratio = Decimal('0')
        if current_liabilities > 0:
            quick_ratio = quick_assets / current_liabilities
        
        debt_to_equity_ratio = Decimal('0')
        if total_equity_with_profit > 0:
            debt_to_equity_ratio = total_liabilities / total_equity_with_profit
        
        working_capital = current_assets - current_liabilities
        
        context.update({
            'branch': branch,
            'selected_branch_filter': branch_filter_param,
            'all_branches': all_branches,
            'as_of_date': as_of_date,
            'balance_sheet_data': balance_sheet_data,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity_with_profit,
            'total_liabilities_and_equity': total_liabilities_and_equity,
            'net_worth': net_worth,
            'balance_difference': balance_difference,
            'is_balanced': is_balanced,
            'current_ratio': round(current_ratio, 2),
            'quick_ratio': round(quick_ratio, 2),
            'debt_to_equity_ratio': round(debt_to_equity_ratio, 2),
            'working_capital': working_capital,
            'net_profit': net_profit,
        })
        return context
    
    def get_balance_sheet_data(self, branch, as_of_date):
        """Get balance sheet data for assets, liabilities, and equity"""
        as_of_datetime = datetime.combine(as_of_date, datetime.max.time())
        
        # Transaction filters
        filters = Q(transaction__date__lte=as_of_datetime, transaction__status='posted')
        if branch:
            filters &= Q(transaction__branch=branch)
        if hasattr(Transaction, 'deleted'):
            filters &= Q(transaction__deleted__isnull=True)
        if hasattr(TransactionEntry, 'deleted'):
            filters &= Q(deleted__isnull=True)
        
        # Group filters
        group_base_filter = {'parent__isnull': True}
        if branch:
            group_base_filter['branch'] = branch
        if hasattr(GroupMaster, 'deleted'):
            group_base_filter['deleted__isnull'] = True
        
        # Pre-calculate totals for efficiency
        self._group_totals_cache = self._calculate_all_group_totals(branch, as_of_date)
        
        # Explicit mapping to avoid KeyError
        mapping = {
            'Assets': 'asset_groups',
            'Liabilities': 'liability_groups',
            'Equity': 'equity_groups'
        }
        
        results = {'asset_groups': [], 'liability_groups': [], 'equity_groups': []}
        
        for nature, context_key in mapping.items():
            groups = GroupMaster.objects.filter(nature_of_group=nature, **group_base_filter).order_by('name')
            for group in groups:
                group_data = self.get_group_hierarchy_data(group, filters, as_of_date, nature)
                if group_data and group_data['amount'] != 0:
                    results[context_key].append(group_data)
        
        return results

    def get_group_hierarchy_data(self, group, filters, as_of_date, nature):
        """Recursively build hierarchy data for groups"""
        total_amount = self.get_group_total_amount(group, nature)
        if total_amount == 0:
            return None
        
        children_query = group.get_children()
        if hasattr(GroupMaster, 'deleted'):
            children_query = children_query.filter(deleted__isnull=True)
        
        has_children = children_query.exists()
        
        group_data = {
            'name': group.name,
            'code': group.code,
            'amount': total_amount,
            'is_parent': has_children,
            'accounts': [],
            'subgroups': [],
            'locking_group': getattr(group, 'locking_group', None)
        }
        
        if has_children:
            for child_group in children_query.filter(nature_of_group=nature):
                child_data = self.get_group_hierarchy_data(child_group, filters, as_of_date, nature)
                if child_data and child_data['amount'] != 0:
                    group_data['subgroups'].append(child_data)
        else:
            group_data['accounts'] = self.get_group_accounts_data(group, as_of_date, nature)
        
        return group_data

    def get_group_total_amount(self, group, nature):
        """Retrieves amount from cache"""
        total = self._group_totals_cache.get(group.id, Decimal('0'))
        return total if nature == 'Assets' else -total

    def _calculate_all_group_totals(self, branch, as_of_date):
        """Efficient bottom-up aggregation of balances"""
        account_filter = {}
        if branch:
            account_filter['branch'] = branch
        
        # Get balances up to date
        account_balances = Account.objects.filter(**account_filter).with_balances(date_to=as_of_date).values('under_id', 'current_balance_annotated')
        
        group_totals = defaultdict(Decimal)
        for acc in account_balances:
            group_totals[acc['under_id']] += acc['current_balance_annotated']
        
        group_filter = {}
        if branch:
            group_filter['branch'] = branch
        
        groups = GroupMaster.objects.filter(**group_filter).order_by('-level')
        for group in groups:
            if group.parent_id:
                group_totals[group.parent_id] += group_totals[group.id]
        return group_totals

    def get_group_accounts_data(self, group, as_of_date, nature):
        """Retrieve individual account balances for a group"""
        account_filter = {'under': group}
        if group.branch:
            account_filter['branch'] = group.branch
        
        account_query = Account.objects.filter(**account_filter)
        if hasattr(Account, 'deleted'):
            account_query = account_query.filter(deleted__isnull=True)
        
        group_accounts = account_query.with_balances(date_to=as_of_date).order_by('name')
        accounts_data = []
        
        for account in group_accounts:
            amount = account.current_balance_annotated
            if nature != 'Assets':
                amount = -amount
            
            if amount != 0:
                as_of_date_str = as_of_date.strftime("%d/%m/%Y")
                ledger_url = str(reverse_lazy('reports:ledger_report')) + f'?account={account.id}&as_of_date={quote(as_of_date_str)}'
                accounts_data.append({
                    'id': account.id,
                    'name': account.name,
                    'code': account.code,
                    'amount': amount,
                    'url': ledger_url,
                })
        return accounts_data

    def get_group_total_by_locking_group(self, branch, as_of_date, locking_group):
        """Helper for ratio calculations (Current Assets, etc.)"""
        group_filter = {'locking_group': locking_group}
        if branch:
            group_filter['branch'] = branch
        
        groups = GroupMaster.objects.filter(**group_filter)
        if not groups.exists():
            return Decimal('0')
            
        total = Decimal('0')
        for group in groups:
            # We use the existing cache if available, or calculate fresh
            group_total = self._group_totals_cache.get(group.id, Decimal('0'))
            total += group_total
            
        # Assets are positive debits, Liabilities are positive credits
        if locking_group in ['CURRENT_ASSETS', 'NON_CURRENT_ASSETS', 'CASH_ACCOUNT', 'BANK_ACCOUNT', 'SUNDRY_DEBTORS']:
            return total
        return -total

    def calculate_net_profit(self, branch, as_of_date):
        """Calculates Net Profit based on Income and Expense groups"""
        if as_of_date.month >= 4:
            fiscal_year_start = date(as_of_date.year, 4, 1)
        else:
            fiscal_year_start = date(as_of_date.year - 1, 4, 1)
        
        # Get period totals for P&L
        pnl_totals = self._calculate_all_group_totals_for_period(branch, fiscal_year_start, as_of_date)
        
        # Define locking groups for P&L
        income_codes = ['DIRECT_INCOME', 'INDIRECT_INCOME']
        expense_codes = ['DIRECT_EXPENSES', 'INDIRECT_EXPENSES']
        
        total_income = Decimal('0')
        total_expense = Decimal('0')
        
        # Sum Income (Credit balances are negative in current_balance_annotated, so we negate)
        income_groups = GroupMaster.objects.filter(locking_group__in=income_codes)
        if branch: income_groups = income_groups.filter(branch=branch)
        for g in income_groups:
            total_income += -pnl_totals.get(g.id, Decimal('0'))
            
        # Sum Expenses (Debit balances are positive)
        expense_groups = GroupMaster.objects.filter(locking_group__in=expense_codes)
        if branch: expense_groups = expense_groups.filter(branch=branch)
        for g in expense_groups:
            total_expense += pnl_totals.get(g.id, Decimal('0'))
            
        return total_income - total_expense

    def _calculate_all_group_totals_for_period(self, branch, date_from, date_to):
        """Aggregates balances specifically for a date range (P&L style)"""
        account_filter = {}
        if branch:
            account_filter['branch'] = branch
            
        account_balances = Account.objects.filter(**account_filter).with_balances(
            date_from=date_from, date_to=date_to
        ).values('under_id', 'current_balance_annotated')
        
        group_totals = defaultdict(Decimal)
        for acc in account_balances:
            group_totals[acc['under_id']] += acc['current_balance_annotated']
        
        group_filter = {}
        if branch:
            group_filter['branch'] = branch
        
        groups = GroupMaster.objects.filter(**group_filter).order_by('-level')
        for group in groups:
            if group.parent_id:
                group_totals[group.parent_id] += group_totals[group.id]
        return group_totals


class PNLReportView(mixins.HybridTemplateView):
    template_name = 'reports/pnl_report.html'
    permission_required = "transactions.view_pnlreport"
    title = "Profit & Loss Statement"

    def get_branch_context(self):
        """Returns a Branch object if a specific one is filtered, otherwise None"""
        branch_id = self.request.GET.get('branch_filter')
        if branch_id and branch_id not in ['all', '']:
            try:
                return Branch.objects.get(id=branch_id)
            except (Branch.DoesNotExist, ValueError):
                return None
        return None

    def get(self, request, *args, **kwargs):
        self.form = forms.PNLReportForm(request.GET or None)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_title"] = "Profit & Loss Statement"
        context["is_profit_loss"] = True
        
        # 1. Date and Branch Scope
        date_from, date_to = self._get_date_range()
        branch = self.get_branch_context()
        
        # 2. Data Calculation
        stock_data = {'opening_stock_value': Decimal('0'), 'closing_stock_value': Decimal('0')}
        pnl_data = self.get_main_groups_pnl_data(branch, date_from, date_to, stock_data)
        metrics = self._calculate_financial_metrics(pnl_data)

        # 3. Final Context
        context.update({
            'form': self.form,
            'branch': branch,
            'date_from': date_from,
            'date_to': date_to,
            'pnl_data': pnl_data,
            'total_income': pnl_data['total_income'],
            'total_expense': pnl_data['total_expense'],
            'net_profit': pnl_data['net_profit'],
            'net_profit_abs': abs(pnl_data['net_profit']),
            'ordered_rows': self._prepare_ordered_pnl_rows(pnl_data, metrics),
            **metrics,
        })
        return context

    def _get_date_range(self):
        if self.form.is_valid():
            return self.form.cleaned_data['date_from'], self.form.cleaned_data['date_to']
        today = date.today()
        return today.replace(day=1), today

    def get_main_groups_pnl_data(self, branch, date_from, date_to, stock_data):
        filters = Q(transaction__date__date__gte=date_from, 
                    transaction__date__date__lte=date_to,
                    transaction__status='posted')
        if branch:
            filters &= Q(transaction__branch=branch)

        # Define the structure for P&L
        main_groups = [
            {'name': 'Direct Income', 'code': 'DIRECT_INCOME', 'nature': 'Income'},
            {'name': 'Direct Expenses', 'code': 'DIRECT_EXPENSES', 'nature': 'Expense'},
            {'name': 'Indirect Income', 'code': 'INDIRECT_INCOME', 'nature': 'Income'},
            {'name': 'Indirect Expenses', 'code': 'INDIRECT_EXPENSES', 'nature': 'Expense'},
        ]
        
        results = {'Income': [], 'Expense': []}
        for g in main_groups:
            # We filter GroupMaster by code (locking_group)
            group_objs = GroupMaster.objects.filter(locking_group=g['code'])
            
            # If a specific branch is selected, we only want groups for that branch 
            # (Assuming groups are branch-specific in your DB structure)
            if branch:
                group_objs = group_objs.filter(branch=branch)
            
            total = self.get_group_total_amount(group_objs, filters, g['nature'], branch)
            
            results[g['nature']].append({
                'name': g['name'],
                'code': g['code'],
                'amount': total,
                'group_id': group_objs.first().id if group_objs.exists() else None
            })

        total_inc = sum(i['amount'] for i in results['Income'])
        total_exp = sum(e['amount'] for e in results['Expense'])

        return {
            'income_groups': results['Income'],
            'expense_groups': results['Expense'],
            'total_income': total_inc,
            'total_expense': total_exp,
            'net_profit': total_inc - total_exp
        }

    def get_group_total_amount(self, groups, filters, nature, branch):
        if not groups.exists(): return Decimal('0')
        
        # Get all descendant IDs for the groups
        ids = []
        for g in groups:
            ids.extend(g.get_descendants(include_self=True).values_list('id', flat=True))
        
        # Filter transactions based on accounts under these groups
        acc_filters = Q(under__id__in=ids)
        if branch: acc_filters &= Q(branch=branch)
        
        totals = TransactionEntry.objects.filter(
            filters, 
            account__in=Account.objects.filter(acc_filters)
        ).aggregate(
            dr=Coalesce(Sum('debit_amount'), Value(Decimal('0'))),
            cr=Coalesce(Sum('credit_amount'), Value(Decimal('0')))
        )
        
        if nature == 'Income':
            return totals['cr'] - totals['dr']
        return totals['dr'] - totals['cr']

    def _calculate_financial_metrics(self, pnl_data):
        def get_amt(groups, code):
            return next((x['amount'] for x in groups if x['code'] == code), Decimal('0'))

        d_inc = get_amt(pnl_data['income_groups'], 'DIRECT_INCOME')
        d_exp = get_amt(pnl_data['expense_groups'], 'DIRECT_EXPENSES')
        
        gross_profit = d_inc - d_exp
        net_profit = pnl_data['net_profit']
        total_income = pnl_data['total_income']
        total_expense = pnl_data['total_expense']
        
        return {
            'gross_profit': gross_profit,
            'gross_margin': (gross_profit / d_inc * 100) if d_inc > 0 else 0,
            'net_margin': (net_profit / total_income * 100) if total_income > 0 else 0,
            'income_expense_ratio': round(total_income / total_expense, 2) if total_expense > 0 else total_income,
        }

    def _prepare_ordered_pnl_rows(self, pnl_data, metrics):
        """Constructs a flat list of rows for the template to render sequentially"""
        rows = []
        # Trading Section
        rows.append({'type': 'header', 'name': 'Direct Income', 'nature': 'Income'})
        rows.append({**pnl_data['income_groups'][0], 'type': 'group', 'nature': 'Income'})
        
        rows.append({'type': 'header', 'name': 'Direct Expenses', 'nature': 'Expense'})
        rows.append({**pnl_data['expense_groups'][0], 'type': 'group', 'nature': 'Expense'})
        
        rows.append({'type': 'gross_profit', 'amount': metrics['gross_profit']})
        
        # P&L Section
        rows.append({'type': 'header', 'name': 'Indirect Income', 'nature': 'Income'})
        rows.append({**pnl_data['income_groups'][1], 'type': 'group', 'nature': 'Income'})
        
        rows.append({'type': 'header', 'name': 'Indirect Expenses', 'nature': 'Expense'})
        rows.append({**pnl_data['expense_groups'][1], 'type': 'group', 'nature': 'Expense'})
        
        return rows


class PNLGroupDetailView(View):
    """
    AJAX view to get detailed account breakdown for a P&L group.
    FIXED: Handles "All Branches" by aggregating data based on Locking Group Code.
    """
    
    def get(self, request, *args, **kwargs):
        # Get parameters
        group_id = request.GET.get('group_id')
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')
        branch_filter_param = request.GET.get('branch_filter')
        
        if not all([group_id, date_from_str, date_to_str]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Determine Branch Context
        branch = None
        if branch_filter_param and branch_filter_param not in ['all', '']:
            try:
                branch = Branch.objects.get(id=branch_filter_param)
            except Branch.DoesNotExist:
                return JsonResponse({'error': 'Branch not found'}, status=404)
        
        # Get the reference group
        try:
            ref_group = GroupMaster.objects.get(id=group_id)
        except GroupMaster.DoesNotExist:
            return JsonResponse({'error': 'Group not found'}, status=404)
        
        # -------------------------------------------------------------
        # CRITICAL FIX: Determine Target Group IDs for Aggregation
        # -------------------------------------------------------------
        target_group_ids = []
        
        if branch:
            # If specific branch, get descendants of the specific group ID
            target_group_ids = ref_group.get_descendants(include_self=True).values_list('id', flat=True)
        else:
            # If "All Branches", we must find ALL groups that share the same Code (Locking Group)
            # This handles the case where Branch A and Branch B both have "Direct Expenses"
            if ref_group.locking_group:
                all_matching_groups = GroupMaster.objects.filter(locking_group=ref_group.locking_group)
                if hasattr(GroupMaster, 'deleted'):
                    all_matching_groups = all_matching_groups.filter(deleted__isnull=True)
                
                # Get descendants for ALL matching groups across branches
                for g in all_matching_groups:
                    target_group_ids.extend(g.get_descendants(include_self=True).values_list('id', flat=True))
            else:
                # Fallback if no code (standard behavior)
                target_group_ids = ref_group.get_descendants(include_self=True).values_list('id', flat=True)
        
        # -------------------------------------------------------------
        # Build Filters
        # -------------------------------------------------------------
        
        # Transaction Filters
        tx_filters = Q(
            transaction__date__date__gte=date_from,
            transaction__date__date__lte=date_to,
            transaction__status='posted'
        )
        if branch:
            tx_filters &= Q(transaction__branch=branch)
        
        if hasattr(TransactionEntry, 'deleted'):
            tx_filters &= Q(deleted__isnull=True)
            tx_filters &= Q(transaction__deleted__isnull=True)
            
        # Account Filters
        account_filter = {'under__id__in': target_group_ids}
        if branch:
            account_filter['branch'] = branch
            
        account_query = Account.objects.filter(**account_filter)
        if hasattr(Account, 'deleted'):
            account_query = account_query.filter(deleted__isnull=True)
        
        # We distinct() to get unique accounts. In "All Branches" mode, 
        # this will retrieve accounts from all branches involved in these groups.
        group_accounts = account_query.distinct().order_by('name')
        
        accounts_data = []
        is_income = ref_group.locking_group in ['DIRECT_INCOME', 'INDIRECT_INCOME']
        
        for account in group_accounts:
            totals = TransactionEntry.objects.filter(
                tx_filters,
                account=account
            ).aggregate(
                dr=Coalesce(Sum('debit_amount'), Value(Decimal('0'))),
                cr=Coalesce(Sum('credit_amount'), Value(Decimal('0')))
            )
            
            # P&L Logic: Income (Cr-Dr), Expense (Dr-Cr)
            if is_income:
                amount = totals['cr'] - totals['dr']
            else:
                amount = totals['dr'] - totals['cr']
            
            if amount != 0:
                date_from_str_fmt = date_from.strftime("%d/%m/%Y")
                date_to_str_fmt = date_to.strftime("%d/%m/%Y")
                ledger_url = (
                    str(reverse_lazy('reports:ledger_report')) + 
                    f'?account={account.id}&date_from={quote(date_from_str_fmt)}&date_to={quote(date_to_str_fmt)}'
                )
                
                accounts_data.append({
                    'id': account.id,
                    'name': account.name,
                    'code': account.code,
                    'ledger_type': account.ledger_type,
                    'amount': float(amount),
                    'formatted_amount': f"₹{amount:,.2f}",
                    'url': ledger_url,
                })
        
        # Placeholder for Stock Logic (if implemented in future)
        # Note: In "All Branches" mode, you'd likely want to sum stock values across branches here.
        # Keeping existing placeholder logic for specific branches for now.
        
        return JsonResponse({
            'success': True,
            'group_name': ref_group.name,
            'group_code': ref_group.locking_group,
            'total_accounts': len(accounts_data),
            'accounts': accounts_data
        })


class CashFlowReportView(mixins.HybridTemplateView):
    template_name = 'reports/cashflow_report.html'
    permission_required = "transactions.view_cashflow"
    title = "Cash Flow Statement"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_cash_flow"] = True
        
        date_from, date_to = self._get_date_range()
        branch_id = self.request.GET.get('branch')
        
        selected_branch = None
        if branch_id and branch_id.isdigit():
            try:
                from .models import Branch  
                selected_branch = Branch.objects.get(id=branch_id)
            except:
                pass

        # 2. Fetch Data
        cashflow_data = self.get_cashflow_data(selected_branch, date_from, date_to)
        
        # 3. Extract Totals
        operating_total = cashflow_data.get('operating_cashflow', Decimal('0'))
        investing_total = cashflow_data.get('investing_cashflow', Decimal('0'))
        financing_total = cashflow_data.get('financing_cashflow', Decimal('0'))
        net_cashflow = cashflow_data.get('net_cashflow', Decimal('0'))
        opening_cash = cashflow_data.get('opening_cash', Decimal('0'))
        closing_cash = cashflow_data.get('closing_cash', Decimal('0'))
        
        # 4. Calculate Ratios
        operating_to_cash_ratio = (operating_total / closing_cash * 100) if closing_cash != 0 else Decimal('0')
        cash_growth_rate = (net_cashflow / opening_cash * 100) if opening_cash != 0 else (Decimal('100') if net_cashflow > 0 else Decimal('0'))
        cash_efficiency = (net_cashflow / operating_total * 100) if operating_total != 0 else Decimal('0')
        cash_position_index = (closing_cash / opening_cash * 100) if opening_cash != 0 else Decimal('100')

        # 5. Get all branches for the filter dropdown
        from branches.models import Branch # Adjust import
        all_branches = Branch.objects.all()
        if hasattr(Branch, 'deleted'):
            all_branches = all_branches.filter(deleted__isnull=True)

        context.update({
            'title': 'Cash Flow Statement',
            'all_branches': all_branches,
            'selected_branch': selected_branch,
            'date_from': date_from,
            'date_to': date_to,
            'cashflow_data': cashflow_data,
            'operating_cashflow': operating_total,
            'investing_cashflow': investing_total,
            'financing_cashflow': financing_total,
            'net_cashflow': net_cashflow,
            'opening_cash': opening_cash,
            'closing_cash': closing_cash,
            'net_cashflow_abs': abs(net_cashflow),
            'operating_to_cash_ratio': round(operating_to_cash_ratio, 2),
            'cash_growth_rate': round(cash_growth_rate, 2),
            'cash_efficiency': round(cash_efficiency, 2),
            'cash_position_index': round(cash_position_index, 2),
        })
        
        return context
    
    def _get_date_range(self) -> Tuple[date, date]:
        date_from_str = self.request.GET.get('date_from')
        date_to_str = self.request.GET.get('date_to')
        
        try:
            if date_from_str and date_to_str:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            else:
                today = date.today()
                date_from = date(today.year, 4, 1) if today.month >= 4 else date(today.year - 1, 4, 1)
                date_to = today
        except ValueError:
            today = date.today()
            date_from = date(today.year, 4, 1) if today.month >= 4 else date(today.year - 1, 4, 1)
            date_to = today
        return date_from, date_to

    def get_cashflow_data(self, branch, date_from, date_to):
        cash_accounts = self.get_cash_accounts(branch)
        opening_cash = self.get_opening_cash_balance(branch, cash_accounts, date_from)
        
        operating_data = self.get_category_cashflow(branch, ['Income', 'Expense'], date_from, date_to, 'Operating')
        
        # Investing (Specific Locking Groups)
        investing_groups = ['SHORT_TERM_INVESTMENTS', 'LONG_TERM_INVESTMENTS', 'OFFICE_EQUIPMENT', 'FIXED_ASSETS']
        investing_data = self.get_category_cashflow(branch, ['Assets'], date_from, date_to, 'Investing', investing_groups)
        
        # Financing (Specific Locking Groups)
        financing_groups = ['LONG_TERM_LOANS', 'STAFF_LOANS', 'CAPITAL', 'LOANS_LIABILITY']
        financing_data = self.get_category_cashflow(branch, ['Liabilities', 'Equity'], date_from, date_to, 'Financing', financing_groups)
        
        operating_total = sum([item['amount'] for item in operating_data], Decimal('0'))
        investing_total = sum([item['amount'] for item in investing_data], Decimal('0'))
        financing_total = sum([item['amount'] for item in financing_data], Decimal('0'))
        
        net_cashflow = operating_total + investing_total + financing_total
        closing_cash = opening_cash + net_cashflow
        
        return {
            'operating_activities': operating_data,
            'investing_activities': investing_data,
            'financing_activities': financing_data,
            'operating_cashflow': operating_total,
            'investing_cashflow': investing_total,
            'financing_cashflow': financing_total,
            'net_cashflow': net_cashflow,
            'opening_cash': opening_cash,
            'closing_cash': closing_cash,
        }

    def get_cash_accounts(self, branch):
        group_filter = Q(locking_group__in=['CASH_ACCOUNT', 'BANK_ACCOUNT'])
        if branch:
            group_filter &= Q(branch=branch)
        
        if hasattr(GroupMaster, 'deleted'):
            group_filter &= Q(deleted__isnull=True)
        
        cash_groups = GroupMaster.objects.filter(group_filter)
        all_group_ids = []
        for g in cash_groups:
            all_group_ids.extend(g.get_descendants(include_self=True).values_list('id', flat=True))
        
        account_filter = Q(under_id__in=all_group_ids)
        if branch:
            account_filter &= Q(branch=branch)
        
        return Account.objects.filter(account_filter).distinct()

    def get_opening_cash_balance(self, branch, cash_accounts, date_from):
        dt_start = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
        filters = Q(account__in=cash_accounts, transaction__date__lt=dt_start, transaction__status='posted')
        
        if branch:
            filters &= Q(transaction__branch=branch)
        
        # Soft delete checks
        if hasattr(TransactionEntry, 'deleted'): filters &= Q(deleted__isnull=True)
        if hasattr(Transaction, 'deleted'): filters &= Q(transaction__deleted__isnull=True)
        
        totals = TransactionEntry.objects.filter(filters).aggregate(
            bal=Coalesce(Sum('debit_amount'), Value(0, DecimalField())) - Coalesce(Sum('credit_amount'), Value(0, DecimalField()))
        )
        return totals['bal']

    def get_category_cashflow(self, branch, natures, date_from, date_to, category_label, locking_groups=None):
        group_filter = Q(nature_of_group__in=natures)
        if locking_groups:
            group_filter &= Q(locking_group__in=locking_groups)
        if branch:
            group_filter &= Q(branch=branch)
        
        if hasattr(GroupMaster, 'deleted'): group_filter &= Q(deleted__isnull=True)
        
        groups = GroupMaster.objects.filter(group_filter)
        results = []
        
        dt_from = timezone.make_aware(datetime.combine(date_from, datetime.min.time()))
        dt_to = timezone.make_aware(datetime.combine(date_to, datetime.max.time()))

        for group in groups:
            descendants = group.get_descendants(include_self=True)
            acc_filter = Q(under__in=descendants)
            if branch: acc_filter &= Q(branch=branch)
            
            accounts = Account.objects.filter(acc_filter)
            
            for acc in accounts:
                tx_filter = Q(account=acc, transaction__date__range=(dt_from, dt_to), transaction__status='posted')
                if branch: tx_filter &= Q(transaction__branch=branch)
                
                if hasattr(TransactionEntry, 'deleted'): tx_filter &= Q(deleted__isnull=True)

                totals = TransactionEntry.objects.filter(tx_filter).aggregate(
                    d=Coalesce(Sum('debit_amount'), Value(0, DecimalField())),
                    c=Coalesce(Sum('credit_amount'), Value(0, DecimalField()))
                )
                
                # Logic: Inflow is Credit for Income/Liab, Debit for Assets (Negative impact)
                if group.nature_of_group == 'Income':
                    impact = totals['c'] - totals['d']
                elif group.nature_of_group == 'Expense':
                    impact = -(totals['d'] - totals['c'])
                elif group.nature_of_group == 'Assets':
                    impact = -(totals['d'] - totals['c'])
                else: # Liabilities/Equity
                    impact = totals['c'] - totals['d']
                
                if impact != 0:
                    results.append({
                        'account_name': acc.name,
                        'group_name': group.name,
                        'amount': impact,
                        'category': category_label,
                        'url': f"{reverse_lazy('reports:ledger_report')}?account={acc.id}&date_from={date_from}&date_to={date_to}"
                    })
        return results


class LedgerReportView(mixins.HybridListView):
    model = TransactionEntry
    table_class = tables.LedgerTable
    template_name = 'reports/ledger_report.html'
    context_object_name = 'entries'
    filterset_class = filters.LedgerFilter
    title = "Ledger Report"

    def get_queryset(self):
        """Get transaction entries with branch and scope filtering"""
        queryset = (
            super()
            .get_queryset()
            .filter(transaction__status='posted')
            .select_related('transaction', 'transaction__branch', 'account')
            .order_by('-transaction__date', 'transaction__voucher_number', 'id')
        )

        # 1. Get Branch Filter from Request
        self.branch_id = self.request.GET.get('branch')
        
        # Apply Branch Filter to Queryset if selected
        if self.branch_id:
            queryset = queryset.filter(transaction__branch_id=self.branch_id)

        # Initialize default values
        self.account = None
        self.date_from = None
        self.date_to = None

        # Apply filterset
        # Note: We don't pass 'request' or 'company' as arguments anymore if your filter doesn't strictly require them
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)

        # --- FIX: OVERRIDE ACCOUNT QUERYSET FOR VALIDATION ---
        # This fixes the "Select a valid choice" error. 
        # We ensure the form accepts any account ID, while the UI restricts the list visually.
        if 'account' in self.filterset.form.fields:
            self.filterset.form.fields['account'].queryset = Account.objects.all()
        # -----------------------------------------------------

        if self.filterset.is_valid():
            # Check if account is selected
            selected_account = self.filterset.form.cleaned_data.get('account')
            if not selected_account:
                return queryset.none()

            self.account = selected_account
            self.date_from = self.filterset.form.cleaned_data.get('date_from')
            self.date_to = self.filterset.form.cleaned_data.get('date_to')

            queryset = self.filterset.qs
        else:
            return queryset.none()

        return queryset

    def get_table(self, **kwargs):
        """Calculate balance data before creating the table"""
        balance_data = {}

        if self.account:
            # --- 1. Calculate Opening Balance ---
            if self.date_from:
                # Build filters for opening balance calculation
                opening_filters = Q(
                    account=self.account,
                    transaction__date__lt=self.date_from,
                    transaction__status='posted'
                )

                # CRITICAL: Apply Branch Filter to Opening Balance logic
                if self.branch_id:
                    opening_filters &= Q(transaction__branch_id=self.branch_id)
                
                # Add soft-delete filters
                if hasattr(TransactionEntry, 'deleted'):
                    opening_filters &= Q(deleted__isnull=True)
                if hasattr(Transaction, 'deleted'):
                    opening_filters &= Q(transaction__deleted__isnull=True)
                
                opening_totals = TransactionEntry.objects.filter(
                    opening_filters
                ).aggregate(
                    total_debit=Coalesce(Sum('debit_amount'), Value(Decimal('0')), output_field=DecimalField()),
                    total_credit=Coalesce(Sum('credit_amount'), Value(Decimal('0')), output_field=DecimalField())
                )
                
                opening_debit = opening_totals['total_debit']
                opening_credit = opening_totals['total_credit']
            else:
                opening_debit = Decimal('0')
                opening_credit = Decimal('0')

            opening_balance = opening_debit - opening_credit

            # --- 2. Calculate Running Balance ---
            # Get all entries for this account to calculate running balance
            all_entries_query = TransactionEntry.objects.filter(
                account=self.account,
                transaction__status='posted'
            )
            
            # Apply Branch Filter to Running Balance logic
            if self.branch_id:
                all_entries_query = all_entries_query.filter(transaction__branch_id=self.branch_id)

            # Add soft-delete filters
            if hasattr(TransactionEntry, 'deleted'):
                all_entries_query = all_entries_query.filter(deleted__isnull=True)
            if hasattr(Transaction, 'deleted'):
                all_entries_query = all_entries_query.filter(transaction__deleted__isnull=True)
            
            # Add date filtering
            if self.date_from:
                all_entries_query = all_entries_query.filter(transaction__date__gte=self.date_from)
            if self.date_to:
                all_entries_query = all_entries_query.filter(transaction__date__lte=self.date_to)
            
            # Order chronologically
            chronological_entries = all_entries_query.select_related('transaction').order_by(
                'transaction__date', 
                'transaction__voucher_number', 
                'id'
            )
            
            # Calculate running balance
            running_balance = opening_balance
            for entry in chronological_entries:
                running_balance += Decimal(str(entry.debit_amount)) - Decimal(str(entry.credit_amount))
                balance_data[entry.pk] = running_balance

        # Create table with balance data
        table = self.table_class(self.get_queryset(), balance_data=balance_data, **kwargs)
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_ledger_report"] = True
        
        # --- 1. Load Branches for Dropdown ---
        branches = Branch.objects.all().order_by('name')
        
        # --- 2. Filter Available Accounts based on selected Branch ---
        account_filter = {}
        
        if self.branch_id:
            # If a branch is selected, show accounts for that branch 
            # OR accounts with no branch (Global accounts) if your logic requires it.
            # Here we filter strictly by branch based on your request.
            account_filter['branch_id'] = self.branch_id

        # Add soft-delete filter if applicable
        if hasattr(Account, 'deleted'):
            account_filter['deleted__isnull'] = True

        all_accounts = Account.objects.filter(**account_filter).order_by('name')

        # --- 3. Initialize Filterset if not present ---
        if not hasattr(self, 'filterset'):
            queryset = super().get_queryset().select_related(
                'transaction', 
                'transaction__branch',
                'account'
            )
            self.filterset = self.filterset_class(self.request.GET, queryset=queryset)

        # Update context common elements
        context.update({
            'branches': branches,
            'selected_branch_id': int(self.branch_id) if self.branch_id else None,
            'all_accounts': all_accounts,
            'filter_form': self.filterset.form,
        })

        if not self.account:
            context.update({
                'selected_account_id': None, 
                'no_account_selected': True,
            })
            return context

        try:
            # --- 4. Calculate Aggregates with Branch Filtering ---
            
            # Opening Balance Filters
            if self.date_from:
                opening_filters = Q(
                    account=self.account,
                    transaction__date__lt=self.date_from,
                    transaction__status='posted'
                )

                if self.branch_id:
                    opening_filters &= Q(transaction__branch_id=self.branch_id)
                
                if hasattr(TransactionEntry, 'deleted'):
                    opening_filters &= Q(deleted__isnull=True)
                if hasattr(Transaction, 'deleted'):
                    opening_filters &= Q(transaction__deleted__isnull=True)
                
                opening_totals = TransactionEntry.objects.filter(
                    opening_filters
                ).aggregate(
                    total_debit=Coalesce(Sum('debit_amount'), Value(Decimal('0')), output_field=DecimalField()),
                    total_credit=Coalesce(Sum('credit_amount'), Value(Decimal('0')), output_field=DecimalField())
                )
                
                opening_debit = opening_totals['total_debit']
                opening_credit = opening_totals['total_credit']
            else:
                opening_debit = Decimal('0')
                opening_credit = Decimal('0')

            opening_balance = opening_debit - opening_credit

            # Period totals (queryset is already branch-filtered in get_queryset)
            period_totals = self.get_queryset().aggregate(
                total_debit=Coalesce(Sum('debit_amount'), Value(Decimal('0')), output_field=DecimalField()),
                total_credit=Coalesce(Sum('credit_amount'), Value(Decimal('0')), output_field=DecimalField())
            )
            
            closing_balance = opening_balance + period_totals['total_debit'] - period_totals['total_credit']

            # --- 5. Draft Entries with Branch Filtering ---
            draft_filters = Q(
                account=self.account,
                transaction__status='draft'
            )

            if self.branch_id:
                draft_filters &= Q(transaction__branch_id=self.branch_id)
            
            if hasattr(TransactionEntry, 'deleted'):
                draft_filters &= Q(deleted__isnull=True)
            if hasattr(Transaction, 'deleted'):
                draft_filters &= Q(transaction__deleted__isnull=True)
            
            draft_entries_query = TransactionEntry.objects.filter(draft_filters)
            
            if self.date_from:
                draft_entries_query = draft_entries_query.filter(transaction__date__gte=self.date_from)
            if self.date_to:
                draft_entries_query = draft_entries_query.filter(transaction__date__lte=self.date_to)
            
            draft_entries = draft_entries_query.select_related(
                'transaction'
            ).order_by('-transaction__date', 'transaction__voucher_number', 'id')
            
            draft_totals = draft_entries.aggregate(
                total_debit=Coalesce(Sum('debit_amount'), Value(Decimal('0')), output_field=DecimalField()),
                total_credit=Coalesce(Sum('credit_amount'), Value(Decimal('0')), output_field=DecimalField())
            )
            
            draft_count = draft_entries.count()

            context.update({
                'account': self.account,
                'selected_account_id': self.account.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'opening_balance_abs': abs(opening_balance),
                'closing_balance_abs': abs(closing_balance),
                'total_debit': period_totals['total_debit'],
                'total_credit': period_totals['total_credit'],
                'transaction_types': dict(Transaction.TRANSACTION_TYPE_CHOICES),
                'draft_entries': draft_entries,
                'draft_count': draft_count,
                'draft_total_debit': draft_totals['total_debit'],
                'draft_total_credit': draft_totals['total_credit'],
            })

        except Exception as e:
            messages.error(self.request, f"Error generating report: {str(e)}")
            context['error'] = True

        return context

    
class TrialBalanceReportView(mixins.HybridListView):
    model = Account
    table_class = tables.TrialBalanceTable
    filterset_class = filters.TrialBalanceFilter
    template_name = "reports/trial_balance.html"
    title = "Trial Balance"
    permission_required = 'transactions.view_balancesheet'
    
    paginate_by = None
    export_name = 'trial_balance'

    def get_queryset(self):
        # Base queryset optimized with select_related
        return super().get_queryset().select_related('under').order_by('under__name', 'code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_trail_balance"] = True
        context["branches"] = Branch.objects.filter(is_active=True)
        
        # 1. Date range calculation
        date_from, date_to = self._get_date_range()
        
        # 2. Process data (Calculates all balances in optimized queries)
        accounts = self.get_processed_data(date_from, date_to)
        
        # 3. Calculate grand totals for the footer
        totals = self._calculate_totals(accounts)
        
        context.update({
            'date_from': date_from,
            'date_to': date_to,
            'accounts': accounts,
            'totals': totals,
            'is_balanced': abs(totals['closing_debit'] - totals['closing_credit']) < Decimal('0.01'),
            'difference': abs(totals['closing_debit'] - totals['closing_credit']),
            'summary_by_nature': self._get_summary_by_nature(accounts),
            'show_grouped': self.request.GET.get('show_grouped') == 'true',
            'total_accounts': len([acc for acc in accounts if not getattr(acc, 'is_group_total', False)])
        })
        
        # If using django-tables2, sync the processed data
        if hasattr(context, 'table'):
            context['table'].data = accounts
            
        return context

    def get_processed_data(self, date_from, date_to):
        """
        Uses Django Annotations to fetch Opening and Period balances.
        Replaces 'entries' with the correct reverse lookup 'transactionentry'.
        """
        # Get filtered queryset from the FilterSet (respects Branch/Nature filters)
        self.filterset = self.get_filterset(self.filterset_class)
        queryset = self.filterset.qs
        
        # Get selected branch from request for transaction-level filtering
        selected_branch = self.request.GET.get('branch')

        # Helper function to build the filter for Sum aggregates
        def get_sum_filter(extra_q):
            # Base condition: Only posted transactions
            q = Q(transactionentry__transaction__status='posted') & extra_q
            # Add branch filter to transaction entries if branch is selected
            if selected_branch:
                q &= Q(transactionentry__transaction__branch_id=selected_branch)
            return q

        # Annotated Query: One hit to DB to get all sums
        annotated_qs = queryset.annotate(
            # Opening: Sum before date_from
            op_debit=Coalesce(Sum('transactionentry__debit_amount', filter=get_sum_filter(Q(transactionentry__transaction__date__lt=date_from))), Value(0, output_field=DecimalField())),
            op_credit=Coalesce(Sum('transactionentry__credit_amount', filter=get_sum_filter(Q(transactionentry__transaction__date__lt=date_from))), Value(0, output_field=DecimalField())),
            
            # Period: Sum within range
            p_debit=Coalesce(Sum('transactionentry__debit_amount', filter=get_sum_filter(Q(transactionentry__transaction__date__range=(date_from, date_to)))), Value(0, output_field=DecimalField())),
            p_credit=Coalesce(Sum('transactionentry__credit_amount', filter=get_sum_filter(Q(transactionentry__transaction__date__range=(date_from, date_to)))), Value(0, output_field=DecimalField())),
        )

        processed_accounts = []
        show_zero_balance = self.request.GET.get('show_zero_balance') == 'true'

        for acc in annotated_qs:
            # Calculate Opening Net
            net_opening = acc.op_debit - acc.op_credit
            acc.opening_debit_amount = max(net_opening, Decimal('0'))
            acc.opening_credit_amount = max(-net_opening, Decimal('0'))
            
            # Period movements
            acc.period_debit_amount = acc.p_debit
            acc.period_credit_amount = acc.p_credit
            
            # Calculate Closing Net (Opening + Period)
            net_closing = net_opening + (acc.p_debit - acc.p_credit)
            acc.closing_debit_amount = max(net_closing, Decimal('0'))
            acc.closing_credit_amount = max(-net_closing, Decimal('0'))

            # Visibility check
            has_balance = (
                acc.opening_debit_amount > 0 or acc.opening_credit_amount > 0 or
                acc.period_debit_amount > 0 or acc.period_credit_amount > 0 or
                acc.closing_debit_amount > 0 or acc.closing_credit_amount > 0
            )

            if show_zero_balance or has_balance:
                processed_accounts.append(acc)

        if self.request.GET.get('show_grouped') == 'true':
            return self._group_accounts_by_parent(processed_accounts)
        
        return processed_accounts

    def _group_accounts_by_parent(self, accounts):
        """Groups flat accounts under their GroupMaster names with totals"""
        grouped_list = []
        groups = defaultdict(list)
        
        for acc in accounts:
            group_name = acc.under.name if acc.under else 'Uncategorized'
            groups[group_name].append(acc)
            
        for group_name in sorted(groups.keys()):
            group_accs = groups[group_name]
            for acc in group_accs:
                acc.indent_level = 1
                grouped_list.append(acc)
            
            # Add a dynamic Total row for this group
            grouped_list.append(self._create_group_total(group_name, group_accs))
                
        return grouped_list

    def _get_date_range(self):
        """Extracts dates and ensures they are timezone aware"""
        date_from_str = self.request.GET.get('date_from')
        date_to_str = self.request.GET.get('date_to')
        
        try:
            if date_from_str and date_to_str:
                df = datetime.strptime(date_from_str, '%Y-%m-%d')
                dt = datetime.strptime(date_to_str, '%Y-%m-%d')
            else:
                # Default to current financial year (Starting April)
                today = datetime.now()
                if today.month >= 4:
                    df = datetime(today.year, 4, 1)
                else:
                    df = datetime(today.year - 1, 4, 1)
                dt = today
            
            return timezone.make_aware(df.replace(hour=0, minute=0, second=0)), \
                   timezone.make_aware(dt.replace(hour=23, minute=59, second=59))
        except ValueError:
            # Fallback
            return timezone.now().replace(hour=0, minute=0), timezone.now()

    def _calculate_totals(self, accounts):
        t = {k: Decimal('0') for k in ['opening_debit', 'opening_credit', 'period_debit', 'period_credit', 'closing_debit', 'closing_credit']}
        for acc in accounts:
            if getattr(acc, 'is_group_total', False):
                continue
            t['opening_debit'] += acc.opening_debit_amount
            t['opening_credit'] += acc.opening_credit_amount
            t['period_debit'] += acc.period_debit_amount
            t['period_credit'] += acc.period_credit_amount
            t['closing_debit'] += acc.closing_debit_amount
            t['closing_credit'] += acc.closing_credit_amount
        return t

    def _create_group_total(self, group_name, accounts):
        total = Account(name=f"Total {group_name}")
        total.is_group_total = True
        total.indent_level = 0
        total.opening_debit_amount = sum(a.opening_debit_amount for a in accounts)
        total.opening_credit_amount = sum(a.opening_credit_amount for a in accounts)
        total.period_debit_amount = sum(a.period_debit_amount for a in accounts)
        total.period_credit_amount = sum(a.period_credit_amount for a in accounts)
        total.closing_debit_amount = sum(a.closing_debit_amount for a in accounts)
        total.closing_credit_amount = sum(a.closing_credit_amount for a in accounts)
        return total

    def _get_summary_by_nature(self, accounts):
        summary = {}
        for acc in accounts:
            if getattr(acc, 'is_group_total', False): continue
            nature = acc.under.nature_of_group if acc.under else 'Other'
            if nature not in summary:
                summary[nature] = {'closing_debit': Decimal('0'), 'closing_credit': Decimal('0'), 'count': 0}
            
            summary[nature]['closing_debit'] += acc.closing_debit_amount
            summary[nature]['closing_credit'] += acc.closing_credit_amount
            summary[nature]['count'] += 1
        return summary

    
class IncomeExpenseReportView(mixins.HybridTemplateView):
    template_name = "reports/income_expense_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["is_income_expense_report"] = True
        context["report_title"] = "Income & Expense Analysis"

        # ---------------------------------------------------------
        # 1. Get Filter Parameters from Request
        # ---------------------------------------------------------
        branch_id = self.request.GET.get('branch')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # ---------------------------------------------------------
        # 2. Build the Base Query
        # ---------------------------------------------------------
        # Only fetch posted transactions
        transactions = Transaction.objects.filter(status='posted')

        # Apply Branch Filter (If selected)
        if branch_id:
            transactions = transactions.filter(branch_id=branch_id)
            context['selected_branch'] = int(branch_id)
        
        # Apply Date Filter
        current_date = timezone.now()
        
        if start_date and end_date:
            # Custom Date Range
            transactions = transactions.filter(date__date__gte=start_date, date__date__lte=end_date)
            display_period = f"{start_date} to {end_date}"
        else:
            # Default: Current Year
            current_year = current_date.year
            transactions = transactions.filter(date__year=current_year)
            display_period = str(current_year)
            
            # Set default dates for the template inputs
            start_date = f"{current_year}-01-01"
            end_date = f"{current_year}-12-31"

        # ---------------------------------------------------------
        # 3. Aggregate Data (Group by Month)
        # ---------------------------------------------------------
        income_qs = transactions.filter(
            transaction_type='income'
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')

        expense_qs = transactions.filter(
            transaction_type='expense'
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')

        # ---------------------------------------------------------
        # 4. Process Data for Charts (12 Months Mapping)
        # ---------------------------------------------------------
        months_label = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        
        # Initialize arrays with 0
        income_data = [0] * 12
        expense_data = [0] * 12
        profit_data = [0] * 12

        # Map Income Data
        for item in income_qs:
            if item['month']:
                # month is 1-12, array index is 0-11
                month_idx = item['month'].month - 1
                income_data[month_idx] = float(item['total'] or 0)

        # Map Expense Data
        for item in expense_qs:
            if item['month']:
                month_idx = item['month'].month - 1
                expense_data[month_idx] = float(item['total'] or 0)

        # Calculate Profit (Income - Expense) per month
        for i in range(12):
            profit_data[i] = income_data[i] - expense_data[i]

        # Calculate Grand Totals
        total_income = sum(income_data)
        total_expense = sum(expense_data)
        total_profit = total_income - total_expense

        # ---------------------------------------------------------
        # 5. Update Context
        # ---------------------------------------------------------
        context.update({
            "current_year": display_period,
            "branches": Branch.objects.all(), # Pass branches for dropdown
            
            # Filter values to keep inputs populated
            "start_date": start_date,
            "end_date": end_date,
            
            # Totals
            "total_income": total_income,
            "total_expense": total_expense,
            "net_profit": total_profit,
            
            # Chart Data
            "chart_labels": json.dumps(months_label),
            "income_series": json.dumps(income_data),
            "expense_series": json.dumps(expense_data),
            "profit_series": json.dumps(profit_data),
        })

        return context

    
class AcademicStatisticsReportView(mixins.OpenView):
    template_name = "reports/academic_statistics_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_title"] = "Academic Overview"

        # 1. BASE ACTIVE STUDENTS
        students = Admission.objects.filter(
            is_active=True,
            stage_status="active"
        )
        context["total_students"] = students.count()
        context["pusher_key"] = settings.PUSHER_KEY

        # --------------------------------------------------
        # 2. TELECALLER STATS (TOP 6 ACTIVE TELECALLERS)
        # --------------------------------------------------
        telecaller_stats = Employee.objects.filter(
            user__is_active=True,
            status="Appointed"
        ).filter(
            Q(user__usertype="tele_caller") |
            Q(is_also_tele_caller="Yes")
        ).annotate(
            active_count=Count(
                'user__admission',
                filter=Q(
                    user__admission__is_active=True,
                    user__admission__stage_status='active'
                ),
                distinct=True
            )
        ).filter(
            active_count__gt=0
        ).select_related(
            'user', 'branch'
        ).order_by('-active_count')[:6]

        context["telecaller_stats"] = telecaller_stats

        # --------------------------------------------------
        # 3. BRANCH-WISE STATS
        # --------------------------------------------------
        active_courses = Course.objects.filter(
            is_active=True
        ).order_by('name')

        branch_stats_data = []
        all_branches = Branch.objects.filter(is_active=True)

        for branch in all_branches:
            branch_students = students.filter(branch=branch)

            branch_courses = active_courses.annotate(
                branch_course_count=Count(
                    'admission',
                    filter=Q(
                        admission__branch=branch,
                        admission__is_active=True,
                        admission__stage_status='active'
                    ),
                    distinct=True
                )
            ).order_by('name')

            branch_stats_data.append({
                "branch_obj": branch,
                "total": branch_students.count(),
                "courses": branch_courses,
            })

        branch_stats_data.sort(
            key=lambda x: x["total"],
            reverse=True
        )

        context["branch_stats"] = branch_stats_data

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, "reports/partials/dashboard_stats_content.html", context)
        
        return render(request, self.template_name, context)