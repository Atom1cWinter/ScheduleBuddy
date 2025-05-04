from django.urls import path
<<<<<<< HEAD

from . import views

=======
from . import views

from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views

>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb
urlpatterns = [
    path('', views.home, name="home"),
    path('calendarSync/', views.calendarSync, name="calendarSync"),
    path('courseLoad/', views.courseLoad, name="courseLoad"),
    path('roadMap/', views.roadMap, name="roadMap"),
    path('waitListClearance', views.waitListClearance, name="waitListClearance"),
    path('openSeat/', views.openSeat, name="openSeat"),
<<<<<<< HEAD
    path('sectionRec/', views.sectionRec, name="sectionRec"),
=======
    path('recommend_section/<int:course_id>/', views.recommend_section, name='recommend_section'),
>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb
    path('courses/', views.course_list, name='course_list'),
    path('survey/', views.survey_view, name='survey'),
    path('thank-you/', views.thank_you, name='survey_thankyou'),
    path('add_course/', views.add_course, name='add_course'),
    path('get_courses/<str:ids>/', views.get_courses, name='get_courses'),
<<<<<<< HEAD
    path('login/', views.login_view, name='login'),
=======
    path('create_schedule/', views.create_schedule, name='create_schedule'),
    path('export_schedule/<int:schedule_id>/', views.export_schedule_to_google_calendar, name='export_schedule'),
    path('login/', auth_views.LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),
>>>>>>> 40265fa96d43daf7e52e876c31df26ca56378ddb
]