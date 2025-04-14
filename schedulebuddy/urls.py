
from django.contrib import admin
from django.urls import path, include
from . import views





urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('add_course/', views.add_course, name='add_course'),
    path('get_courses/<int:course_id>/', views.get_courses, name='get_courses')

]
