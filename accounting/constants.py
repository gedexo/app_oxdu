# accounting/constants.py

# === 1. ACCOUNT GROUP CHOICES ===
ACCOUNT_GROUP_CHOICES = [
    # ASSETS
    ('CURRENT_ASSETS', 'Current Assets'),
    ('SUNDRY_DEBTORS', 'Sundry Debtors'),
    ('STUDENTS', 'Students'),
    ('BANK_ACCOUNT', 'Bank Account'),
    ('CASH_ACCOUNT', 'Cash Account'),
    ('NON_CURRENT_ASSETS', 'Non-Current Assets'),
    ('FIXED_ASSETS', 'Fixed Assets'),
    ('SECURITY_DEPOSITS', 'Security Deposits'),
    
    # LIABILITIES
    ('CURRENT_LIABILITIES', 'Current Liabilities'),
    ('SUNDRY_CREDITORS', 'Sundry Creditors'),
    ('NON_CURRENT_LIABILITIES', 'Non-Current Liabilities'),
    ('PROVISIONS', 'Provisions'),
    
    # EQUITY
    ('CAPITAL', 'Capital'),
    ('RESERVES_SURPLUS', 'Reserves & Surplus'),
    
    # INCOME
    ('DIRECT_INCOME', 'Direct Income'),
    ('FEE_INCOME', 'Fee Income (Direct)'),
    ('INDIRECT_INCOME', 'Indirect Income'),
    ('OTHER_INCOME', 'Other Income (Indirect)'),
    
    # EXPENSES
    ('DIRECT_EXPENSES', 'Direct Expenses'),
    ('ACADEMIC_EXPENSES', 'Academic Expenses'),
    ('INDIRECT_EXPENSES', 'Indirect Expenses'),
    ('ADMINISTRATIVE_EXPENSES', 'Administrative Expenses'),
    ('OPERATIONAL_EXPENSES', 'Operational Expenses'),
    ('MARKETING_EXPENSES', 'Marketing Expenses'),
    ('FINANCIAL_EXPENSES', 'Financial Expenses'),
    
    # SPECIAL
    ('SPECIAL_ACCOUNTS', 'Special Accounts'),
    ('ADJUSTMENT_ACCOUNTS', 'Adjustment Accounts'),
]

# === 2. GROUP HIERARCHY (Parents) ===
GROUP_HIERARCHY = {
    'CURRENT_ASSETS': None,
    'SUNDRY_DEBTORS': 'CURRENT_ASSETS',
    'STUDENTS': 'SUNDRY_DEBTORS',
    'BANK_ACCOUNT': 'CURRENT_ASSETS',
    'CASH_ACCOUNT': 'CURRENT_ASSETS',
    'NON_CURRENT_ASSETS': None,
    'FIXED_ASSETS': 'NON_CURRENT_ASSETS',
    'SECURITY_DEPOSITS': 'NON_CURRENT_ASSETS',
    
    'CURRENT_LIABILITIES': None,
    'SUNDRY_CREDITORS': 'CURRENT_LIABILITIES',
    'NON_CURRENT_LIABILITIES': None,
    'PROVISIONS': 'NON_CURRENT_LIABILITIES',
    
    'CAPITAL': None,
    'RESERVES_SURPLUS': 'CAPITAL',
    
    'DIRECT_INCOME': None,
    'FEE_INCOME': 'DIRECT_INCOME',
    'INDIRECT_INCOME': None,
    'OTHER_INCOME': 'INDIRECT_INCOME',

    'DIRECT_EXPENSES': None,
    'ACADEMIC_EXPENSES': 'DIRECT_EXPENSES',
    'INDIRECT_EXPENSES': None,
    'ADMINISTRATIVE_EXPENSES': 'INDIRECT_EXPENSES',
    'OPERATIONAL_EXPENSES': 'INDIRECT_EXPENSES',
    'MARKETING_EXPENSES': 'INDIRECT_EXPENSES',
    'FINANCIAL_EXPENSES': 'INDIRECT_EXPENSES',
    
    'SPECIAL_ACCOUNTS': None,
    'ADJUSTMENT_ACCOUNTS': 'SPECIAL_ACCOUNTS',
}

