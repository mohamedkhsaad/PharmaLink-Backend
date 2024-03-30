from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from User.views import *  
from Doctor.views import *
from django.conf.urls.static import static
from django.conf import settings
from Prescription.views import *
from Drugs.views import *

# from django.conf.urls import url


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    # User
    path('user/signup/', UserSignupView.as_view(), name='user_signup'),
    path('user/verify/<int:user_id>/', EmailVerificationView.as_view(), name='email_verification'),
    path('user/resend-email-verification/', ResendEmailVerificationView.as_view(), name='resend_email_verification'),
    path('user/login/', CustomTokenLoginView.as_view(), name='user_login'),
    path('user/users/<int:user_id>/', UserInfoView.as_view(), name='user-info'),
    path('user/logout/', UserLogoutView.as_view(), name='custom_logout'),
    path('user/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('user/reset-password/<int:user_id>/', PasswordResetView.as_view(), name='password_reset'),
    # Prescription/User
    path('Prescription/user/prescriptions/', PatientPrescriptionsView.as_view(), name='user_prescriptions'),

    path('Prescription/user/activate-prescription/<int:prescription_id>/', ActivatePrescriptionView.as_view(), name='activate_prescription'),
    path('Prescription/user/<int:prescription_id>/activate/', ActivateDrugView.as_view(), name='activate_drug'),

    path('Prescription/user/deactivate-prescription/<int:prescription_id>/', DeActivatePrescriptionView.as_view(), name='deactivate_prescription'),
    path('Prescription/user/<int:prescription_id>/deactivate/', DeActivateDrugView.as_view(), name='deactivate_drug'),

    path('Prescription/user/auto-deactivate-prescription/<int:prescription_id>/', AutomaticDeactivateView.as_view(), name='auto_deactivate_prescription'),

    path('Prescription/user/<int:prescription_id>/delete/', DeletePrescriptionView.as_view(), name='delete_prescription'),
    path('Prescription/user/active-prescriptions/', ActivePrescriptionsForUserView.as_view(), name='active_prescriptions_for_user'),
    path('Prescription/user/prescriptions/Doctorinfo/', PatientPrescriptionsDoctorInfoView.as_view(), name='user_prescriptions_doctorinfo'),
    path('Prescription/user/state-prescriptions/Doctorinfo/', ActivePrescriptionsForUserDoctorinfoView.as_view(), name='user_prescriptions_doctorinfo'),
    path('Prescription/user/HomePage/', HomePageinfoView.as_view(), name='user_prescriptions_homepage'),

    # Doctor
    path('doctor/signup/', DoctorSignupView.as_view(), name='doctor_signup'),
    path('doctor/login/', DoctorCustomTokenLoginView.as_view(), name='doctor_login'),
    path('doctor/doctors/<int:doctor_id>/', DoctorInfoView.as_view(), name='user-info'),
    path('doctor/verify/<int:doctor_id>/', DoctorEmailVerificationView.as_view(), name='email_verification'),
    path('doctor/resend-email-verification/', DoctorResendEmailVerificationView.as_view(), name='resend_email_verification'),

    path('doctor/update/', DoctorUpdateView.as_view(), name='user-update'),
    path('doctor/logout/',DoctorLogoutView.as_view(), name='doctor_logout'),
    path('doctor/password/reset/', DoctorPasswordResetRequestView.as_view(), name='Doctor_password_reset_request'),
    path('doctor/reset-password/<int:user_id>/', DoctorPasswordResetView.as_view(), name='password_reset'),
    path('doctor/doctor_phone/<int:doctor_id>/', DoctorPhoneNumberView.as_view(), name='user-info'),
    # Prescription/doctor
    path('Prescription/doctor/prescriptions/', DoctorPrescriptionsView.as_view(), name='doctor_prescriptions'),

    # Prescription 
    path('Prescription/drug_search/', MedicineSearchView.as_view(), name='medicine-search'),
    path('Prescription/start-session/', StartSessionView.as_view(), name='start_session'),
    path('Prescription/verify-session/', VerifySessionView.as_view(), name='verify_session'),
    path('Prescription/end-session/', EndSessionView.as_view(), name='end_session'),

    path('Prescription/create-prescription/', CreatePrescriptionView.as_view(), name='create_prescription'),
    path('Prescription/get-prescription/<int:prescription_id>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('Prescription/Update-prescription/<int:prescription_id>/', UpdatePrescriptionView.as_view(), name='update_prescription'),
    path('Prescription/prescriptions/<int:prescription_id>/', DeletePrescriptionView.as_view(), name='delete_prescription'),
    # Prescriptions during the session
    path('Prescription/doctor/<int:user_id>/prescriptions/', DoctorPrescriptionsForUserView.as_view(), name='doctor_prescriptions_for_user'),
    path('Prescription/user-prescriptions/', UserPrescriptionsView.as_view(), name='user_prescriptions'),
    path('Prescription/active-prescriptions/', ActivePrescriptionsView.as_view(), name='active_prescriptions'),
    
    # Drugs
    path('Drugs/<int:prescription_id>/check-drug-interaction/', DrugInteractionCheckView.as_view(), name='check_drug_interaction'),
    path('Drugs/check-drug-interaction-TradeName/', DrugInteractionByTradeNameView.as_view(), name='check_drug_interaction_by_tradename'),
    path('Drugs/check-drug-interaction-All/', DrugInteractionCheckViewForAllUserPrescriptions.as_view(), name='check_drug_interaction_for_all_user_prescriptions'),
    path('Drugs/User/check-interactions/', DrugInteractionCheckViewForUser.as_view(), name='user_check_interactions'),


    # Chat
    # path('Chat/messages/<int:receiver_id>/', ChatMessageCreateView.as_view(), name='chat-message-create'),
    # path('Chat/messages/list/<int:channel_id>/', ChatMessageListView.as_view(), name='chat-message-list'),
    # path('Chat/channel/', ChatChannelCreateView.as_view(), name='chat-channel-create'),
    # path('', include('Chat.urls')),

    # path('ws/chat/', ChatConsumer.as_asgi()),  # Directly include the WebSocket URL here

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
