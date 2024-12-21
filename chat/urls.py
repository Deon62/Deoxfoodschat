from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('process-voice/', views.process_voice, name='process_voice'),
    path('get-response/', views.get_bot_response, name='get_response'),
]
