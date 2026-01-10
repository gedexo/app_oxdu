import calendar
import datetime
current_year = datetime.datetime.now().year

BOOL_CHOICES = ((True, "Yes"), (False, "No"))

CHOICES = (("true", "Yes"), ("false", "No"))

COLLECTION_MODE_CHOICES = (("CASH", "Cash"), ("CHEQUE", "Cheque"), ("BANK_TRANSFER", "Bank Transfer"), ("OTHERS", "Others"))

ATTENDANCE_LOCATION_CHOICES = (("HOME", "HOME"), ("OFFICE", "OFFICE"))

CONTACT_TYPE_CHOICES = (("PHONE", "PHONE"), ("WHATSAPP", "WHATSAPP"), ("EMAIL", "EMAIL"), ("SMS", "SMS"))

EXPERIENCE_CHOICES = (("EXPERIENCED", "Experienced"), ("FRESHER", "Fresher"))

EMPLOYMENT_TYPE_CHOICES = (("PERMANENT", "Permanent"), ("PROBATION", "Probation"), ("CONTRACT", "Contract"), ("TEMPORARY", "Temporary"), ("COMMISSION", "Commission"))

EDUCATION_TYPE_CHOICES = (("PROFESSIONAL", "Professional"), ("VOCATIONAL", "Vocational"), ("OTHERS", "Others"))
    
GENDER_CHOICES = (("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other"))

GST_CHOICES = (("unregistered", "Unregistered/Consumer"), ("regular", "Registered - Regular"), ("composite", "Registered -Composite"))

JOB_TYPE_CHOICES = (("Contructual", "Contructual"), ("Permanent", "Permanent"), ("Probation", "Probation"))

ORIGIN_CHOICES = (("UAE", "UAE"), ("Qatar", "Qatar"), ("Oman", "Oman"), ("Kuwait", "Kuwait"), ("KSA", "KSA"), ("EXPAT", "EXPAT"), ("Bahrain", "Bahrain"))

PAYMODE_CHOICES = (("CASH", "Cash on Hand"), ("BANK", "Bank Account"), ("WPS", "WPS - Wages Protection System"))

