# accounting/constants.py

ACCOUNT_GROUPS = [
    # === ASSETS ===
    {'code': 'AST001', 'name': 'Current Assets', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'AST002', 'name': 'Sundry Debtors', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST003', 'name': 'Bank Account', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST004', 'name': 'Cash Account', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST005', 'name': 'Prepaid Expenses', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST006', 'name': 'Advance to Employees', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST007', 'name': 'Tax Receivable', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST001'},
    {'code': 'AST008', 'name': 'Non-Current Assets', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'AST009', 'name': 'Land', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST010', 'name': 'Building', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST011', 'name': 'Furniture & Fixtures', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST012', 'name': 'Computer & Equipment', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST013', 'name': 'Vehicles', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST014', 'name': 'Library Books', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST015', 'name': 'Laboratory Equipment', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST016', 'name': 'Sports Equipment', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST017', 'name': 'Security Deposits', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST008'},
    {'code': 'AST002A', 'name': 'Students', 'category': 'Assets', 'main_group': 'balance_sheet', 'parent': 'AST002'},
    # === LIABILITIES ===
    {'code': 'LIA001', 'name': 'Current Liabilities', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'LIA002', 'name': 'Sundry Creditors', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA003', 'name': 'Fee Advance', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA004', 'name': 'Salary Payable', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA005', 'name': 'Tax Payable', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA006', 'name': 'Outstanding Expenses', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA007', 'name': 'Student Deposits', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA001'},
    {'code': 'LIA008', 'name': 'Non-Current Liabilities', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'LIA009', 'name': 'Long-Term Loans', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA008'},
    {'code': 'LIA010', 'name': 'Provisions', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'LIA011', 'name': 'Provision for Gratuity', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA010'},
    {'code': 'LIA012', 'name': 'Provision for Leave Encashment', 'category': 'Liabilities', 'main_group': 'balance_sheet', 'parent': 'LIA010'},
    
    # === EQUITY ===
    {'code': 'EQY001', 'name': 'Capital', 'category': 'Equity', 'main_group': 'balance_sheet', 'parent': None},
    {'code': 'EQY002', 'name': 'Owners Capital', 'category': 'Equity', 'main_group': 'balance_sheet', 'parent': 'EQY001'},
    {'code': 'EQY003', 'name': 'Retained Earnings', 'category': 'Equity', 'main_group': 'balance_sheet', 'parent': 'EQY001'},
    {'code': 'EQY004', 'name': 'Reserves & Surplus', 'category': 'Equity', 'main_group': 'balance_sheet', 'parent': 'EQY001'},
    
    # === INCOME ===
    {'code': 'INC001', 'name': 'Fee Income', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'INC002', 'name': 'Tuition Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC003', 'name': 'Admission Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC004', 'name': 'Examination Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC005', 'name': 'Transport Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC006', 'name': 'Library Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC007', 'name': 'Laboratory Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC008', 'name': 'Sports Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC009', 'name': 'Hostel Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC010', 'name': 'Other Fee', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC001'},
    {'code': 'INC011', 'name': 'Other Income', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'INC012', 'name': 'Donation', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC011'},
    {'code': 'INC013', 'name': 'Grant Income', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC011'},
    {'code': 'INC014', 'name': 'Interest Income', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC011'},
    {'code': 'INC015', 'name': 'Rental Income', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC011'},
    {'code': 'INC016', 'name': 'Late Fee/Fine', 'category': 'Income', 'main_group': 'profit_and_loss', 'parent': 'INC011'},
    
    # === EXPENSES ===
    {'code': 'EXP001', 'name': 'Staff Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP002', 'name': 'Teaching Staff Salary', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP001'},
    {'code': 'EXP003', 'name': 'Non-Teaching Staff Salary', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP001'},
    {'code': 'EXP004', 'name': 'PF Contribution', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP001'},
    {'code': 'EXP005', 'name': 'ESI Contribution', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP001'},
    {'code': 'EXP006', 'name': 'Staff Welfare', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP001'},
    {'code': 'EXP007', 'name': 'Administrative Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP008', 'name': 'Office Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP007'},
    {'code': 'EXP009', 'name': 'Printing & Stationery', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP007'},
    {'code': 'EXP010', 'name': 'Telephone & Internet', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP007'},
    {'code': 'EXP011', 'name': 'Postage & Courier', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP007'},
    {'code': 'EXP012', 'name': 'Professional Fees', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP007'},
    {'code': 'EXP013', 'name': 'Operational Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP014', 'name': 'Rent', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP015', 'name': 'Electricity', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP016', 'name': 'Water Charges', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP017', 'name': 'Repairs & Maintenance', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP018', 'name': 'Housekeeping', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP019', 'name': 'Security Charges', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP013'},
    {'code': 'EXP020', 'name': 'Academic Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP021', 'name': 'Books & Periodicals', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP022', 'name': 'Laboratory Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP023', 'name': 'Examination Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP024', 'name': 'Sports Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP025', 'name': 'Cultural Activities', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP026', 'name': 'Student Activities', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP020'},
    {'code': 'EXP027', 'name': 'Transport Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP028', 'name': 'Vehicle Maintenance', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP027'},
    {'code': 'EXP029', 'name': 'Fuel', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP027'},
    {'code': 'EXP030', 'name': 'Driver Salary', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP027'},
    {'code': 'EXP031', 'name': 'Marketing Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP032', 'name': 'Advertising', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP031'},
    {'code': 'EXP033', 'name': 'Promotional Activities', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP031'},
    {'code': 'EXP034', 'name': 'Financial Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP035', 'name': 'Interest Paid', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP034'},
    {'code': 'EXP036', 'name': 'Bank Charges', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP034'},
    {'code': 'EXP037', 'name': 'Depreciation', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP034'},
    {'code': 'EXP038', 'name': 'Other Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': None},
    {'code': 'EXP039', 'name': 'Insurance', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP038'},
    {'code': 'EXP040', 'name': 'Legal Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP038'},
    {'code': 'EXP041', 'name': 'Audit Fees', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP038'},
    {'code': 'EXP042', 'name': 'Miscellaneous Expenses', 'category': 'Expense', 'main_group': 'profit_and_loss', 'parent': 'EXP038'},
]

# Fixed ACCOUNT_GROUP_CHOICES with proper category mapping for Education ERP
ACCOUNT_GROUP_CHOICES = [
    # 🔵 ASSETS
    # Group: Current Assets
    ('CURRENT_ASSETS', 'Current Assets'),
    ('SUNDRY_DEBTORS', 'Sundry Debtors'),
    ('STUDENTS', 'Students'),
    ('BANK_ACCOUNT', 'Bank Account'),
    ('CASH_ACCOUNT', 'Cash Account'),
    ('PREPAID_EXPENSES', 'Prepaid Expenses'),
    ('ADVANCE_TO_EMPLOYEES', 'Advance to Employees'),
    ('INPUT_TAX_CREDIT', 'Input Tax Credit'),
    ('TDS_RECEIVABLE', 'TDS Receivable'),
    ('FEES_RECEIVABLE', 'Fees Receivable'),
    
    # Group: Non-Current Assets
    ('NON_CURRENT_ASSETS', 'Non-Current Assets'),
    ('LAND', 'Land'),
    ('BUILDING', 'Building'),
    ('FURNITURE_FIXTURES', 'Furniture & Fixtures'),
    ('COMPUTER_EQUIPMENT', 'Computer & Equipment'),
    ('VEHICLES', 'Vehicles'),
    ('LIBRARY_BOOKS', 'Library Books'),
    ('LABORATORY_EQUIPMENT', 'Laboratory Equipment'),
    ('SPORTS_EQUIPMENT', 'Sports Equipment'),
    ('EDUCATIONAL_EQUIPMENT', 'Educational Equipment'),
    
    # Group: Other Non-Current Assets
    ('OTHER_NON_CURRENT_ASSETS', 'Other Non-Current Assets'),
    ('SECURITY_DEPOSITS', 'Security Deposits'),
    ('LONG_TERM_INVESTMENTS', 'Long-Term Investments'),
    ('STAFF_LOANS', 'Staff Loans'),
    
    # 🔴 LIABILITIES
    # Group: Current Liabilities
    ('CURRENT_LIABILITIES', 'Current Liabilities'),
    ('SUNDRY_CREDITORS', 'Sundry Creditors'),
    ('TAXES_PAYABLE', 'Taxes Payable'),
    ('FEE_ADVANCE', 'Fee Advance'),
    ('SALARY_PAYABLE', 'Salary Payable'),
    ('OUTSTANDING_EXPENSES', 'Outstanding Expenses'),
    ('STUDENT_DEPOSITS', 'Student Deposits'),
    ('PF_PAYABLE', 'PF Payable'),
    ('ESI_PAYABLE', 'ESI Payable'),
    ('TDS_PAYABLE', 'TDS Payable'),
    
    # Group: Non-Current Liabilities
    ('NON_CURRENT_LIABILITIES', 'Non-Current Liabilities'),
    ('LONG_TERM_LOANS', 'Long-Term Loans'),
    
    # Group: Provisions
    ('PROVISIONS', 'Provisions'),
    ('PROVISION_FOR_GRATUITY', 'Provision for Gratuity'),
    ('PROVISION_FOR_LEAVE_ENCASHMENT', 'Provision for Leave Encashment'),
    
    # 🔶 CAPITAL/EQUITY
    ('CAPITAL', 'Capital'),
    ('OWNERS_CAPITAL', "Owner's Capital"),
    ('PARTNERS_CAPITAL', "Partner's Capital"),
    ('RETAINED_EARNINGS', 'Retained Earnings'),
    ('RESERVES_SURPLUS', 'Reserves & Surplus'),
    
    # 🟢 INCOME
    # Group: Fee Income
    ('FEE_INCOME', 'Fee Income'),
    ('TUITION_FEE', 'Tuition Fee'),
    ('ADMISSION_FEE', 'Admission Fee'),
    ('EXAMINATION_FEE', 'Examination Fee'),
    ('TRANSPORT_FEE', 'Transport Fee'),
    ('LIBRARY_FEE', 'Library Fee'),
    ('LABORATORY_FEE', 'Laboratory Fee'),
    ('SPORTS_FEE', 'Sports Fee'),
    ('HOSTEL_FEE', 'Hostel Fee'),
    ('DEVELOPMENT_FEE', 'Development Fee'),
    ('ACTIVITY_FEE', 'Activity Fee'),
    ('OTHER_FEE', 'Other Fee'),
    
    # Group: Other Income
    ('OTHER_INCOME', 'Other Income'),
    ('DONATION', 'Donation'),
    ('GRANT_INCOME', 'Grant Income'),
    ('INTEREST_INCOME', 'Interest Income'),
    ('RENTAL_INCOME', 'Rental Income'),
    ('LATE_FEE', 'Late Fee/Fine'),
    ('MISCELLANEOUS_INCOME', 'Miscellaneous Income'),
    
    # 🟠 EXPENSES
    # Group: Staff Expenses
    ('STAFF_EXPENSES', 'Staff Expenses'),
    ('TEACHING_STAFF_SALARY', 'Teaching Staff Salary'),
    ('NON_TEACHING_STAFF_SALARY', 'Non-Teaching Staff Salary'),
    ('PF_CONTRIBUTION', 'PF Contribution'),
    ('ESI_CONTRIBUTION', 'ESI Contribution'),
    ('STAFF_WELFARE', 'Staff Welfare'),
    ('BONUS', 'Bonus'),
    ('GRATUITY', 'Gratuity'),
    
    # Group: Administrative Expenses
    ('ADMINISTRATIVE_EXPENSES', 'Administrative Expenses'),
    ('OFFICE_EXPENSES', 'Office Expenses'),
    ('PRINTING_STATIONERY', 'Printing & Stationery'),
    ('TELEPHONE_INTERNET', 'Telephone & Internet'),
    ('POSTAGE_COURIER', 'Postage & Courier'),
    ('PROFESSIONAL_FEES', 'Professional Fees'),
    
    # Group: Operational Expenses
    ('OPERATIONAL_EXPENSES', 'Operational Expenses'),
    ('RENT', 'Rent'),
    ('ELECTRICITY', 'Electricity'),
    ('WATER_CHARGES', 'Water Charges'),
    ('REPAIRS_MAINTENANCE', 'Repairs & Maintenance'),
    ('HOUSEKEEPING', 'Housekeeping'),
    ('SECURITY_CHARGES', 'Security Charges'),
    
    # Group: Academic Expenses
    ('ACADEMIC_EXPENSES', 'Academic Expenses'),
    ('BOOKS_PERIODICALS', 'Books & Periodicals'),
    ('LABORATORY_EXPENSES', 'Laboratory Expenses'),
    ('EXAMINATION_EXPENSES', 'Examination Expenses'),
    ('SPORTS_EXPENSES', 'Sports Expenses'),
    ('CULTURAL_ACTIVITIES', 'Cultural Activities'),
    ('STUDENT_ACTIVITIES', 'Student Activities'),
    
    # Group: Transport Expenses
    ('TRANSPORT_EXPENSES', 'Transport Expenses'),
    ('VEHICLE_MAINTENANCE', 'Vehicle Maintenance'),
    ('FUEL', 'Fuel'),
    ('DRIVER_SALARY', 'Driver Salary'),
    
    # Group: Marketing Expenses
    ('MARKETING_EXPENSES', 'Marketing Expenses'),
    ('ADVERTISING', 'Advertising'),
    ('PROMOTIONAL_ACTIVITIES', 'Promotional Activities'),
    
    # Group: Financial Expenses
    ('FINANCIAL_EXPENSES', 'Financial Expenses'),
    ('INTEREST_PAID', 'Interest Paid'),
    ('BANK_CHARGES', 'Bank Charges'),
    ('DEPRECIATION', 'Depreciation'),
    
    # Group: Other Expenses
    ('OTHER_EXPENSES', 'Other Expenses'),
    ('INSURANCE', 'Insurance'),
    ('LEGAL_EXPENSES', 'Legal Expenses'),
    ('AUDIT_FEES', 'Audit Fees'),
    ('MISCELLANEOUS_EXPENSES', 'Miscellaneous Expenses'),
    
    # 🔧 SPECIAL/SYSTEM ACCOUNTS
    ('SPECIAL_ACCOUNTS', 'Special Accounts'),
    ('ADJUSTMENT_ACCOUNTS', 'Adjustment Accounts'),
]

# Define parent-child relationships for Education ERP
GROUP_HIERARCHY = {
    # Assets
    'CURRENT_ASSETS': None,
    'SUNDRY_DEBTORS': 'CURRENT_ASSETS',
    'STUDENTS': 'SUNDRY_DEBTORS',
    'BANK_ACCOUNT': 'CURRENT_ASSETS',
    'CASH_ACCOUNT': 'CURRENT_ASSETS',
    'PREPAID_EXPENSES': 'CURRENT_ASSETS',
    'ADVANCE_TO_EMPLOYEES': 'CURRENT_ASSETS',
    'INPUT_TAX_CREDIT': 'CURRENT_ASSETS',
    'TDS_RECEIVABLE': 'CURRENT_ASSETS',
    'FEES_RECEIVABLE': 'CURRENT_ASSETS',
    
    'NON_CURRENT_ASSETS': None,
    'LAND': 'NON_CURRENT_ASSETS',
    'BUILDING': 'NON_CURRENT_ASSETS',
    'FURNITURE_FIXTURES': 'NON_CURRENT_ASSETS',
    'COMPUTER_EQUIPMENT': 'NON_CURRENT_ASSETS',
    'VEHICLES': 'NON_CURRENT_ASSETS',
    'LIBRARY_BOOKS': 'NON_CURRENT_ASSETS',
    'LABORATORY_EQUIPMENT': 'NON_CURRENT_ASSETS',
    'SPORTS_EQUIPMENT': 'NON_CURRENT_ASSETS',
    'EDUCATIONAL_EQUIPMENT': 'NON_CURRENT_ASSETS',
    
    'OTHER_NON_CURRENT_ASSETS': 'NON_CURRENT_ASSETS',
    'SECURITY_DEPOSITS': 'OTHER_NON_CURRENT_ASSETS',
    'LONG_TERM_INVESTMENTS': 'OTHER_NON_CURRENT_ASSETS',
    'STAFF_LOANS': 'OTHER_NON_CURRENT_ASSETS',
    
    # Liabilities
    'CURRENT_LIABILITIES': None,
    'SUNDRY_CREDITORS': 'CURRENT_LIABILITIES',
    'TAXES_PAYABLE': 'CURRENT_LIABILITIES',
    'FEE_ADVANCE': 'CURRENT_LIABILITIES',
    'SALARY_PAYABLE': 'CURRENT_LIABILITIES',
    'OUTSTANDING_EXPENSES': 'CURRENT_LIABILITIES',
    'STUDENT_DEPOSITS': 'CURRENT_LIABILITIES',
    'PF_PAYABLE': 'CURRENT_LIABILITIES',
    'ESI_PAYABLE': 'CURRENT_LIABILITIES',
    'TDS_PAYABLE': 'CURRENT_LIABILITIES',
    
    'NON_CURRENT_LIABILITIES': None,
    'LONG_TERM_LOANS': 'NON_CURRENT_LIABILITIES',
    
    'PROVISIONS': 'NON_CURRENT_LIABILITIES',
    'PROVISION_FOR_GRATUITY': 'PROVISIONS',
    'PROVISION_FOR_LEAVE_ENCASHMENT': 'PROVISIONS',
    
    # Capital
    'CAPITAL': None,
    'OWNERS_CAPITAL': 'CAPITAL',
    'PARTNERS_CAPITAL': 'CAPITAL',
    'RETAINED_EARNINGS': 'CAPITAL',
    'RESERVES_SURPLUS': 'CAPITAL',
    
    # Income
    'FEE_INCOME': None,
    'TUITION_FEE': 'FEE_INCOME',
    'ADMISSION_FEE': 'FEE_INCOME',
    'EXAMINATION_FEE': 'FEE_INCOME',
    'TRANSPORT_FEE': 'FEE_INCOME',
    'LIBRARY_FEE': 'FEE_INCOME',
    'LABORATORY_FEE': 'FEE_INCOME',
    'SPORTS_FEE': 'FEE_INCOME',
    'HOSTEL_FEE': 'FEE_INCOME',
    'DEVELOPMENT_FEE': 'FEE_INCOME',
    'ACTIVITY_FEE': 'FEE_INCOME',
    'OTHER_FEE': 'FEE_INCOME',
    
    'OTHER_INCOME': None,
    'DONATION': 'OTHER_INCOME',
    'GRANT_INCOME': 'OTHER_INCOME',
    'INTEREST_INCOME': 'OTHER_INCOME',
    'RENTAL_INCOME': 'OTHER_INCOME',
    'LATE_FEE': 'OTHER_INCOME',
    'MISCELLANEOUS_INCOME': 'OTHER_INCOME',
    
    # Expenses
    'STAFF_EXPENSES': None,
    'TEACHING_STAFF_SALARY': 'STAFF_EXPENSES',
    'NON_TEACHING_STAFF_SALARY': 'STAFF_EXPENSES',
    'PF_CONTRIBUTION': 'STAFF_EXPENSES',
    'ESI_CONTRIBUTION': 'STAFF_EXPENSES',
    'STAFF_WELFARE': 'STAFF_EXPENSES',
    'BONUS': 'STAFF_EXPENSES',
    'GRATUITY': 'STAFF_EXPENSES',
    
    'ADMINISTRATIVE_EXPENSES': None,
    'OFFICE_EXPENSES': 'ADMINISTRATIVE_EXPENSES',
    'PRINTING_STATIONERY': 'ADMINISTRATIVE_EXPENSES',
    'TELEPHONE_INTERNET': 'ADMINISTRATIVE_EXPENSES',
    'POSTAGE_COURIER': 'ADMINISTRATIVE_EXPENSES',
    'PROFESSIONAL_FEES': 'ADMINISTRATIVE_EXPENSES',
    
    'OPERATIONAL_EXPENSES': None,
    'RENT': 'OPERATIONAL_EXPENSES',
    'ELECTRICITY': 'OPERATIONAL_EXPENSES',
    'WATER_CHARGES': 'OPERATIONAL_EXPENSES',
    'REPAIRS_MAINTENANCE': 'OPERATIONAL_EXPENSES',
    'HOUSEKEEPING': 'OPERATIONAL_EXPENSES',
    'SECURITY_CHARGES': 'OPERATIONAL_EXPENSES',
    
    'ACADEMIC_EXPENSES': None,
    'BOOKS_PERIODICALS': 'ACADEMIC_EXPENSES',
    'LABORATORY_EXPENSES': 'ACADEMIC_EXPENSES',
    'EXAMINATION_EXPENSES': 'ACADEMIC_EXPENSES',
    'SPORTS_EXPENSES': 'ACADEMIC_EXPENSES',
    'CULTURAL_ACTIVITIES': 'ACADEMIC_EXPENSES',
    'STUDENT_ACTIVITIES': 'ACADEMIC_EXPENSES',
    
    'TRANSPORT_EXPENSES': None,
    'VEHICLE_MAINTENANCE': 'TRANSPORT_EXPENSES',
    'FUEL': 'TRANSPORT_EXPENSES',
    'DRIVER_SALARY': 'TRANSPORT_EXPENSES',
    
    'MARKETING_EXPENSES': None,
    'ADVERTISING': 'MARKETING_EXPENSES',
    'PROMOTIONAL_ACTIVITIES': 'MARKETING_EXPENSES',
    
    'FINANCIAL_EXPENSES': None,
    'INTEREST_PAID': 'FINANCIAL_EXPENSES',
    'BANK_CHARGES': 'FINANCIAL_EXPENSES',
    'DEPRECIATION': 'FINANCIAL_EXPENSES',
    
    'OTHER_EXPENSES': None,
    'INSURANCE': 'OTHER_EXPENSES',
    'LEGAL_EXPENSES': 'OTHER_EXPENSES',
    'AUDIT_FEES': 'OTHER_EXPENSES',
    'MISCELLANEOUS_EXPENSES': 'OTHER_EXPENSES',
    
    # Special Accounts
    'SPECIAL_ACCOUNTS': None,
    'ADJUSTMENT_ACCOUNTS': 'SPECIAL_ACCOUNTS',
}

# Map group codes to their category for Education ERP
GROUP_CATEGORIES = {
    # Assets
    'CURRENT_ASSETS': 'Assets',
    'SUNDRY_DEBTORS': 'Assets',
    'STUDENTS': 'Assets',
    'BANK_ACCOUNT': 'Assets',
    'CASH_ACCOUNT': 'Assets',
    'PREPAID_EXPENSES': 'Assets',
    'ADVANCE_TO_EMPLOYEES': 'Assets',
    'INPUT_TAX_CREDIT': 'Assets',
    'TDS_RECEIVABLE': 'Assets',
    'FEES_RECEIVABLE': 'Assets',
    
    'NON_CURRENT_ASSETS': 'Assets',
    'LAND': 'Assets',
    'BUILDING': 'Assets',
    'FURNITURE_FIXTURES': 'Assets',
    'COMPUTER_EQUIPMENT': 'Assets',
    'VEHICLES': 'Assets',
    'LIBRARY_BOOKS': 'Assets',
    'LABORATORY_EQUIPMENT': 'Assets',
    'SPORTS_EQUIPMENT': 'Assets',
    'EDUCATIONAL_EQUIPMENT': 'Assets',
    
    'OTHER_NON_CURRENT_ASSETS': 'Assets',
    'SECURITY_DEPOSITS': 'Assets',
    'LONG_TERM_INVESTMENTS': 'Assets',
    'STAFF_LOANS': 'Assets',
    
    # Liabilities
    'CURRENT_LIABILITIES': 'Liabilities',
    'SUNDRY_CREDITORS': 'Liabilities',
    'TAXES_PAYABLE': 'Liabilities',
    'FEE_ADVANCE': 'Liabilities',
    'SALARY_PAYABLE': 'Liabilities',
    'OUTSTANDING_EXPENSES': 'Liabilities',
    'STUDENT_DEPOSITS': 'Liabilities',
    'PF_PAYABLE': 'Liabilities',
    'ESI_PAYABLE': 'Liabilities',
    'TDS_PAYABLE': 'Liabilities',
    
    'NON_CURRENT_LIABILITIES': 'Liabilities',
    'LONG_TERM_LOANS': 'Liabilities',
    
    'PROVISIONS': 'Liabilities',
    'PROVISION_FOR_GRATUITY': 'Liabilities',
    'PROVISION_FOR_LEAVE_ENCASHMENT': 'Liabilities',
    
    # Capital
    'CAPITAL': 'Equity',
    'OWNERS_CAPITAL': 'Equity',
    'PARTNERS_CAPITAL': 'Equity',
    'RETAINED_EARNINGS': 'Equity',
    'RESERVES_SURPLUS': 'Equity',
    
    # Income
    'FEE_INCOME': 'Income',
    'TUITION_FEE': 'Income',
    'ADMISSION_FEE': 'Income',
    'EXAMINATION_FEE': 'Income',
    'TRANSPORT_FEE': 'Income',
    'LIBRARY_FEE': 'Income',
    'LABORATORY_FEE': 'Income',
    'SPORTS_FEE': 'Income',
    'HOSTEL_FEE': 'Income',
    'DEVELOPMENT_FEE': 'Income',
    'ACTIVITY_FEE': 'Income',
    'OTHER_FEE': 'Income',
    
    'OTHER_INCOME': 'Income',
    'DONATION': 'Income',
    'GRANT_INCOME': 'Income',
    'INTEREST_INCOME': 'Income',
    'RENTAL_INCOME': 'Income',
    'LATE_FEE': 'Income',
    'MISCELLANEOUS_INCOME': 'Income',
    
    # Expenses
    'STAFF_EXPENSES': 'Expense',
    'TEACHING_STAFF_SALARY': 'Expense',
    'NON_TEACHING_STAFF_SALARY': 'Expense',
    'PF_CONTRIBUTION': 'Expense',
    'ESI_CONTRIBUTION': 'Expense',
    'STAFF_WELFARE': 'Expense',
    'BONUS': 'Expense',
    'GRATUITY': 'Expense',
    
    'ADMINISTRATIVE_EXPENSES': 'Expense',
    'OFFICE_EXPENSES': 'Expense',
    'PRINTING_STATIONERY': 'Expense',
    'TELEPHONE_INTERNET': 'Expense',
    'POSTAGE_COURIER': 'Expense',
    'PROFESSIONAL_FEES': 'Expense',
    
    'OPERATIONAL_EXPENSES': 'Expense',
    'RENT': 'Expense',
    'ELECTRICITY': 'Expense',
    'WATER_CHARGES': 'Expense',
    'REPAIRS_MAINTENANCE': 'Expense',
    'HOUSEKEEPING': 'Expense',
    'SECURITY_CHARGES': 'Expense',
    
    'ACADEMIC_EXPENSES': 'Expense',
    'BOOKS_PERIODICALS': 'Expense',
    'LABORATORY_EXPENSES': 'Expense',
    'EXAMINATION_EXPENSES': 'Expense',
    'SPORTS_EXPENSES': 'Expense',
    'CULTURAL_ACTIVITIES': 'Expense',
    'STUDENT_ACTIVITIES': 'Expense',
    
    'TRANSPORT_EXPENSES': 'Expense',
    'VEHICLE_MAINTENANCE': 'Expense',
    'FUEL': 'Expense',
    'DRIVER_SALARY': 'Expense',
    
    'MARKETING_EXPENSES': 'Expense',
    'ADVERTISING': 'Expense',
    'PROMOTIONAL_ACTIVITIES': 'Expense',
    
    'FINANCIAL_EXPENSES': 'Expense',
    'INTEREST_PAID': 'Expense',
    'BANK_CHARGES': 'Expense',
    'DEPRECIATION': 'Expense',
    
    'OTHER_EXPENSES': 'Expense',
    'INSURANCE': 'Expense',
    'LEGAL_EXPENSES': 'Expense',
    'AUDIT_FEES': 'Expense',
    'MISCELLANEOUS_EXPENSES': 'Expense',
    
    # Special Accounts
    'SPECIAL_ACCOUNTS': 'Assets',
    'ADJUSTMENT_ACCOUNTS': 'Assets',
}

# Main group mapping based on category
CATEGORY_TO_MAIN_GROUP = {
    'Assets': 'balance_sheet',
    'Liabilities': 'balance_sheet', 
    'Equity': 'balance_sheet',
    'Income': 'profit_and_loss',
    'Expense': 'profit_and_loss',
}

# Locked Account Choices for Education ERP
LOCKED_ACCOUNT_CHOICES = [
    # 💰 CASH & BANK ACCOUNTS
    ('CASH_ON_HAND', 'Cash on Hand'),
    ('MAIN_BANK_ACCOUNT', 'Main Bank Account'),
    ('FEE_COLLECTION_ACCOUNT', 'Fee Collection Account'),
    
    # 👥 RECEIVABLES
    ('FEES_RECEIVABLE', 'Fees Receivable'),
    ('ADVANCE_TO_EMPLOYEES', 'Advance to Employees'),
    ('ADVANCE_TO_STAFF', 'Advance to Staff'),
    ('TDS_RECEIVABLE', 'TDS Receivable'),
    ('INPUT_GST_CREDIT', 'Input GST Credit'),
    
    # 🏫 FIXED ASSETS
    ('LAND', 'Land'),
    ('BUILDINGS', 'Buildings'),
    ('FURNITURE_FIXTURES', 'Furniture & Fixtures'),
    ('COMPUTERS_EQUIPMENT', 'Computers & Equipment'),
    ('VEHICLES', 'Vehicles'),
    ('LIBRARY_BOOKS', 'Library Books'),
    ('LABORATORY_EQUIPMENT', 'Laboratory Equipment'),
    ('SPORTS_EQUIPMENT', 'Sports Equipment'),
    ('EDUCATIONAL_EQUIPMENT', 'Educational Equipment'),
    
    # 💼 OTHER ASSETS
    ('SECURITY_DEPOSITS', 'Security Deposits'),
    ('LONG_TERM_INVESTMENTS', 'Long-Term Investments'),
    ('STAFF_LOANS', 'Staff Loans'),
    ('PREPAID_INSURANCE', 'Prepaid Insurance'),
    
    # 📊 LIABILITIES
    ('SUNDRY_CREDITORS', 'Sundry Creditors'),
    ('GST_PAYABLE', 'GST Payable'),
    ('TDS_PAYABLE', 'TDS Payable'),
    ('FEE_ADVANCE', 'Fee Advance'),
    ('STUDENT_CAUTION_DEPOSIT', 'Student Caution Deposit'),
    ('SALARY_PAYABLE', 'Salary Payable'),
    ('PF_PAYABLE', 'PF Payable'),
    ('ESI_PAYABLE', 'ESI Payable'),
    ('PROFESSIONAL_TAX_PAYABLE', 'Professional Tax Payable'),
    ('OUTSTANDING_EXPENSES', 'Outstanding Expenses'),
    
    # 🏦 LONG-TERM LIABILITIES
    ('LONG_TERM_LOAN', 'Long-Term Loan'),
    ('PROVISION_FOR_GRATUITY', 'Provision for Gratuity'),
    ('PROVISION_FOR_LEAVE_ENCASHMENT', 'Provision for Leave Encashment'),
    
    # 💎 CAPITAL
    ('OWNERS_CAPITAL', "Owner's Capital"),
    ('PARTNERS_CAPITAL', "Partner's Capital"),
    ('RETAINED_EARNINGS', 'Retained Earnings'),
    ('GENERAL_RESERVE', 'General Reserve'),
    
    # 💵 FEE INCOME
    ('TUITION_FEE', 'Tuition Fee'),
    ('ADMISSION_FEE', 'Admission Fee'),
    ('EXAMINATION_FEE', 'Examination Fee'),
    ('TRANSPORT_FEE', 'Transport Fee'),
    ('LIBRARY_FEE', 'Library Fee'),
    ('LABORATORY_FEE', 'Laboratory Fee'),
    ('SPORTS_FEE', 'Sports Fee'),
    ('HOSTEL_FEE', 'Hostel Fee'),
    ('DEVELOPMENT_FEE', 'Development Fee'),
    ('ACTIVITY_FEE', 'Activity Fee'),
    ('COMPUTER_FEE', 'Computer Fee'),
    ('OTHER_FEE', 'Other Fee'),
    
    # 🎁 OTHER INCOME
    ('DONATION', 'Donation'),
    ('GRANT_INCOME', 'Grant Income'),
    ('INTEREST_INCOME', 'Interest Income'),
    ('RENTAL_INCOME', 'Rental Income'),
    ('LATE_FEE', 'Late Fee/Fine'),
    ('MISCELLANEOUS_INCOME', 'Miscellaneous Income'),
    
    # 👨‍🏫 STAFF EXPENSES
    ('TEACHING_STAFF_SALARY', 'Teaching Staff Salary'),
    ('NON_TEACHING_STAFF_SALARY', 'Non-Teaching Staff Salary'),
    ('ADMINISTRATIVE_STAFF_SALARY', 'Administrative Staff Salary'),
    ('SUPPORT_STAFF_SALARY', 'Support Staff Salary'),
    ('PF_CONTRIBUTION_EMPLOYER', 'PF Contribution (Employer)'),
    ('ESI_CONTRIBUTION_EMPLOYER', 'ESI Contribution (Employer)'),
    ('STAFF_WELFARE', 'Staff Welfare'),
    ('BONUS', 'Bonus'),
    ('GRATUITY', 'Gratuity'),
    ('PROFESSIONAL_TAX', 'Professional Tax'),
    
    # 🏢 ADMINISTRATIVE EXPENSES
    ('OFFICE_EXPENSES', 'Office Expenses'),
    ('PRINTING_STATIONERY', 'Printing & Stationery'),
    ('TELEPHONE_INTERNET', 'Telephone & Internet'),
    ('POSTAGE_COURIER', 'Postage & Courier'),
    ('PROFESSIONAL_FEES', 'Professional Fees'),
    
    # ⚡ OPERATIONAL EXPENSES
    ('RENT', 'Rent'),
    ('ELECTRICITY', 'Electricity'),
    ('WATER_CHARGES', 'Water Charges'),
    ('REPAIRS_MAINTENANCE', 'Repairs & Maintenance'),
    ('HOUSEKEEPING', 'Housekeeping'),
    ('SECURITY_CHARGES', 'Security Charges'),
    
    # 📚 ACADEMIC EXPENSES
    ('BOOKS_PERIODICALS', 'Books & Periodicals'),
    ('LABORATORY_EXPENSES', 'Laboratory Expenses'),
    ('EXAMINATION_EXPENSES', 'Examination Expenses'),
    ('SPORTS_EXPENSES', 'Sports Expenses'),
    ('CULTURAL_ACTIVITIES', 'Cultural Activities'),
    ('STUDENT_ACTIVITIES', 'Student Activities'),
    ('EDUCATIONAL_MATERIALS', 'Educational Materials'),
    
    # 🚌 TRANSPORT EXPENSES
    ('VEHICLE_MAINTENANCE', 'Vehicle Maintenance'),
    ('FUEL', 'Fuel'),
    ('DRIVER_SALARY', 'Driver Salary'),
    ('VEHICLE_INSURANCE', 'Vehicle Insurance'),
    
    # 📣 MARKETING EXPENSES
    ('ADVERTISING', 'Advertising'),
    ('PROMOTIONAL_ACTIVITIES', 'Promotional Activities'),
    ('STUDENT_RECRUITMENT', 'Student Recruitment'),
    
    # 💳 FINANCIAL EXPENSES
    ('INTEREST_PAID', 'Interest Paid'),
    ('BANK_CHARGES', 'Bank Charges'),
    ('DEPRECIATION', 'Depreciation'),
    
    # 📋 OTHER EXPENSES
    ('INSURANCE', 'Insurance'),
    ('LEGAL_EXPENSES', 'Legal Expenses'),
    ('AUDIT_FEES', 'Audit Fees'),
    ('LICENSE_FEES', 'License Fees'),
    ('MISCELLANEOUS_EXPENSES', 'Miscellaneous Expenses'),
    
    # 🔧 SPECIAL ACCOUNTS
    ('ROUNDING_OFF', 'Rounding Off'),
    ('SUSPENSE_ACCOUNT', 'Suspense Account'),
    ('OPENING_BALANCE_ASSET_ADJUSTMENT', 'Opening Balance Asset Adjustment'),
    ('OPENING_BALANCE_LIABILITY_ADJUSTMENT', 'Opening Balance Liability Adjustment'),
    
    # 🧾 TAX ACCOUNTS
    ('IGST_RECEIVABLE', 'IGST Receivable'),
    ('IGST_PAYABLE', 'IGST Payable'),
    ('CGST_RECEIVABLE', 'CGST Receivable'),
    ('CGST_PAYABLE', 'CGST Payable'),
    ('SGST_RECEIVABLE', 'SGST Receivable'),
    ('SGST_PAYABLE', 'SGST Payable'),
]

# Account to Group Mapping for Education ERP
ACCOUNT_TO_GROUP_MAPPING = {
    # Current Assets
    'CASH_ON_HAND': 'CASH_ACCOUNT',
    'MAIN_BANK_ACCOUNT': 'BANK_ACCOUNT',
    'FEE_COLLECTION_ACCOUNT': 'BANK_ACCOUNT',
    'FEES_RECEIVABLE': 'STUDENTS',
    'ADVANCE_TO_EMPLOYEES': 'ADVANCE_TO_EMPLOYEES',
    'ADVANCE_TO_STAFF': 'ADVANCE_TO_EMPLOYEES',
    'PREPAID_INSURANCE': 'PREPAID_EXPENSES',
    'INPUT_GST_CREDIT': 'INPUT_TAX_CREDIT',
    'TDS_RECEIVABLE': 'TDS_RECEIVABLE',
    
    # Fixed Assets
    'LAND': 'LAND',
    'BUILDINGS': 'BUILDING',
    'FURNITURE_FIXTURES': 'FURNITURE_FIXTURES',
    'COMPUTERS_EQUIPMENT': 'COMPUTER_EQUIPMENT',
    'VEHICLES': 'VEHICLES',
    'LIBRARY_BOOKS': 'LIBRARY_BOOKS',
    'LABORATORY_EQUIPMENT': 'LABORATORY_EQUIPMENT',
    'SPORTS_EQUIPMENT': 'SPORTS_EQUIPMENT',
    'EDUCATIONAL_EQUIPMENT': 'EDUCATIONAL_EQUIPMENT',
    
    # Other Assets
    'SECURITY_DEPOSITS': 'SECURITY_DEPOSITS',
    'LONG_TERM_INVESTMENTS': 'LONG_TERM_INVESTMENTS',
    'STAFF_LOANS': 'STAFF_LOANS',
    
    # Current Liabilities
    'SUNDRY_CREDITORS': 'SUNDRY_CREDITORS',
    'GST_PAYABLE': 'TAXES_PAYABLE',
    'TDS_PAYABLE': 'TDS_PAYABLE',
    'FEE_ADVANCE': 'FEE_ADVANCE',
    'STUDENT_CAUTION_DEPOSIT': 'STUDENT_DEPOSITS',
    'SALARY_PAYABLE': 'SALARY_PAYABLE',
    'PF_PAYABLE': 'PF_PAYABLE',
    'ESI_PAYABLE': 'ESI_PAYABLE',
    'PROFESSIONAL_TAX_PAYABLE': 'TAXES_PAYABLE',
    'OUTSTANDING_EXPENSES': 'OUTSTANDING_EXPENSES',
    
    # Non-Current Liabilities
    'LONG_TERM_LOAN': 'LONG_TERM_LOANS',
    'PROVISION_FOR_GRATUITY': 'PROVISION_FOR_GRATUITY',
    'PROVISION_FOR_LEAVE_ENCASHMENT': 'PROVISION_FOR_LEAVE_ENCASHMENT',
    
    # Capital
    'OWNERS_CAPITAL': 'OWNERS_CAPITAL',
    'PARTNERS_CAPITAL': 'PARTNERS_CAPITAL',
    'RETAINED_EARNINGS': 'RETAINED_EARNINGS',
    'GENERAL_RESERVE': 'RESERVES_SURPLUS',
    
    # Fee Income
    'TUITION_FEE': 'TUITION_FEE',
    'ADMISSION_FEE': 'ADMISSION_FEE',
    'EXAMINATION_FEE': 'EXAMINATION_FEE',
    'TRANSPORT_FEE': 'TRANSPORT_FEE',
    'LIBRARY_FEE': 'LIBRARY_FEE',
    'LABORATORY_FEE': 'LABORATORY_FEE',
    'SPORTS_FEE': 'SPORTS_FEE',
    'HOSTEL_FEE': 'HOSTEL_FEE',
    'DEVELOPMENT_FEE': 'DEVELOPMENT_FEE',
    'ACTIVITY_FEE': 'ACTIVITY_FEE',
    'COMPUTER_FEE': 'OTHER_FEE',
    'OTHER_FEE': 'OTHER_FEE',
    
    # Other Income
    'DONATION': 'DONATION',
    'GRANT_INCOME': 'GRANT_INCOME',
    'INTEREST_INCOME': 'INTEREST_INCOME',
    'RENTAL_INCOME': 'RENTAL_INCOME',
    'LATE_FEE': 'LATE_FEE',
    'MISCELLANEOUS_INCOME': 'MISCELLANEOUS_INCOME',
    
    # Staff Expenses
    'TEACHING_STAFF_SALARY': 'TEACHING_STAFF_SALARY',
    'NON_TEACHING_STAFF_SALARY': 'NON_TEACHING_STAFF_SALARY',
    'ADMINISTRATIVE_STAFF_SALARY': 'NON_TEACHING_STAFF_SALARY',
    'SUPPORT_STAFF_SALARY': 'NON_TEACHING_STAFF_SALARY',
    'PF_CONTRIBUTION_EMPLOYER': 'PF_CONTRIBUTION',
    'ESI_CONTRIBUTION_EMPLOYER': 'ESI_CONTRIBUTION',
    'STAFF_WELFARE': 'STAFF_WELFARE',
    'BONUS': 'BONUS',
    'GRATUITY': 'GRATUITY',
    'PROFESSIONAL_TAX': 'STAFF_EXPENSES',
    
    # Administrative Expenses
    'OFFICE_EXPENSES': 'OFFICE_EXPENSES',
    'PRINTING_STATIONERY': 'PRINTING_STATIONERY',
    'TELEPHONE_INTERNET': 'TELEPHONE_INTERNET',
    'POSTAGE_COURIER': 'POSTAGE_COURIER',
    'PROFESSIONAL_FEES': 'PROFESSIONAL_FEES',
    
    # Operational Expenses
    'RENT': 'RENT',
    'ELECTRICITY': 'ELECTRICITY',
    'WATER_CHARGES': 'WATER_CHARGES',
    'REPAIRS_MAINTENANCE': 'REPAIRS_MAINTENANCE',
    'HOUSEKEEPING': 'HOUSEKEEPING',
    'SECURITY_CHARGES': 'SECURITY_CHARGES',
    
    # Academic Expenses
    'BOOKS_PERIODICALS': 'BOOKS_PERIODICALS',
    'LABORATORY_EXPENSES': 'LABORATORY_EXPENSES',
    'EXAMINATION_EXPENSES': 'EXAMINATION_EXPENSES',
    'SPORTS_EXPENSES': 'SPORTS_EXPENSES',
    'CULTURAL_ACTIVITIES': 'CULTURAL_ACTIVITIES',
    'STUDENT_ACTIVITIES': 'STUDENT_ACTIVITIES',
    'EDUCATIONAL_MATERIALS': 'ACADEMIC_EXPENSES',
    
    # Transport Expenses
    'VEHICLE_MAINTENANCE': 'VEHICLE_MAINTENANCE',
    'FUEL': 'FUEL',
    'DRIVER_SALARY': 'DRIVER_SALARY',
    'VEHICLE_INSURANCE': 'TRANSPORT_EXPENSES',
    
    # Marketing Expenses
    'ADVERTISING': 'ADVERTISING',
    'PROMOTIONAL_ACTIVITIES': 'PROMOTIONAL_ACTIVITIES',
    'STUDENT_RECRUITMENT': 'MARKETING_EXPENSES',
    
    # Financial Expenses
    'INTEREST_PAID': 'INTEREST_PAID',
    'BANK_CHARGES': 'BANK_CHARGES',
    'DEPRECIATION': 'DEPRECIATION',
    
    # Other Expenses
    'INSURANCE': 'INSURANCE',
    'LEGAL_EXPENSES': 'LEGAL_EXPENSES',
    'AUDIT_FEES': 'AUDIT_FEES',
    'LICENSE_FEES': 'OTHER_EXPENSES',
    'MISCELLANEOUS_EXPENSES': 'MISCELLANEOUS_EXPENSES',
    
    # Special Accounts
    'ROUNDING_OFF': 'ADJUSTMENT_ACCOUNTS',
    'SUSPENSE_ACCOUNT': 'ADJUSTMENT_ACCOUNTS',
    'OPENING_BALANCE_ASSET_ADJUSTMENT': 'ADJUSTMENT_ACCOUNTS',
    'OPENING_BALANCE_LIABILITY_ADJUSTMENT': 'ADJUSTMENT_ACCOUNTS',
    
    # Tax Accounts
    'IGST_RECEIVABLE': 'INPUT_TAX_CREDIT',
    'IGST_PAYABLE': 'TAXES_PAYABLE',
    'CGST_RECEIVABLE': 'INPUT_TAX_CREDIT',
    'CGST_PAYABLE': 'TAXES_PAYABLE',
    'SGST_RECEIVABLE': 'INPUT_TAX_CREDIT',
    'SGST_PAYABLE': 'TAXES_PAYABLE',
}

# Account Balance Types for Education ERP
ACCOUNT_BALANCE_TYPES = {
    # Assets (Debit balances)
    **{
        k: 'DR'
        for k in [
            'CASH_ON_HAND',
            'MAIN_BANK_ACCOUNT',
            'FEE_COLLECTION_ACCOUNT',
            'FEES_RECEIVABLE',
            'ADVANCE_TO_EMPLOYEES',
            'ADVANCE_TO_STAFF',
            'PREPAID_INSURANCE',
            'INPUT_GST_CREDIT',
            'TDS_RECEIVABLE',
            'LAND',
            'BUILDINGS',
            'FURNITURE_FIXTURES',
            'COMPUTERS_EQUIPMENT',
            'VEHICLES',
            'LIBRARY_BOOKS',
            'LABORATORY_EQUIPMENT',
            'SPORTS_EQUIPMENT',
            'EDUCATIONAL_EQUIPMENT',
            'SECURITY_DEPOSITS',
            'LONG_TERM_INVESTMENTS',
            'STAFF_LOANS',
            'IGST_RECEIVABLE',
            'CGST_RECEIVABLE',
            'SGST_RECEIVABLE',
        ]
    },
    # Liabilities (Credit balances)
    **{
        k: 'CR'
        for k in [
            'SUNDRY_CREDITORS',
            'GST_PAYABLE',
            'TDS_PAYABLE',
            'FEE_ADVANCE',
            'STUDENT_CAUTION_DEPOSIT',
            'SALARY_PAYABLE',
            'PF_PAYABLE',
            'ESI_PAYABLE',
            'PROFESSIONAL_TAX_PAYABLE',
            'OUTSTANDING_EXPENSES',
            'LONG_TERM_LOAN',
            'PROVISION_FOR_GRATUITY',
            'PROVISION_FOR_LEAVE_ENCASHMENT',
            'IGST_PAYABLE',
            'CGST_PAYABLE',
            'SGST_PAYABLE',
        ]
    },
    # Capital (Credit balances)
    **{k: 'CR' for k in ['OWNERS_CAPITAL', 'PARTNERS_CAPITAL', 'RETAINED_EARNINGS', 'GENERAL_RESERVE']},
    
    # Income (Credit balances)
    **{
        k: 'CR'
        for k in [
            'TUITION_FEE',
            'ADMISSION_FEE',
            'EXAMINATION_FEE',
            'TRANSPORT_FEE',
            'LIBRARY_FEE',
            'LABORATORY_FEE',
            'SPORTS_FEE',
            'HOSTEL_FEE',
            'DEVELOPMENT_FEE',
            'ACTIVITY_FEE',
            'COMPUTER_FEE',
            'OTHER_FEE',
            'DONATION',
            'GRANT_INCOME',
            'INTEREST_INCOME',
            'RENTAL_INCOME',
            'LATE_FEE',
            'MISCELLANEOUS_INCOME',
        ]
    },
    
    # Expenses (Debit balances)
    **{
        k: 'DR'
        for k in [
            'TEACHING_STAFF_SALARY',
            'NON_TEACHING_STAFF_SALARY',
            'ADMINISTRATIVE_STAFF_SALARY',
            'SUPPORT_STAFF_SALARY',
            'PF_CONTRIBUTION_EMPLOYER',
            'ESI_CONTRIBUTION_EMPLOYER',
            'STAFF_WELFARE',
            'BONUS',
            'GRATUITY',
            'PROFESSIONAL_TAX',
            'OFFICE_EXPENSES',
            'PRINTING_STATIONERY',
            'TELEPHONE_INTERNET',
            'POSTAGE_COURIER',
            'PROFESSIONAL_FEES',
            'RENT',
            'ELECTRICITY',
            'WATER_CHARGES',
            'REPAIRS_MAINTENANCE',
            'HOUSEKEEPING',
            'SECURITY_CHARGES',
            'BOOKS_PERIODICALS',
            'LABORATORY_EXPENSES',
            'EXAMINATION_EXPENSES',
            'SPORTS_EXPENSES',
            'CULTURAL_ACTIVITIES',
            'STUDENT_ACTIVITIES',
            'EDUCATIONAL_MATERIALS',
            'VEHICLE_MAINTENANCE',
            'FUEL',
            'DRIVER_SALARY',
            'VEHICLE_INSURANCE',
            'ADVERTISING',
            'PROMOTIONAL_ACTIVITIES',
            'STUDENT_RECRUITMENT',
            'INTEREST_PAID',
            'BANK_CHARGES',
            'DEPRECIATION',
            'INSURANCE',
            'LEGAL_EXPENSES',
            'AUDIT_FEES',
            'LICENSE_FEES',
            'MISCELLANEOUS_EXPENSES',
            'ROUNDING_OFF',
            'SUSPENSE_ACCOUNT',
        ]
    },
    
    # Special Account Balance Types
    'OPENING_BALANCE_ASSET_ADJUSTMENT': 'CR',
    'OPENING_BALANCE_LIABILITY_ADJUSTMENT': 'DR',
}

# Account Code Prefixes for Education ERP
ACCOUNT_CODE_PREFIXES = {
    # Asset Accounts
    'CASH': '100',
    'BANK': '110',
    'RECEIVABLE': '120',
    'PREPAID': '140',
    'FIXED_ASSET': '150',
    'OTHER_ASSET': '190',
    
    # Liability Accounts
    'PAYABLE': '200',
    'TAX': '210',
    'FEE_ADVANCE': '220',
    'STUDENT_DEPOSIT': '230',
    'LOAN': '240',
    'PROVISION': '250',
    'OTHER_LIABILITY': '290',
    
    # Capital Accounts
    'CAPITAL': '300',
    'RETAINED': '310',
    'RESERVE': '320',
    
    # Fee Income Accounts
    'FEE': '400',
    'OTHER_INCOME': '490',
    
    # Staff Expense Accounts
    'SALARY': '500',
    'STAFF_COST': '510',
    
    # Administrative Expense Accounts
    'ADMIN': '520',
    
    # Operational Expense Accounts
    'OPERATIONAL': '530',
    
    # Academic Expense Accounts
    'ACADEMIC': '540',
    
    # Transport Expense Accounts
    'TRANSPORT': '550',
    
    # Marketing Expense Accounts
    'MARKETING': '560',
    
    # Financial Expense Accounts
    'FINANCIAL': '570',
    
    # Other Expense Accounts
    'OTHER_EXPENSE': '590',
    
    # Special Accounts
    'SUSPENSE': '900',
    'ADJUSTMENT': '910',
}

# Account Code Mapping for Education ERP
ACCOUNT_CODE_MAPPING = {
    # Asset Accounts
    'CASH_ON_HAND': '10001',
    'MAIN_BANK_ACCOUNT': '11001',
    'FEE_COLLECTION_ACCOUNT': '11002',
    'FEES_RECEIVABLE': '12001',
    'ADVANCE_TO_EMPLOYEES': '12002',
    'ADVANCE_TO_STAFF': '12003',
    'PREPAID_INSURANCE': '14001',
    'INPUT_GST_CREDIT': '14002',
    'TDS_RECEIVABLE': '19001',
    
    # Fixed Assets
    'LAND': '15001',
    'BUILDINGS': '15002',
    'FURNITURE_FIXTURES': '15003',
    'COMPUTERS_EQUIPMENT': '15004',
    'VEHICLES': '15005',
    'LIBRARY_BOOKS': '15006',
    'LABORATORY_EQUIPMENT': '15007',
    'SPORTS_EQUIPMENT': '15008',
    'EDUCATIONAL_EQUIPMENT': '15009',
    
    # Other Assets
    'SECURITY_DEPOSITS': '19002',
    'LONG_TERM_INVESTMENTS': '19003',
    'STAFF_LOANS': '19004',
    
    # Liability Accounts
    'SUNDRY_CREDITORS': '20001',
    'GST_PAYABLE': '21001',
    'TDS_PAYABLE': '21002',
    'FEE_ADVANCE': '22001',
    'STUDENT_CAUTION_DEPOSIT': '23001',
    'SALARY_PAYABLE': '20002',
    'PF_PAYABLE': '21003',
    'ESI_PAYABLE': '21004',
    'PROFESSIONAL_TAX_PAYABLE': '21005',
    'OUTSTANDING_EXPENSES': '20003',
    'LONG_TERM_LOAN': '24001',
    'PROVISION_FOR_GRATUITY': '25001',
    'PROVISION_FOR_LEAVE_ENCASHMENT': '25002',
    
    # Capital Accounts
    'OWNERS_CAPITAL': '30001',
    'PARTNERS_CAPITAL': '30002',
    'RETAINED_EARNINGS': '31001',
    'GENERAL_RESERVE': '32001',
    
    # Fee Income Accounts
    'TUITION_FEE': '40001',
    'ADMISSION_FEE': '40002',
    'EXAMINATION_FEE': '40003',
    'TRANSPORT_FEE': '40004',
    'LIBRARY_FEE': '40005',
    'LABORATORY_FEE': '40006',
    'SPORTS_FEE': '40007',
    'HOSTEL_FEE': '40008',
    'DEVELOPMENT_FEE': '40009',
    'ACTIVITY_FEE': '40010',
    'COMPUTER_FEE': '40011',
    'OTHER_FEE': '40099',
    
    # Other Income
    'DONATION': '49001',
    'GRANT_INCOME': '49002',
    'INTEREST_INCOME': '49003',
    'RENTAL_INCOME': '49004',
    'LATE_FEE': '49005',
    'MISCELLANEOUS_INCOME': '49099',
    
    # Staff Expenses
    'TEACHING_STAFF_SALARY': '50001',
    'NON_TEACHING_STAFF_SALARY': '50002',
    'ADMINISTRATIVE_STAFF_SALARY': '50003',
    'SUPPORT_STAFF_SALARY': '50004',
    'PF_CONTRIBUTION_EMPLOYER': '51001',
    'ESI_CONTRIBUTION_EMPLOYER': '51002',
    'STAFF_WELFARE': '51003',
    'BONUS': '51004',
    'GRATUITY': '51005',
    'PROFESSIONAL_TAX': '51006',
    
    # Administrative Expenses
    'OFFICE_EXPENSES': '52001',
    'PRINTING_STATIONERY': '52002',
    'TELEPHONE_INTERNET': '52003',
    'POSTAGE_COURIER': '52004',
    'PROFESSIONAL_FEES': '52005',
    
    # Operational Expenses
    'RENT': '53001',
    'ELECTRICITY': '53002',
    'WATER_CHARGES': '53003',
    'REPAIRS_MAINTENANCE': '53004',
    'HOUSEKEEPING': '53005',
    'SECURITY_CHARGES': '53006',
    
    # Academic Expenses
    'BOOKS_PERIODICALS': '54001',
    'LABORATORY_EXPENSES': '54002',
    'EXAMINATION_EXPENSES': '54003',
    'SPORTS_EXPENSES': '54004',
    'CULTURAL_ACTIVITIES': '54005',
    'STUDENT_ACTIVITIES': '54006',
    'EDUCATIONAL_MATERIALS': '54007',
    
    # Transport Expenses
    'VEHICLE_MAINTENANCE': '55001',
    'FUEL': '55002',
    'DRIVER_SALARY': '55003',
    'VEHICLE_INSURANCE': '55004',
    
    # Marketing Expenses
    'ADVERTISING': '56001',
    'PROMOTIONAL_ACTIVITIES': '56002',
    'STUDENT_RECRUITMENT': '56003',
    
    # Financial Expenses
    'INTEREST_PAID': '57001',
    'BANK_CHARGES': '57002',
    'DEPRECIATION': '57003',
    
    # Other Expenses
    'INSURANCE': '59001',
    'LEGAL_EXPENSES': '59002',
    'AUDIT_FEES': '59003',
    'LICENSE_FEES': '59004',
    'MISCELLANEOUS_EXPENSES': '59099',
    
    # Special Accounts
    'ROUNDING_OFF': '90001',
    'SUSPENSE_ACCOUNT': '90002',
    'OPENING_BALANCE_ASSET_ADJUSTMENT': '91001',
    'OPENING_BALANCE_LIABILITY_ADJUSTMENT': '91002',
    
    # Tax Accounts
    'IGST_RECEIVABLE': '14003',
    'IGST_PAYABLE': '21006',
    'CGST_RECEIVABLE': '14004',
    'CGST_PAYABLE': '21007',
    'SGST_RECEIVABLE': '14005',
    'SGST_PAYABLE': '21008',
}