from django.urls import path
from . import views 

app_name = "branhes"

urlpatterns =[
    path("", views.BranchListView.as_view(), name="branch_list"),
    path('new/branch/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branch/<str:pk>/update/', views.BranchUpdateView.as_view(), name='branch_update'),
    path('branch/<str:pk>/update/', views.BranchUpdateView.as_view(), name='branch_detail'),
    path('branch/<str:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
]