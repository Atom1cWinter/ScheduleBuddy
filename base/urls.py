from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home Page
    path('', views.home, name="home"),

    # Survey and Recommendations
    path('survey/', views.survey_view, name='survey'),
    path('thank-you/', views.thank_you, name='survey_thankyou'),
    path('recommend_section/<int:course_id>/', views.recommend_section, name='recommend_section'),
    path('recommend_sections/', views.recommend_sections, name='recommend_sections'),

    # Course Filtering and Management
    path('filter_courses/', views.filter_courses, name='filter_courses'),
    path('add_course/', views.add_course, name='add_course'),
    path('get_courses/<str:ids>/', views.get_courses, name='get_courses'),

    # Schedule Management
    path('create_schedule/', views.create_schedule, name='create_schedule'),
    path('add_to_schedule/', views.add_to_schedule, name='add_to_schedule'),
    path('export_schedule/<int:schedule_id>/', views.export_schedule, name='export_schedule'),
    path('view_schedule/<int:schedule_id>/', views.view_schedule, name='view_schedule'),

    # Miscellaneous Features
    path('calendar_sync/', views.calendarSync, name="calendar_sync"),
    path('course_load/', views.courseLoad, name="course_load"),
    # Removed Roadmap
    # Removed Waitlist Clearance 
    # Removed Open Seat

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
]