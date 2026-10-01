from django.urls import path
from .views import (
    RecordingUploadView,
    RecordingDetailView,
    UserRecordingsListView,
    ProgressMetricsView,
    ConversationScenariosListView,
    ConversationSessionListCreateView,
    ConversationSessionDetailView,
    ConversationTurnReplyView,
    ConcludeConversationSessionView,
)

urlpatterns = [
    path('', UserRecordingsListView.as_view(), name='recording-list'),
    path('upload/', RecordingUploadView.as_view(), name='recording-upload'),
    path('progress/', ProgressMetricsView.as_view(), name='recording-progress'),
    path('scenarios/', ConversationScenariosListView.as_view(), name='conversation-scenarios'),
    path('sessions/', ConversationSessionListCreateView.as_view(), name='conversation-sessions'),
    path('sessions/<uuid:pk>/', ConversationSessionDetailView.as_view(), name='conversation-session-detail'),
    path('sessions/<uuid:pk>/turn/', ConversationTurnReplyView.as_view(), name='conversation-turn-reply'),
    path('sessions/<uuid:pk>/conclude/', ConcludeConversationSessionView.as_view(), name='conversation-session-conclude'),
    path('<int:pk>/', RecordingDetailView.as_view(), name='recording-detail'),
]

