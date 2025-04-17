from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserDetailsManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_isAct', True)
        extra_fields.setdefault('user_phNo', '0000000000')  
        extra_fields.setdefault('user_gender', 'O')  

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        if RoleMaster.objects.filter(role_name='admin').exists():
            extra_fields.setdefault('role', RoleMaster.objects.get(role_name='admin'))
        else:
            role = RoleMaster.objects.create(role_name='admin', role_isAct=True)
            extra_fields.setdefault('role', role)

        return self.create_user(email, password, **extra_fields)

class StateMaster(models.Model):
    state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=100)
    state_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.state_name

class CityMaster(models.Model):
    city_id = models.AutoField(primary_key=True)
    city_name = models.CharField(max_length=100)
    state = models.ForeignKey(StateMaster, on_delete=models.CASCADE)
    city_isAct = models.BooleanField(default=True)

    def __str__(self):  
        return self.city_name

class RoleMaster(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)
    role_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.role_name

class CourseDetails(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=150)
    course_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.course_name

class SubjectMaster(models.Model):
    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=150)
    course = models.ForeignKey(CourseDetails, on_delete=models.CASCADE)
    subject_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.subject_name

class UserDetails(AbstractUser):
    user_gender = models.CharField(
        max_length=1, 
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], 
        null=True, 
    )
    user_phNo = models.CharField(max_length=15, null=True, blank=True)
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(RoleMaster, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(CourseDetails, on_delete=models.SET_NULL, null=True, blank=True)
    user_isAct = models.BooleanField(default=True)

    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserDetailsManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

class QuizDetails(models.Model):
    quiz_id = models.AutoField(primary_key=True)
    quiz_title = models.CharField(max_length=150)
    quiz_rules = models.TextField()
    quiz_createdBy = models.ForeignKey(UserDetails, on_delete=models.CASCADE)
    subject = models.ForeignKey(SubjectMaster, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseDetails, on_delete=models.CASCADE)
    quiz_duration = models.PositiveIntegerField(default=30, help_text="Duration in minutes")  # New field, motherfucker
    quiz_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.quiz_title

class QuestionMaster(models.Model):
    question_id = models.AutoField(primary_key=True)
    question_text = models.TextField()
    quiz = models.ForeignKey(QuizDetails, on_delete=models.CASCADE)
    question_isAct = models.BooleanField(default=True)

    def __str__(self):
        return self.question_text

class OptionMaster(models.Model):
    option_id = models.AutoField(primary_key=True)
    option_text = models.TextField()
    question = models.ForeignKey(QuestionMaster, on_delete=models.CASCADE)
    option_isCorrect = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text

class UserResponsesDetails(models.Model):
    response_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserDetails, on_delete=models.CASCADE)
    question = models.ForeignKey(QuestionMaster, on_delete=models.CASCADE)
    option = models.ForeignKey(OptionMaster, on_delete=models.CASCADE)
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.question.question_text}"