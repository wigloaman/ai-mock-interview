from django.urls import path
from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit', views.update_profile, name='update_profile'),
]
