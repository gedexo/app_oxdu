from . import views
from django.urls import path


app_name = "accounts"

urlpatterns = [
    path("", views.UserListView.as_view(), name="user_list"),
    path("user/<str:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("new/user/", views.UserCreateView.as_view(), name="user_create"),
    path("new/user/<pk>/", views.UserCreateView.as_view(), name="user_create"),
    path("new/student/user/", views.StudentUserCreateView.as_view(), name="student_user_create"),
    path("new/student/user/<pk>/", views.StudentUserCreateView.as_view(), name="student_user_create"),
    path("partner/<int:pk>/account/create/", views.PartnerUserCreateView.as_view(), name="partner_user_create"),
    path("partner/<int:pk>/account/update/", views.PartnerUserUpdateView.as_view(), name="partner_user_update"),
    path("student/user/<str:pk>/update/", views.StudentUserUpdateView.as_view(), name="student_user_update"),
    path("user/<str:pk>/update/", views.UserUpdateView.as_view(), name="user_update"),
    path("user/<str:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
]