# === 3. GROUP CATEGORIES ===
GROUP_CATEGORIES = {
    'CURRENT_ASSETS': 'Assets', 'SUNDRY_DEBTORS': 'Assets', 'STUDENTS': 'Assets',
    'BANK_ACCOUNT': 'Assets', 'CASH_ACCOUNT': 'Assets', 'NON_CURRENT_ASSETS': 'Assets',
    'FIXED_ASSETS': 'Assets', 'SECURITY_DEPOSITS': 'Assets',
    
    'CURRENT_LIABILITIES': 'Liabilities', 'SUNDRY_CREDITORS': 'Liabilities',
    'NON_CURRENT_LIABILITIES': 'Liabilities', 'PROVISIONS': 'Liabilities',
    
    'CAPITAL': 'Equity', 'RESERVES_SURPLUS': 'Equity',
    
    'DIRECT_INCOME': 'Income', 'FEE_INCOME': 'Income',
    'INDIRECT_INCOME': 'Income', 'OTHER_INCOME': 'Income',
    
    'DIRECT_EXPENSES': 'Expense', 'ACADEMIC_EXPENSES': 'Expense',
    'INDIRECT_EXPENSES': 'Expense', 'ADMINISTRATIVE_EXPENSES': 'Expense',
    'OPERATIONAL_EXPENSES': 'Expense', 'MARKETING_EXPENSES': 'Expense',
    'FINANCIAL_EXPENSES': 'Expense',
    
    'SPECIAL_ACCOUNTS': 'Assets', # Technically usually assets/liabilities mixed, putting Assets for safety
    'ADJUSTMENT_ACCOUNTS': 'Assets',
}

CATEGORY_TO_MAIN_GROUP = {
    'Assets': 'balance_sheet', 
    'Liabilities': 'balance_sheet', 
    'Equity': 'balance_sheet', 
    'Income': 'profit_and_loss', 
    'Expense': 'profit_and_loss',
}

# === 4. LOCKED ACCOUNTS & MAPPINGS ===
LOCKED_ACCOUNT_CHOICES = [
    ('CASH_ON_HAND', 'Cash on Hand'),
    ('MAIN_BANK_ACCOUNT', 'Main Bank Account'),
    ('FEES_RECEIVABLE', 'Fees Receivable'),
    ('SUNDRY_CREDITORS', 'Sundry Creditors (Control)'),
    ('TUITION_FEE', 'Tuition Fee'),
    ('TEACHING_STAFF_SALARY', 'Teaching Staff Salary'),
    ('NON_TEACHING_SALARY', 'Non-Teaching Staff Salary'),
    ('CAMPUS_RENT', 'Campus/Office Rent'),
    ('ELECTRICITY_EXPENSE', 'Electricity Charges'),
    ('ROUNDING_OFF', 'Rounding Off'),
    ('SUSPENSE_ACCOUNT', 'Suspense Account'),
]

ACCOUNT_TO_GROUP_MAPPING = {
    'CASH_ON_HAND': 'CASH_ACCOUNT',
    'MAIN_BANK_ACCOUNT': 'BANK_ACCOUNT',
    'FEES_RECEIVABLE': 'STUDENTS',
    'SUNDRY_CREDITORS': 'SUNDRY_CREDITORS',
    'TUITION_FEE': 'FEE_INCOME',              # Fixed: Was mapped to self in your snippet
    'TEACHING_STAFF_SALARY': 'ACADEMIC_EXPENSES', # Fixed: Was mapped to self
    'NON_TEACHING_SALARY': 'ADMINISTRATIVE_EXPENSES',
    'CAMPUS_RENT': 'OPERATIONAL_EXPENSES',
    'ELECTRICITY_EXPENSE': 'OPERATIONAL_EXPENSES',
    'ROUNDING_OFF': 'ADJUSTMENT_ACCOUNTS',
    'SUSPENSE_ACCOUNT': 'SPECIAL_ACCOUNTS',
}

ACCOUNT_CODE_MAPPING = {
    'CASH_ON_HAND': '10001',
    'MAIN_BANK_ACCOUNT': '11001',
    'FEES_RECEIVABLE': '12001',
    'SUNDRY_CREDITORS': '20001',
    'TUITION_FEE': '40001',
    'TEACHING_STAFF_SALARY': '50001',
    'NON_TEACHING_SALARY': '55001',
    'CAMPUS_RENT': '55002',
    'ELECTRICITY_EXPENSE': '55003',
    'ROUNDING_OFF': '90001',
    'SUSPENSE_ACCOUNT': '90002',
}