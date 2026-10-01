from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    CurrentUserView,
    UserLanguageListCreateView,
    UserLanguageDetailView,
    UserLanguageSetPrimaryView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('languages/', UserLanguageListCreateView.as_view(), name='auth-user-languages'),
    path('languages/<int:pk>/', UserLanguageDetailView.as_view(), name='auth-user-language-detail'),
    path('languages/<int:pk>/set-primary/', UserLanguageSetPrimaryView.as_view(), name='auth-user-language-set-primary'),
]
