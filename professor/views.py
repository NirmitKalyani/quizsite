from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import QuizDetails, QuestionMaster, OptionMaster, UserResponsesDetails, UserDetails, CourseDetails, SubjectMaster
from django.utils import timezone
from django.db.models import Count, Max
import json

@login_required
def professor_dashboard(request):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    print(user.course)
    quizzes = QuizDetails.objects.filter(quiz_createdBy=user, quiz_isAct=True)
    courses = CourseDetails.objects.filter(course_id=user.course.course_id) if user.course else CourseDetails.objects.none()
    quizzes_data = []
    for quiz in quizzes:
        questions = [{
            'question_text': q.question_text,
            'question_id': q.question_id,
            'optionmaster_set': [{
                'option_text': opt.option_text,
                'option_isCorrect': opt.option_isCorrect
            } for opt in q.optionmaster_set.all()]
        } for q in quiz.questionmaster_set.all()]
        quizzes_data.append({
            'quiz_id': quiz.quiz_id,
            'quiz_title': quiz.quiz_title,
            'course': {'course_id': quiz.course.course_id, 'course_name': quiz.course.course_name},
            'questionmaster_set': questions
        })
    
    return render(request, 'professor/dashboard.html', {
        'quizzes': quizzes,
        'courses': courses,
        'quizzes_json': json.dumps(quizzes_data) 
    })



@login_required
def add_quiz(request):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    
    professor_course = user.course
    
    if not professor_course:
        return render(request, 'professor/add_quiz.html', {
            'error': 'No course assigned to your profile'
        })
    
    if request.method == 'POST':
        quiz_title = request.POST.get('quiz_title')
        subject_id = request.POST.get('subject')
        duration = request.POST.get('duration')
        questions = []
        
        i = 0
        while f'question_{i}' in request.POST:
            question_text = request.POST.get(f'question_{i}')
            qid = int(request.POST.get(f'qid_{i}', i + 1))
            options = [
                request.POST.get(f'option_{i}_0'),
                request.POST.get(f'option_{i}_1'),
                request.POST.get(f'option_{i}_2'),
                request.POST.get(f'option_{i}_3')
            ]
            correct_option = int(request.POST.get(f'correct_{i}', 0))
            if all(options):
                questions.append((question_text, qid, options, correct_option))
            i += 1
        
        if quiz_title and subject_id and questions:
            quiz = QuizDetails.objects.create(
                quiz_title=quiz_title,
                quiz_createdBy=user,
                course=professor_course, 
                subject_id=subject_id,
                quiz_duration=duration,
                quiz_isAct=True
            )
            # Rest of the quiz creation logic remains the same
            max_qid = QuestionMaster.objects.aggregate(Max('question_id'))['question_id__max'] or 0
            for q_text, qid, opts, correct in questions:
                if qid <= max_qid:
                    qid = max_qid + 1
                question = QuestionMaster.objects.create(
                    quiz=quiz,
                    question_text=q_text,
                    question_id=qid,
                    question_isAct=True
                )
                max_qid = max(max_qid, qid)
                for idx, opt_text in enumerate(opts):
                    OptionMaster.objects.create(
                        question=question,
                        option_text=opt_text,
                        option_isCorrect=(idx == correct)
                    )
            return redirect('professor_dashboard')
    
    
    subjects = SubjectMaster.objects.filter(course=professor_course)
    return render(request, 'professor/add_quiz.html', {
        'course': professor_course,
        'subjects': subjects
    })
   
@login_required
def delete_quiz(request, quiz_id):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, quiz_createdBy=user)
    
    if request.method == 'POST':
        quiz.quiz_isAct = False
        quiz.save()
        return redirect('professor_dashboard')
    
    return redirect('professor_dashboard')


@login_required
def quiz_responses(request, quiz_id):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, quiz_createdBy=user)
    responses = UserResponsesDetails.objects.filter(question__quiz=quiz).select_related('user', 'question', 'option')
    
    student_scores = {}
    for response in responses:
        student = response.user
        if student not in student_scores:
            student_scores[student] = {'score': 0, 'total': 0}
        student_scores[student]['total'] += 1
        if response.option.option_isCorrect:
            student_scores[student]['score'] += 1
    
    pass_count = sum(1 for s in student_scores.values() if s['score'] / s['total'] >= 0.5)
    fail_count = len(student_scores) - pass_count
    
    return render(request, 'professor/quiz_responses.html', {
        'quiz': quiz,
        'student_scores': student_scores,
        'pass_count': pass_count,
        'fail_count': fail_count
    })

@login_required
def student_responses(request, quiz_id, student_id):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, quiz_createdBy=user)
    student = get_object_or_404(UserDetails, id=student_id, role__role_name='student')
    responses = UserResponsesDetails.objects.filter(user=student, question__quiz=quiz).select_related('question', 'option')
    
    question_details = []
    for response in responses:
        question = response.question
        selected_answer = response.option.option_text
        try:
            correct_answer = question.optionmaster_set.get(option_isCorrect=True).option_text
        except OptionMaster.DoesNotExist:
            correct_answer = "No correct answer set"
        question_details.append({
            'question_text': question.question_text,
            'selected_answer': selected_answer,
            'correct_answer': correct_answer,
            'is_correct': selected_answer == correct_answer
        })
    
    score = sum(1 for q in question_details if q['is_correct'])
    total_questions = len(question_details)
    
    return render(request, 'professor/student_responses.html', {
        'quiz': quiz,
        'student': student,
        'question_details': question_details,
        'score': score,
        'total_questions': total_questions
    })

@login_required
def profile(request):
    user = request.user
    if user.role.role_name != 'professor':
        return redirect('dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        user_phNo = request.POST.get('user_phNo', user.user_phNo)
        email = request.POST.get('email', user.email)
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        
        if email != user.email and UserDetails.objects.filter(email=email).exists():
            return render(request, 'professor/profile.html', {
                'user': user,
                'error': 'This email’s already taken'
            })
        
        
        if password and password != password_confirm:
            return render(request, 'professor/profile.html', {
                'user': user,
                'error': 'Passwords don’t match'
            })
        
        
        user.first_name = first_name
        user.last_name = last_name
        user.user_phNo = user_phNo
        user.email = email
        if password:
            user.set_password(password)
        user.save()
        return redirect('professor_profile')
    
    return render(request, 'professor/profile.html', {'user': user})