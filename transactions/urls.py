from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    #ajax 
    path('ajax/load-party-accounts/', views.load_party_accounts, name='load_party_accounts'),
    path('ajax/load-category-accounts/', views.load_category_accounts, name='load_category_accounts'),

    #Transaction URLs
    path("", views.TransactionListView.as_view(), name="transaction_list"),
    path("transaction/<str:pk>/", views.TransactionDetailView.as_view(), name="transaction_detail"),
    path("new/transaction/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("update/transaction/<str:pk>/", views.TransactionUpdateView.as_view(), name="transaction_update"),
    path("delete/transaction/<str:pk>/", views.TransactionDeleteView.as_view(), name="transaction_delete"),

    # Journal Voucher URLs
    path('journal-vouchers/', views.JournalVoucherListView.as_view(), name='journalvoucher_list'),
    path('journal-vouchers/create/', views.JournalVoucherCreateView.as_view(), name='journalvoucher_create'),
    path('journal-vouchers/<int:pk>/edit/', views.JournalVoucherUpdateView.as_view(), name='journalvoucher_update'),
    path('journal-vouchers/<int:pk>/delete/', views.JournalVoucherDeleteview.as_view(), name='journalvoucher_delete'),

    # Contra Voucher URLs
    path('contravoucher/', views.ContraVoucherListView.as_view(), name='contravoucher_list'),
    path('contravoucher/create/', views.ContraVoucherCreateView.as_view(), name='contravoucher_create'),
    path('contravoucher/<int:pk>/', views.ContraVoucherDetailView.as_view(), name='contravoucher_detail'),
    path('contravoucher/<int:pk>/update/', views.ContraVoucherUpdateView.as_view(), name='contravoucher_update'),
    path('contravoucher/<int:pk>/delete/', views.ContraVoucherDeleteView.as_view(), name='contravoucher_delete'),

    # Income URLs
    path('incomes/', views.IncomeListView.as_view(), name='income_list'),
    path('incomes/create/', views.IncomeExpenseCreateView.as_view(), name='income_create'),
    path('incomes/<int:pk>/detail/', views.IncomeExpenseDetailView.as_view(), name='income_detail'),
    path('incomes/<int:pk>/edit/', views.IncomeExpenseUpdateView.as_view(), name='income_update'),
    path('incomes/<int:pk>/delete/', views.IncomeExpenseDeleteView.as_view(), name='income_delete'),
    
    # Expense URLs
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/create/', views.IncomeExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/detail/', views.IncomeExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.IncomeExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.IncomeExpenseDeleteView.as_view(), name='expense_delete'),
    
    # Income & Expense Report
    path('income-expense-report/', views.IncomeExpenseReportView.as_view(), name='income_expense_report'),
]   
