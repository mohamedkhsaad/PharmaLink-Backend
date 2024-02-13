"""
URL configuration for PharmaLink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from User.views import *  # Replace 'yourapp' with your actual app name
from Doctor.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('user/signup/', UserSignupView.as_view(), name='user_signup'),
    path('user/verify/<int:user_id>/', EmailVerificationView.as_view(), name='email_verification'),
    path('user/login/', CustomTokenLoginView.as_view(), name='user_login'),
    path('user/logout/', UserLogoutView.as_view(), name='custom_logout'),
    path('user/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('user/reset-password/<int:user_id>/', PasswordResetView.as_view(), name='password_reset'),
    path('doctor/signup/', DoctorSignupView.as_view(), name='doctor_signup'),
    path('doctor/login/', DoctorCustomTokenLoginView.as_view(), name='doctor_login'),
    path('doctor/verify/<int:doctor_id>/', DoctorEmailVerificationView.as_view(), name='email_verification'),
    path('doctor/update/', DoctorUpdateView.as_view(), name='user-update'),
    path('doctor/logout/',DoctorLogoutView.as_view(), name='doctor_logout'),
    path('doctor/password/reset/', DoctorPasswordResetRequestView.as_view(), name='Doctor_password_reset_request'),
    path('doctor/reset-password/<int:user_id>/', PasswordResetView.as_view(), name='password_reset'),

]
