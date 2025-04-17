from django.urls import path
from . import views

urlpatterns = [
    path('', views.professor_dashboard, name='professor_dashboard'),
    path('add_quiz/', views.add_quiz, name='add_quiz'),
    #path('update_quiz/<int:quiz_id>/', views.update_quiz, name='update_quiz'),
    path('delete_quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    path('quiz_responses/<int:quiz_id>/', views.quiz_responses, name='quiz_responses'),
    path('student_responses/<int:quiz_id>/<int:student_id>/', views.student_responses, name='student_responses'),
    path('profile/', views.profile, name='professor_profile'),
]