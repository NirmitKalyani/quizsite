from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import *

class QuizDetailsForm(forms.ModelForm):
    class Meta:
        model = QuizDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'quiz_createdBy' in self.data:
            try:
                professor_id = int(self.data.get('quiz_createdBy'))
                user = UserDetails.objects.get(id=professor_id)
                if user.role.role_name == 'admin':
                    self.fields['course'].queryset = CourseDetails.objects.all()
                elif user.role.role_name == 'professor' and user.course:
                    self.fields['course'].queryset = CourseDetails.objects.filter(course_id=user.course.course_id)
                else:
                    self.fields['course'].queryset = CourseDetails.objects.none()
            except (ValueError, UserDetails.DoesNotExist):
                self.fields['course'].queryset = CourseDetails.objects.all()  # Default to all if shit’s fucked
        elif self.instance.pk and self.instance.quiz_createdBy:
            user = self.instance.quiz_createdBy
            if user.role.role_name == 'admin':
                self.fields['course'].queryset = CourseDetails.objects.all()
            elif user.role.role_name == 'professor' and user.course:
                self.fields['course'].queryset = CourseDetails.objects.filter(course_id=user.course.course_id)
            else:
                self.fields['course'].queryset = CourseDetails.objects.none()

@admin.register(UserDetails)
class UserDetailsAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'user_isAct')
    list_filter = ('role', 'user_isAct')
    search_fields = ('email', 'first_name', 'last_name')
    fields = ('email', 'password', 'first_name', 'last_name', 'user_gender', 'user_phNo', 'state', 'city', 'role', 'course', 'user_isAct', 'is_active', 'is_staff', 'is_superuser')

    def save_model(self, request, obj, form, change):
        if not change or 'password' in form.changed_data:
            if not obj.password.startswith('pbkdf2_sha256$'):
                obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(QuizDetails)
class QuizDetailsAdmin(admin.ModelAdmin):
    form = QuizDetailsForm
    list_display = ('quiz_title', 'quiz_createdBy', 'subject', 'course', 'quiz_duration', 'quiz_isAct')
    list_filter = ('quiz_isAct', 'course', 'subject')
    search_fields = ('quiz_title',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'quiz_createdBy':
            kwargs['queryset'] = UserDetails.objects.filter(role__role_name__in=['admin', 'professor'], user_isAct=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(StateMaster)
admin.site.register(CityMaster)
admin.site.register(RoleMaster)
admin.site.register(CourseDetails)
admin.site.register(SubjectMaster)
admin.site.register(QuestionMaster)
admin.site.register(OptionMaster)
admin.site.register(UserResponsesDetails)