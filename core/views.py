from django.shortcuts import render, redirect
from django.contrib.auth import login, logout 
from core.models import UserDetails, RoleMaster, StateMaster, CityMaster, CourseDetails
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.core.validators import EmailValidator, ValidationError
import re

def login_view(request):
    if request.user.is_authenticated:
        role = request.user.role.role_name if request.user.role else None
        if role == 'student':
            return redirect('student_dashboard')
        elif role == 'professor':
            return redirect('professor_dashboard')
        elif role == 'admin':
            return redirect('/admin/')
        return render(request, 'core/dashboard.html', {'error': 'No role assigned'})

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        errors = {}

        if not email:
            errors['email'] = 'Email is required'
        else:
            try:
                EmailValidator()(email)
            except ValidationError:
                errors['email'] = 'Enter a valid email'

        if not password:
            errors['password'] = 'Password is required'

        if errors:
            return render(request, 'core/login.html', {'errors': errors, 'email': email})

        try:
            user = UserDetails.objects.get(email=email)
            if check_password(password, user.password):
                login(request, user)
                role = user.role.role_name if user.role else None
                if role == 'student':
                    return redirect('student_dashboard')
                elif role == 'professor':
                    return redirect('professor_dashboard')
                elif role == 'admin':
                    return redirect('/admin/')
                return render(request, 'core/dashboard.html', {'error': 'No role assigned'})
            else:
                errors['password'] = 'Invalid email or password, try again!'
                return render(request, 'core/login.html', {'errors': errors, 'email': email})
        except UserDetails.DoesNotExist:
            errors['email'] = 'Invalid email or password'
            return render(request, 'core/login.html', {'errors': errors, 'email': email})
    
    return render(request, 'core/login.html')

def register_view(request):
    states = StateMaster.objects.filter(state_isAct=True)
    cities = CityMaster.objects.filter(city_isAct=True)
    courses = CourseDetails.objects.filter(course_isAct=True)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        user_gender = request.POST.get('user_gender', '').strip()
        user_phNo = request.POST.get('user_phNo', '').strip()
        state_id = request.POST.get('state')
        city_id = request.POST.get('city')
        course_id = request.POST.get('course')
        errors = {}

        if not email:
            errors['email'] = 'Email is required'
        else:
            try:
                EmailValidator()(email)
            except ValidationError:
                errors['email'] = 'Enter a valid email'
            if UserDetails.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered'

        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'
        elif not re.search(r'[A-Za-z].*[0-9]|[0-9].*[A-Za-z]', password):
            errors['password'] = 'Password needs letters and numbers, make it good!'

        if not first_name:
            errors['first_name'] = 'First name is required'
        if not last_name:
            errors['last_name'] = 'Last name is required'
        
        if not course_id:
            errors['course'] = 'Course is required'
        if not state_id:
            errors['state'] = 'State is required'
        if not city_id:
            errors['city'] = 'City is required'



        if not user_gender:
            errors['user_gender'] = 'Gender is required, figure it out!'
        elif user_gender not in ['Male', 'Female', 'Other']:
            errors['user_gender'] = 'Pick Male, Female, or Other'

        if not user_phNo:
            errors['user_phNo'] = 'Phone number is required'
        elif not re.match(r'^\d{10}$', user_phNo):
            errors['user_phNo'] = 'Phone number must be 10 digits'

        if errors:
            return render(request, 'core/register.html', {
                'errors': errors,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'user_gender': user_gender,
                'user_phNo': user_phNo,
                'state_id': state_id,
                'city_id': city_id,
                'course_id': course_id,
                'states': states,
                'cities': cities,
                'courses': courses
            })

        student_role, _ = RoleMaster.objects.get_or_create(role_name='student', defaults={'role_isAct': True})

        user = UserDetails(
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_gender=user_gender,
            user_phNo=user_phNo,
            state_id=state_id if state_id else None,
            city_id=city_id if city_id else None,
            role=student_role,
            course_id=course_id if course_id else None,
            user_isAct=True
        )
        user.password = make_password(password)
        user.save()

        login(request, user)
        return redirect('student_dashboard')

    return render(request, 'core/register.html', {
        'states': states,
        'cities': cities,
        'courses': courses
    })

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)  
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    role = user.role.role_name if user.role else None
    if role == 'student':
        return redirect('student_dashboard')
    elif role == 'professor':
        return redirect('professor_dashboard')
    elif role == 'admin':
        return redirect('/admin/')
    return render(request, 'core/dashboard.html', {'error': 'No role assigned'})