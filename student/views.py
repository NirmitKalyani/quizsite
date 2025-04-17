from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import QuizDetails, QuestionMaster, OptionMaster, UserResponsesDetails, UserDetails
from django.utils import timezone

@login_required
@login_required
def student_dashboard(request):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    

    responses = UserResponsesDetails.objects.filter(user=user).select_related('question__quiz', 'option')
    completed_quizzes = QuizDetails.objects.filter(
        questionmaster__userresponsesdetails__user=user
    ).distinct()
    completed_quizzes_count = QuizDetails.objects.filter(
        questionmaster__userresponsesdetails__user=user
    ).distinct().count()
    total_questions = responses.count()
    correct_questions = responses.filter(option__option_isCorrect=True).count()
    incorrect_questions = total_questions - correct_questions
    

    quiz_history = []
    quizzes = QuizDetails.objects.filter(questionmaster__userresponsesdetails__user=user).distinct()
    for quiz in quizzes:
        quiz_responses = responses.filter(question__quiz=quiz)
        quiz_total = quiz_responses.count()
       
        quiz_correct = quiz_responses.filter(option__option_isCorrect=True).count()
        percentage = (quiz_correct / quiz_total * 100) if quiz_total > 0 else 0
        result = 'PASS' if percentage >= 35 else 'FAIL'
        quiz_history.append({
            'quiz_id': quiz.quiz_id,
            'subject': quiz.subject.subject_name,
            'correct_questions': quiz_correct,
            'total_questions': quiz_total,
            'percentage': int(percentage),
            'result': result
        })
    
    completed_quiz_ids = responses.values_list('question__quiz__quiz_id', flat=True).distinct()
    available_quizzes = QuizDetails.objects.filter(
        course=user.course,
        quiz_isAct=True
    ).exclude(quiz_id__in=completed_quiz_ids)
    return render(request, 'student/dashboard.html', {
        'available_quizzes': available_quizzes,
        'completed_quizzes': completed_quizzes,
        'completed_quizzes_count': completed_quizzes_count,
        'total_questions': total_questions,
        'correct_questions': correct_questions,
        'incorrect_questions': incorrect_questions,
        'quiz_history': quiz_history
    })

@login_required
def take_quiz(request, quiz_id):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, course=user.course, quiz_isAct=True)
    questions = QuestionMaster.objects.filter(quiz=quiz, question_isAct=True).prefetch_related('optionmaster_set')
    
    if UserResponsesDetails.objects.filter(user=user, question__quiz=quiz).exists():
        return redirect('single_quiz_result', quiz_id=quiz.quiz_id)
    
    if 'quiz_start_time' not in request.session:
        request.session['quiz_start_time'] = timezone.now().isoformat()
        request.session['quiz_id'] = quiz_id
        request.session['responses'] = {}
        request.session['current_question'] = 0
    
    quiz_start_time = timezone.datetime.fromisoformat(request.session['quiz_start_time'])
    time_left = quiz.quiz_duration * 60 - (timezone.now() - quiz_start_time).total_seconds()
    
    if time_left <= 0:
        submit_quiz(request, quiz_id, auto_submit=True)
        return redirect('single_quiz_result', quiz_id=quiz.quiz_id)
    
    current_question_idx = request.session['current_question']
    total_questions = len(questions)
    
    if current_question_idx >= total_questions:
        submit_quiz(request, quiz_id)
        return redirect('single_quiz_result', quiz_id=quiz.quiz_id)
    
    current_question = questions[current_question_idx]
    options = current_question.optionmaster_set.all()
    
    if request.method == 'POST':
        selected_option = request.POST.get(f'question_{current_question.question_id}')
        if selected_option:
            request.session['responses'][str(current_question.question_id)] = selected_option
        
        if 'next' in request.POST and current_question_idx < total_questions - 1:
            request.session['current_question'] += 1
        else:
            submit_quiz(request, quiz_id)
            return redirect('single_quiz_result', quiz_id=quiz.quiz_id)
        
        request.session.modified = True
        return redirect('take_quiz', quiz_id=quiz_id)
    
    return render(request, 'student/take_quiz.html', {
        'quiz': quiz,
        'question': current_question,
        'options': options,
        'time_left': int(time_left),
        'question_number': current_question_idx + 1,
        'total_questions': total_questions,
        'is_last_question': current_question_idx == total_questions - 1
    })

