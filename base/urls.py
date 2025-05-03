from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('calendarSync/', views.calendarSync, name="calendarSync"),
    path('courseLoad/', views.courseLoad, name="courseLoad"),
    path('roadMap/', views.roadMap, name="roadMap"),
    path('waitListClearance', views.waitListClearance, name="waitListClearance"),
    path('openSeat/', views.openSeat, name="openSeat"),
    path('recommend_section/<int:course_id>/', views.recommend_section, name='recommend_section'),
    path('courses/', views.course_list, name='course_list'),
    path('survey/', views.survey_view, name='survey'),
    path('thank-you/', views.thank_you, name='survey_thankyou'),
    path('add_course/', views.add_course, name='add_course'),
    path('get_courses/<str:ids>/', views.get_courses, name='get_courses'),
    path('create_schedule/', views.create_schedule, name='create_schedule'),
    path('export_schedule/<int:schedule_id>/', views.export_schedule_to_google_calendar, name='export_schedule'),
    
]