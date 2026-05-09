from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('service/<slug:slug>/', views.service_page, name='service'),
    path('post-job/', views.post_job, name='post_job'),
    
    path('login/', views.login_view, name='login'),
    path('book/<int:wid>/', views.hire_worker, name='hire_worker'),
    path('my-hires/', views.my_hires, name='my_hires'),
    path('login/', views.login_view, name='login'),
    
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('worker-home/', views.worker_home, name='worker_home'),
    path('contractor-home/', views.contractor_home, name='contractor_home'),
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('worker/hires/', views.worker_hires, name='worker_hires'),
    path('worker/area/', views.worker_area, name='worker_area'),
    path('worker/availability/', views.worker_availability, name='worker_availability'),
    path('contractor-dashboard/', views.contractor_dashboard, name='contractor_dashboard'),
    
    path('hire/<int:bid>/<str:status>/', views.update_hire_status, name='update_hire'),
    path('register-user/', views.register_user, name='register_user'),
    path('register-worker/', views.register_worker, name='register_worker'),
    path('bulk-hire/', views.bulk_hire, name='bulk_hire'),
    path('worker/edit/', views.edit_worker_profile, name='edit_worker_profile'),
    path('worker/toggle/', views.toggle_worker_availability, name='toggle_worker'),
    path('services/', views.services_page, name='services'),
    path('register-contractor/', views.register_contractor, name='register_contractor'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('contractor-dashboard/', views.contractor_dashboard, name='contractor_dashboard'),
    path('bulk-action/<int:bid>/<str:action>/', views.bulk_action, name='bulk_action'),
    path('save-contractor-location/', views.save_contractor_location, name='save_contractor_location'),
    path('save-worker-location/', views.save_worker_location, name='save_worker_location'),
    path('contractor/edit/', views.edit_contractor_profile, name='edit_contractor_profile'),
    path('review/hire/<int:bid>/', views.submit_review, name='submit_review'),
    path('review/bulk/<int:bid>/', views.submit_bulk_review, name='submit_bulk_review'),
    path('chatbot/', views.chatbot_reply, name='chatbot_reply'),
    path('home-v4/', views.landing_page, name='landing_page'),

    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
