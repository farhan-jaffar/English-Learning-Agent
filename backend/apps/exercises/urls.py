from django.urls import path
from .views import ExerciseListCreateView, ExerciseDetailView, NextExerciseView

urlpatterns = [
    path('', ExerciseListCreateView.as_view(), name='exercise-list-create'),
    path('next/', NextExerciseView.as_view(), name='exercise-next'),
    path('<int:pk>/', ExerciseDetailView.as_view(), name='exercise-detail'),
]
