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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('signup/', UserSignupView.as_view(), name='user_signup'),
    path('verify/<int:user_id>/', EmailVerificationView.as_view(), name='email_verification'),
    path('login/', CustomTokenLoginView.as_view(), name='user_login'),
    path('logout/', UserLogoutView.as_view(), name='custom_logout'),
    path('update/', UserUpdateView.as_view(), name='user-update'),



]
