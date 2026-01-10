from . import views
from django.urls import path


app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),

    #ID Card
    path("id-card/<str:pk>/", views.IDCardView.as_view(), name="id_card"),
    path("id-card/", views.IDCardView.as_view(), name="my_id_card"),

    path('firebase-messaging-sw.js', views.ServiceWorkerView.as_view(), name='firebase_sw'),

    #company profile
    path("company-profile/", views.CompanyProfileView.as_view(), name="company_profile"),
    path("company-profile/create/", views.CompanyProfileCreateView.as_view(), name="company_profile_create"),
    path("company-profile/<str:pk>/", views.CompanyProfileUpdateView.as_view(), name="company_profile_update"),
    path("company-profile/<str:pk>/delete/", views.CompanyProfileDeleteView.as_view(), name="company_profile_delete"),

    
]
