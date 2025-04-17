from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('/login/'), name='root'),
    path('', include('core.urls')), 
    path('student/', include('student.urls')),
    path('professor/', include('professor.urls')),
]