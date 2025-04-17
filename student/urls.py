from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_dashboard, name='student_dashboard'),
    path('take_quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('results/', views.quiz_results, name='quiz_results'),
    path('result/<int:quiz_id>/', views.single_quiz_result, name='single_quiz_result'),
    path('profile/', views.profile, name='student_profile'),
]