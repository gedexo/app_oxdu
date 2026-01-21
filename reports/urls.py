from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    #Reports
    path('balance-sheet/', views.BalanceSheetReportView.as_view(), name='balance_sheet'),
    path("pnl/", views.PNLReportView.as_view(), name="pnl"),
    path("pnl/group-detail/", views.PNLGroupDetailView.as_view(), name="pnl_group_detail"),
    path("cash_flow/", views.CashFlowReportView.as_view(), name="cash_flow_report"),
    path("ledger/", views.LedgerReportView.as_view(), name="ledger_report"),
    path('trial-balance/', views.TrialBalanceReportView.as_view(), name='trial_balance'),

    #Income expense reports
    path("income-expense-report/", views.IncomeExpenseReportView.as_view(), name="income_expense_report"),

    #Overall Report 
    path("academic-statistics-report/", views.AcademicStatisticsReportView.as_view(), name="academic_statistics_report"),
]