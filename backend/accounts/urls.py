from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/expert/', views.register_expert_view, name='register_expert'),
    
    # Password management
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # Dashboards
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    
    # Profile views
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    
    # Client specific views
    path('client/profile/', views.client_profile_view, name='client_profile'),
    path('client/documents/', views.client_documents_view, name='client_documents'),
    
    # Expert specific views
    path('expert/profile/', views.expert_profile_view, name='expert_profile'),
    
    # Admin specific views - with secure URL pattern
    path('management/secure8765/login/', views.admin_login_view, name='admin_login_view'),
    path('management/secure8765/create/', views.create_admin_user, name='create_admin_view'),
    path('expert/availability/', views.expert_availability_view, name='expert_availability'),
    path('expert/services/', views.expert_services_view, name='expert_services'),
    
    # Admin specific views
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/user/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('admin/create_user/', views.admin_create_user_view, name='admin_create_user'),
    path('admin/profile/edit/', views.admin_edit_profile_view, name='admin_edit_profile'),
    
    # API endpoints
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/update_profile/', views.api_update_profile, name='api_update_profile'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('verification-denied/', views.verification_denied, name='verification_denied'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('email-sent/', views.email_sent, name='email_sent'),
]