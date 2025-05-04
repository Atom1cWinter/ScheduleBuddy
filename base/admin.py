from django.contrib import admin
<<<<<<< HEAD
from .models import Course
=======
from .models import Course, Profile
>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb

# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    #list_display = ('title', 'course_number', 'professor', 'start_date', 'end_date', 'class_type', 'location')
    #list_filter = ('class_type', 'meeting_dates')
<<<<<<< HEAD
    search_fields = ('title', 'course_number', 'professor')
=======
    search_fields = ('title', 'course_number', 'professor')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user' , 'survey_results')
>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb
