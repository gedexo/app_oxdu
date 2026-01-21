from django.urls import path
from . import views

app_name = "accounting"

urlpatterns = [
    #ajax
    path("ajax/next-group-code/", views.ajax_get_next_group_code, name="ajax_get_next_group_code"),
    path("ajax/groups/", views.ajax_group_master_by_branch, name="ajax_group_master_by_branch"),
    path('api/account/<int:pk>/type/', views.get_account_type_api, name='account_type_api'),

    # Accounting Base View
    path("base/", views.AccountingBase.as_view(), name="accounting_base"),

    # group
    path("groups/", views.GroupMasterListView.as_view(), name="groupmaster_list"),
    path("groupmaster/<str:pk>/", views.GroupMasterDetailView.as_view(), name="groupmaster_detail"),
    path("new/groupmaster/", views.GroupMasterCreateView.as_view(), name="groupmaster_create"),
    path("groupmaster/<str:pk>/update/", views.GroupMasterUpdateView.as_view(), name="groupmaster_update"),
    path("groupmaster/<str:pk>/delete/", views.GroupMasterDeleteView.as_view(), name="groupmaster_delete"),    

    # account
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("account/<str:pk>/", views.AccountDetailView.as_view(), name="account_detail"),
    path("new/account/", views.AccountCreateView.as_view(), name="account_create"),
    path("account/<str:pk>/update/", views.AccountUpdateView.as_view(), name="account_update"),
    path("account/<str:pk>/delete/", views.AccountDeleteView.as_view(), name="account_delete"),
    
]   