PRIORITY_CHOICES = (("Urgent", "Urgent"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low"))

READINESS_CHOICES = (("3", "Within 3 Months"), ("5", "with 1 year"), ("6", "Within 6 Months"), ("12", "Within 12 Months"))

RELATION_CHOICES = (("Child", "Child"), ("Father", "Father"), ("Husbend", "Husbend"), ("Mother", "Mother"), ("Spouse", "Spouse"), ("Wife", "Wife"))

REQUEST_STATUS_CHOICES = (("AWAITING", "Awaiting"), ("ACCEPTED", "Accepted"), ("rejected", "Rejected"), ("COMPLETED", "Completed"))

RETIRE_TYPE_CHOICES = (("None", "None"), ("NOR", "Normal"), ("REG", "Resignation"), ("TER", "Termination"), ("VRS", "VRS"))

# RATING_CHOICES = ((1, "One"), (2, "Two"), (3, "Three"), (4, "Four"), (5, "Five"))

STATUS_CHOICES = (("on_hold", "On hold"), ("rejected", "Rejected"), ("approved", "Approved"))

SALUTATION_CHOICES = (("Dr.", "Dr."), ("Miss", "Miss"), ("Mr", "Mr"), ("Mrs", "Mrs"), ("Prof.", "Prof."))

TAX_CHOICES = ((0, "0 %"), (5, "5 %"), (10, "10 %"), (12, "12 %"), (15, "15 %"), (18, "18 %"), (20, "20 %"))

YEAR_CHOICES = [(str(y), str(y)) for y in range(datetime.date.today().year + 1, 1949, -1)]

MONTH_CHOICES = [(str(i), calendar.month_name[i]) for i in range(1, 13)]

MONTH_LIST_CHOICES = [
    (f"{year}-{month:02d}", f"{calendar.month_name[month]} {year}")
    for year in range(current_year, current_year - 6, -1)
    for month in range(12, 0, -1)
]

TAG_CHOICES = (("primary", "Blue"), ("secondary", "Orange"), ("success", "Green"), ("warning", "Yellow"), ("danger", "Red"))

MEAL_TYPE_CHOICES = (("break_fast", "Break Fast"), ("lunch", "Lunch"), ("dinner", "Dinner"), ("other", "Other"))

ANNUAL_CTC_CHOICES = (
    ("LT_2LPA", "< 2 LPA"),
    ("2LPA_3LPA", "2-3 LPA"),
    ("3LPA_5LPA", "3-5 LPA"),
    ("5LPA_7LPA", "5-7 LPA"),
    ("7LPA_10LPA", "7-10 LPA"),
    ("10LPA_15LPA", "10-15 LPA"),
    ("15LPA_20LPA", "15-20 LPA"),
    ("GT_20LPA", ">20+ LPA"),
)
APPLICATION_STATUS_CHOICES = (("APPLIED", "APPLIED"), ("REVIEWED", "REVIEWED"), ("INTERVIEWED", "INTERVIEWED"), ("ACCEPTED", "ACCEPTED"), ("rejected", "rejected"))
APPLICATION_SOURCE_CHOICES = (
    ("EMAIL", "Email"),
    ("WEBSITE", "Website"),
    ("LINKEDIN", "LinkedIn"),
    ("INDEED", "Indeed"),
    ("GLASSDOOR", "Glassdoor"),
    ("JOB_APP", "Other Job Applications"),
)
BLOOD_CHOICES = (
    ("a-positive", "A +Ve"),
    ("b-positive", "B +Ve"),
    ("ab-positive", "AB +Ve"),
    ("o-positive", "O +Ve"),
    ("a-negative", "A -Ve"),
    ("b-negative", "B -Ve"),
    ("ab-negative", "AB -Ve"),
    ("o-negative", "O -Ve"),
)

COLOR_PALETTE = [
    ("#FF5733", "#FF5733"),
    ("#FFBD33", "#FFBD33"),
    ("#DBFF33", "#DBFF33"),
    ("#75FF33", "#75FF33"),
    ("#33FF57", "#33FF57"),
    ("#33FFBD", "#33FFBD"),
    ("#FF58DE", "#FF58DE"),
    ("#7C80FF", "#7C80FF"),
]
DURATION_CHOICES = (
    ("None", "None"),
    ("0-1 Years", "0-1 Years"),
    ("1-2 Years", "1-2 Years"),
    ("2-3 Years", "2-3 Years"),
    ("3-4 Years", "3-4 Years"),
    ("4-5 Years", "4-5 Years"),
    ("5+ Years", "5+ Years"),
)
ENQUIRY_STATUS_TYPE_CHOICES = (("OPEN", "OPEN"), ("CLOSED", "CLOSED"), ("REJECTED_BY_COMPANY", "REJECTED_BY_COMPANY"), ("REJECTED_BY_CLIENT", "rejected_BY_CLIENT"))

ENQUIRY_STATUS = (
    ('new_enquiry', 'New Enquiry'),
    ('no_response', 'No Response'),
    ('follow_up', 'Follow Up'),
    ('demo', 'Ready for Demo'),
    ('interested', 'Interested'),
    ('interested_next_batch', 'Interested in Next Batch'),
    ('admitted', 'Admitted'),
    ('rejected', 'Rejected'),
)

ENQUIRY_TYPE_CHOICES = (
    ('public_lead', 'Public Lead'),
    ('meta_lead', 'Meta Lead'),
    ('campaign_lead', 'Campaign Lead'),
    ('event_lead', 'Event Lead'),
    ('referral_lead', 'Referral Lead'),
)

MARITAL_CHOICES = (("SINGLE", "Single"), ("MARRIED", "Married"), ("IN_A_RELATIONSHIP", "In a Relationship"), ("DIVORCED", "Divorced"), ("WIDOWED", "Widowed"), ("OTHER", "Other"))
NOTICE_PERIOD_CHOICES = (
    ("0", "0"),
    ("1-15", "15 days or less"),
    ("15-30", "15-30 days"),
    ("31-45", "31-45 days"),
    ("46-60", "46-60 days"),
    ("61-90", "61-90 days"),
    ("90+", "More than 90 days"),
)
PROJECT_STATUS_CHOICES = (
    ("ON_SCHEDULE", "On Schedule"),
    ("JUST_STARTED", "Just Started"),
    ("ONGOING", "Ongoing"),
    ("DELAYED", "Delayed"),
    ("W4C", "W4C Approval"),
    ("COMPLETED", "Completed"),
)
PROJECT_PRIORITY_CHOICES = (
    ("URGENT_AND_IMPORTANT", "Urgent and Important"),
    ("NOT_URGENT_AND_IMPORTANT", "Not Urgent and Important"),
    ("URGENT_AND_NOT_IMPORTANT", "Urgent and Not Important"),
    ("NOT_URGENT_AND_NOT_IMPORTANT", "Not Urgent and Not Important"),
)
RESIDENCE_CHOICES = (
    ("SELF_OWNED", "Self Owned"),
    ("FAMILY_OWNED", "Family Owned"),
    ("SELF_RENTED", "Self Rented"),
    ("FAMILY_RENTED", "Family Rented"),
    ("COMPANY_RENTED", "Company Rented"),
    ("COMPANY_OWNED", "Company Owned"),
    ("SHARED", "Shared"),
    ("OTHER", "Other"),
)


EMPLOYEE_STATUS_CHOICES = (("Appointed", "Appointed"), ("Resigned", "Resigned"), ("Terminated", "Terminated"))

PAYMENT_METHOD_CHOICES = [('cash', 'Cash'), ('bank', 'Bank Transfer'), ('Razorpay', 'Razorpay'),]

USERTYPE_CHOICES = (('admin_staff', 'Admin Staff'), ('branch_staff', 'Branch Staff'), ('teacher', 'Teacher'), ('mentor', 'Mentor'), ('sales_head', 'Sales Head'), ('tele_caller', 'Tele Caller'), ('student', 'Student'), ('ceo', 'CEO'), ('cfo', 'CFO'), ('coo', 'COO'), ('hr', 'HR'), ('cmo', "CMO"), ('partner', 'Partner'),)

USERTYPE_FLOW_CHOICES = (('mentor', 'Mentor'), ('sales_head', 'Sales Head'), ('ceo', 'CEO'), ('cfo', 'CFO'), ('coo', 'COO'), ('hr', 'HR'), ('cmo', "CMO"), ('branch_staff', 'Branch Staff'),)

ACCOUNTING_MASTER_CHOICES = (("Assets", "Assets"), ("Liabilities", "Liabilities"), ("Equity", "Equity"), ("Income", "Income"), ("Expense", "Expense"))



LOCKED_ACCOUNT_CHOICES = [
    ('CASH_ON_HAND', 'Cash on Hand'),
    ('MAIN_BANK_ACCOUNT', 'Main Bank Account'),
    ('ACCOUNTS_RECEIVABLE', 'Accounts Receivable'),
    ('ADVANCE_TO_SUPPLIERS', 'Advance to Suppliers'),
    ('PREPAID_INSURANCE', 'Prepaid Insurance'),
    ('INPUT_GST_CREDIT', 'Input GST Credit'),
    ('SHORT_TERM_INVESTMENTS', 'Short-Term Investments'),
    
    # 📦 INVENTORY/STOCK ACCOUNTS
    ('INVENTORY_ASSET', 'Inventory Asset'),
    ('INVENTORY_RAW_MATERIALS', 'Raw Materials'),
    ('INVENTORY_WORK_IN_PROGRESS', 'Work in Progress'),
    ('INVENTORY_FINISHED_GOODS', 'Finished Goods'),
    ('INVENTORY_TRADING_GOODS', 'Trading Goods'),
    ('INVENTORY_CONSUMABLES', 'Consumables & Supplies'),
    ('INVENTORY_PACKAGING_MATERIALS', 'Packaging Materials'),
    ('INVENTORY_SPARE_PARTS', 'Spare Parts'),
    ('INVENTORY_OBSOLETE_STOCK', 'Obsolete Stock'),
    ('STOCK_IN_TRANSIT', 'Stock in Transit'),
    ('GOODS_ON_CONSIGNMENT', 'Goods on Consignment'),
    
    ('LAND', 'Land'),
    ('BUILDINGS', 'Buildings'),
    ('FURNITURE_FIXTURES', 'Furniture & Fixtures'),
    ('COMPUTERS_EQUIPMENT', 'Computers & Equipment'),
    ('VEHICLES', 'Vehicles'),
    ('PLANT_MACHINERY', 'Plant & Machinery'),
    ('SOFTWARE_LICENSES', 'Software Licenses'),
    ('PATENTS', 'Patents'),
    ('COPYRIGHTS', 'Copyrights'),
    ('TRADEMARKS', 'Trademarks'),
    ('SECURITY_DEPOSITS', 'Security Deposits'),
    ('LONG_TERM_INVESTMENTS', 'Long-Term Investments'),
    ('STAFF_LOANS', 'Staff Loans'),
    ('ACCRUED_INTEREST_INCOME', 'Accrued Interest Income'),
    ('ACCOUNTS_PAYABLE', 'Accounts Payable'),
    ('BILLS_PAYABLE', 'Bills Payable'),
    ('GST_PAYABLE', 'GST Payable'),
    ('ADVANCE_FROM_CUSTOMERS', 'Advance from Customers'),
    ('ACCRUED_SALARIES', 'Accrued Salaries'),
    ('OUTSTANDING_EXPENSES', 'Outstanding Expenses'),
    ('LONG_TERM_LOAN', 'Long-Term Loan'),
    ('DEBENTURES_PAYABLE', 'Debentures Payable'),
    ('LEASE_OBLIGATIONS', 'Lease Obligations'),
    ('PROVISION_FOR_TAX', 'Provision for Tax'),
    ('PROVISION_FOR_GRATUITY', 'Provision for Gratuity'),
    ('PROVISION_FOR_BONUS', 'Provision for Bonus'),
    ('OWNERS_CAPITAL', "Owner's Capital"),
    ('PARTNERS_CAPITAL', "Partner's Capital"),
    ('SHARE_CAPITAL', 'Share Capital'),
    ('RETAINED_EARNINGS', 'Retained Earnings'),
    ('GENERAL_RESERVE', 'General Reserve'),
    ('SALES_REVENUE', 'Sales Revenue'),
    ('SERVICE_REVENUE', 'Service Revenue'),
    ('INTEREST_INCOME', 'Interest Income'),
    ('RENT_INCOME', 'Rent Income'),
    ('COMMISSION_RECEIVED', 'Commission Received'),
    ('ASSET_SALE_PROFIT', 'Profit on Sale of Assets'),
    ('MISCELLANEOUS_INCOME', 'Miscellaneous Income'),
    ('PURCHASES', 'Purchases'),
    ('FREIGHT_INWARD', 'Freight Inward'),
    ('DIRECT_WAGES', 'Wages (Direct Labor)'),
    ('POWER_AND_FUEL', 'Power & Fuel'),
    
    # 💰 COST OF GOODS SOLD (COGS) ACCOUNTS
    ('COST_OF_GOODS_SOLD', 'Cost of Goods Sold'),
    ('OPENING_STOCK', 'Opening Stock'),
    ('CLOSING_STOCK', 'Closing Stock'),
    ('COST_OF_RAW_MATERIALS', 'Cost of Raw Materials'),
    ('COST_OF_MATERIALS_CONSUMED', 'Cost of Materials Consumed'),
    ('DIRECT_LABOR_COST', 'Direct Labor Cost'),
    ('MANUFACTURING_OVERHEAD', 'Manufacturing Overhead'),
    ('FACTORY_OVERHEAD', 'Factory Overhead'),
    ('PRODUCTION_OVERHEAD', 'Production Overhead'),
    ('COST_OF_PRODUCTION', 'Cost of Production'),
    ('COST_OF_SALES', 'Cost of Sales'),
    ('CARRIAGE_INWARD', 'Carriage Inward'),
    ('IMPORT_DUTIES', 'Import Duties'),
    ('CUSTOMS_DUTY', 'Customs Duty'),
    ('OCTROI', 'Octroi'),
    ('STOCK_ADJUSTMENT', 'Stock Adjustment'),
    ('STOCK_SHORTAGE', 'Stock Shortage'),
    ('STOCK_SURPLUS', 'Stock Surplus'),
    ('WASTAGE_SCRAP', 'Wastage & Scrap'),
    ('QUALITY_CONTROL_COST', 'Quality Control Cost'),
    
    ('SALARIES', 'Salaries'),
    ('RENT_EXPENSE', 'Rent'),
    ('TELEPHONE_INTERNET', 'Telephone / Internet'),
    ('OFFICE_EXPENSES', 'Office Expenses'),
    ('MARKETING_ADVERTISING', 'Marketing & Advertising'),
    ('REPAIRS_MAINTENANCE', 'Repairs & Maintenance'),
    ('DEPRECIATION', 'Depreciation'),
    ('INTEREST_PAID', 'Interest Paid'),
    ('BANK_CHARGES', 'Bank Charges'),
    ('ROUNDING_OFF', 'Rounding Off'),
    ('SUSPENSE_ACCOUNT', 'Suspense Account'),
    ('OPENING_BALANCE_ASSET_ADJUSTMENT', 'Opening Balance Asset Adjustment'),
    ('OPENING_BALANCE_LIABILITY_ADJUSTMENT', 'Opening Balance Liability Adjustment'),
    ('DEFAULT_GST_RECEIVABLE', 'Default GST Receivable'),
    ('DEFAULT_GST_PAYABLE', 'Default GST Payable'),
    ('IGST_RECEIVABLE', 'IGST Receivable'),
    ('IGST_PAYABLE', 'IGST Payable'),
    ('CGST_RECEIVABLE', 'CGST Receivable'),
    ('CGST_PAYABLE', 'CGST Payable'),
    ('SGST_RECEIVABLE', 'SGST Receivable'),
    ('SGST_PAYABLE', 'SGST Payable'),
    ('CESS_RECEIVABLE', 'CESS Receivable'),
    ('CESS_PAYABLE', 'CESS Payable'),
    ('TDS_RECEIVABLE', 'TDS Receivable'),
    ('TDS_PAYABLE', 'TDS Payable'),
    ('PAYROLL_CONTROL_ACCOUNT', 'Payroll Control Account'),
    ('SALES_ACCOUNT', 'Sales Account'),
    ('PURCHASE_ACCOUNT', 'Purchase Account'),
    ('SALES_RETURN_ACCOUNT', 'Sales Return Account'),
    ('PURCHASE_RETURN_ACCOUNT', 'Purchase Return Account'),
    ('TCS_RECEIVABLE', 'TCS Receivable (Purchase)'),
    ('SALES_DISCOUNT', 'Sales Discount'),
    ('PURCHASE_DISCOUNT', 'Purchase Discount'),
    ('CASH_DISCOUNT_RECEIVED', 'Cash Discount Received'),
    ('CASH_DISCOUNT_ALLOWED', 'Cash Discount Allowed'),
]

MAIN_GROUP_CHOICES = (('balance_sheet', 'Balance Sheet'), ('profit_and_loss', 'Profit & Loss'), ('cash_flow', 'Cash Flow Statement'), ('others', 'Others'))
OPENING_BALANCE_TYPE_CHOICES = (('Dr', 'Dr'), ('Cr', 'Cr'))

INVOICE_TYPE_CHOICES = [
    ('sale_invoice', 'Sale'),
    ('van_sale_invoice', 'Van Sale'),
    ('purhase_invoice', 'Purchase'),
    ('course_fee', 'Course Fee'),
]

NATURE_OF_SUPPLY_CHOICES = (
    ('service_tax', 'Service Tax'),
    ('b2b_igst', 'B2B IGST'),
    ('b2b_igst_sgst', 'B2b IGST+CGST'),
    ('b2c_igst', 'B2c IGST'),
    ('b2c_cgst_sgst', 'B2c CGST+SGST'),
    ('b2b_import', 'B2B Import'),
    ('b2c_import', 'B2C Import'),
    ('b2b_export', 'B2B Export'),
)

TAX_APPLICABLE_CHOICES = (
    ('basic', 'Tax On Basic'),
    ('tax', 'Tax'),
    ('shipping', 'Shipping Charge'),
    ('pakaging', 'Pakaging Charge'),
)



HONORIFICS_CHOICES = (('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Ms', 'Ms'))


VIEW_TYPE_CHOICES = (
    ("CreateView", "CreateView"),
    ("DashboardView", "DashboardView"),
    ("DeleteView", "DeleteView"),
    ("DetailView", "DetailView"),
    ("ListView", "ListView"),
    ("TemplateView", "TemplateView"),
    ("UpdateView", "UpdateView"),
    ("View", "View"),
)

MODULE_CHOICES = [("accounts", "ACCOUNTS"), ("accounting", "ACCOUNTING"), ("core", "core"), ("employees", "employees"), ("invoices", "invoices"), ("masters", "MASTERS")]

PAYMENT_STATUS = (("paid", "Paid"), ("partialy_paid", "Partially Paid"), ("unpaid", "Unpaid"))


INVOICE_STAGE_CHOICES = (('invoice', 'Invoice'), ('estimate', 'Estimate'))

INVOICE_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("packing", "Packing"),
        ("loading", "Loading"),
        ("loaded", "Loaded"),
        ("completed", "Completed"),
    ]

ATTENDANCE_STATUS = (
    ('Present','Present'),
    ('Holiday','Holiday'),
    ('Absent','Absent'),
)

PAYMENT_PERIOD_CHOICES = (
    [(str(i), calendar.month_name[i]) for i in range(5, 13)] + [(str(i), calendar.month_name[i]) for i in range(1, 5)]
)   

FEE_TYPE = (
    ("one_time", "One Time"),
    ("installment", "Installment"),
    ("finance", "Finance"),
)

INSTALLMENT_TYPE_CHOICES = (
    ("regular", "Regular Installment"),
    ("special", "Special Installment"),
    ("custom", "Custom Installment"),
)

FEE_STRUCTURE_TYPE = (
    ("first_payment", "First Payment"),
    ("second_payment", "Second Payment"),
    ("third_payment", "Third Payment"),
    ("fourth_payment", "Fourth Payment"),
)

RELIGION_CHOICES = (
    ('Hindu', 'Hindu'),
    ('Muslim', 'Muslim'),
    ('Christian', 'Christian'),
    ('Other', 'Other'),
)

SYLLABUS_MONTH_CHOICE = (
    ('month_1', 'Month 1'),
    ('month_2', 'Month 2'),
    ('month_3', 'Month 3'),
    ('month_4', 'Month 4'),
)

SYLLABUS_WEEK_CHOICE = (
    ('week_1', 'Week 1'),
    ('week_2', 'Week 2'),
    ('week_3', 'Week 3'),
    ('week_4', 'Week 4'),
)

STUDENT_STAGE_STATUS_CHOICES = (
    ('active', "Active / Ongoing"), 
    ('inactive', "Inactive (Fee Paid, Not Joined)"),
    ('on_hold', "On Hold / Break"),  
    ('completed', "Course Completed"), 
    ('internship', "On Internship"),  
    ('placed', "Placed"), 
    ('dropped', "Dropped Out"),  
    ('terminated', "Terminated by Management"),
)

PLACEMENT_SOURCE_CHOICES = (
    ("institute", "Institute / Campus Placement"),
    ("self", "Self Search (Own Interview)"),
    ("referral", "Referral"),
    ("not_applicable", "Not Applicable"),
)

COURSE_MODE_CHOICES = (
    ("offline", "Offline"),
    ("online", "Online"),
)

REQUEST_SUBMISSION_STATUS_CHOICES = (("forwarded", "Forwarded"), ("re_assign", "Re Assign"), ("approved", "Completed"), ("rejected", "Rejected"), ("pending", "Pending"),)

PAYROLL_STATUS = (("pending", "Pending"), ("completed", "Completed"))

SYLLABUS_STATUS_CHOICES = (("pending", "Pending"), ("completed", "Completed"))

BATCH_STATUS_CHOICES = (("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"))

LEAVE_STATUS_CHOICES = (("approved", "Approved"), ("rejected", "Rejected"), ("pending", "Pending"))

RATING_CHOICES = [
    ('1', 'Poor'),
    ('2', 'Fair'),
    ('3', 'Good'),
    ('4', 'Very Good'),
    ('5', 'Excellent'),
]

FEEDBACK_TYPE_CHOICES = [
    ('faculty', 'Faculty'),
    ('fao', 'FAO'),
    ('other', 'Other')
]

INTERVIEW_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
]

BATCH_TYPE_CHOICES = [
    ('forenoon', 'FN'),
    ('afternoon', 'AN'),
    ('evening', 'EG'),
]