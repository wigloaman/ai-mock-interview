from django.urls import path
from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
    path('contact-us/', views.contact, name='contact'),
    path('feedback/', views.feedback, name='feedback'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    path('create-interview-session/', views.create_interview_session, name='create_interview_session'),
    path('start-interview/', views.start_interview, name='start_interview'),
    path('get_question/', views.get_question, name='get_question'),
    path('save-answer/', views.save_answer, name='save_answer'),
    path('get-answer-automatically/', views.get_answer_automatically, name='get_answer_automatically'),
    path('end-interview/', views.end_interview, name='end_interview'),
    path('display-interview-result/', views.display_result, name='display_result'),
    path('check-review-status/', views.check_review_status, name='check_review_status'),
    path('speak-text/', views.speak_text, name='speak_text'),
    path('transcribe-audio/', views.transcribe_audio, name='transcribe_audio'),
]