@login_required
def submit_quiz(request, quiz_id, auto_submit=False):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, course=user.course, quiz_isAct=True)
    questions = QuestionMaster.objects.filter(quiz=quiz, question_isAct=True)
    
    responses = request.session.get('responses', {})
    for question in questions:
        option_id = responses.get(str(question.question_id))
        if option_id:
            option = OptionMaster.objects.get(option_id=option_id, question=question)
            UserResponsesDetails.objects.create(
                user=user,
                question=question,
                option=option,
                response_date=timezone.now()
            )
    
    if 'quiz_start_time' in request.session:
        del request.session['quiz_start_time']
    if 'quiz_id' in request.session:
        del request.session['quiz_id']
    if 'responses' in request.session:
        del request.session['responses']
    if 'current_question' in request.session:
        del request.session['current_question']
    
    request.session.modified = True
    
    return redirect('single_quiz_result', quiz_id=quiz.quiz_id)



@login_required
def single_quiz_result(request, quiz_id):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    
    quiz = get_object_or_404(QuizDetails, quiz_id=quiz_id, course=user.course)
    responses = UserResponsesDetails.objects.filter(user=user, question__quiz=quiz).select_related('question__quiz', 'option')
    
    if not responses.exists():
        return redirect('student_dashboard')
    
    questions = QuestionMaster.objects.filter(quiz=quiz, question_isAct=True).prefetch_related('optionmaster_set')
    score = sum(1 for r in responses if r.option.option_isCorrect)
    total_questions = questions.count()
    
    quiz_duration = quiz.quiz_duration
    start_time = responses.first().response_date
    end_time = responses.last().response_date
    time_taken_seconds = (end_time - start_time).total_seconds()
    time_taken_minutes = round(time_taken_seconds / 60, 2)
    
    question_details = []
    for question in questions:
        user_response = responses.filter(question=question).first()
        selected_answer = user_response.option.option_text if user_response else "No answer selected"
        try:
            correct_answer = question.optionmaster_set.get(option_isCorrect=True).option_text
        except OptionMaster.DoesNotExist:
            correct_answer = "No correct answer set"
        
        question_details.append({
            'question_text': question.question_text,
            'selected_answer': selected_answer,
            'correct_answer': correct_answer,
            'is_correct': selected_answer == correct_answer if user_response else False
        })
    
    return render(request, 'student/single_result.html', {
        'quiz': quiz,
        'score': score,
        'total_questions': total_questions,
        'quiz_duration': quiz_duration,
        'time_taken': time_taken_minutes,
        'questions': question_details
    })

@login_required
def quiz_results(request):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    
    responses = UserResponsesDetails.objects.filter(user=user).select_related('question__quiz', 'option')
    quiz_ids = responses.values_list('question__quiz__quiz_id', flat=True).distinct()
    quizzes = QuizDetails.objects.filter(quiz_id__in=quiz_ids, course=user.course)
    
    quiz_details = []
    for quiz in quizzes:
        quiz_responses = responses.filter(question__quiz=quiz).order_by('response_date')
        questions = QuestionMaster.objects.filter(quiz=quiz, question_isAct=True).prefetch_related('optionmaster_set')
        score = sum(1 for r in quiz_responses if r.option.option_isCorrect)
        total_questions = questions.count()
        
        quiz_duration = quiz.quiz_duration
        start_time = quiz_responses.first().response_date
        end_time = quiz_responses.last().response_date
        time_taken_seconds = (end_time - start_time).total_seconds()
        time_taken_minutes = round(time_taken_seconds / 60, 2)
        
        question_details = []
        for question in questions:
            user_response = quiz_responses.filter(question=question).first()
            selected_answer = user_response.option.option_text if user_response else "No answer selected"
            try:
                correct_answer = question.optionmaster_set.get(option_isCorrect=True).option_text
            except OptionMaster.DoesNotExist:
                correct_answer = "No correct answer set"
            
            question_details.append({
                'question_text': question.question_text,
                'selected_answer': selected_answer,
                'correct_answer': correct_answer,
                'is_correct': selected_answer == correct_answer if user_response else False
            })
        
        quiz_details.append({
            'quiz': quiz,
            'score': score,
            'total_questions': total_questions,
            'quiz_duration': quiz_duration,
            'time_taken': time_taken_minutes,
            'questions': question_details
        })
    
    return render(request, 'student/results.html', {'quiz_details': quiz_details})

@login_required
def profile(request):
    user = request.user
    if user.role.role_name != 'student':
        return redirect('dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        user_phNo = request.POST.get('user_phNo', user.user_phNo)
        email = request.POST.get('email', user.email)
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        
        if email != user.email and UserDetails.objects.filter(email=email).exists():
            return render(request, 'student/profile.html', {
                'user': user,
                'error': 'This email’s already taken, Pick another.'
            })
        
        
        if password and password != password_confirm:
            return render(request, 'student/profile.html', {
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
        return redirect('student_profile')
    
    return render(request, 'student/profile.html', {'user': user})