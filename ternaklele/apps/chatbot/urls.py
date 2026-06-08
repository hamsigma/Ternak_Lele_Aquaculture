from django.urls import path
from .views import ChatView, ChatSessionListView, ChatSessionDetailView

urlpatterns = [
    path("", ChatView.as_view(), name="chatbot"),
    path("sessions/", ChatSessionListView.as_view(), name="chat-sessions"),
    path("sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
]
