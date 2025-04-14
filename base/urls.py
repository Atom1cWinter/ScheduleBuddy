from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('calendarSync/', views.calendarSync, name="calendarSync"),
    path('courseLoad/', views.courseLoad, name="courseLoad"),
    path('roadMap/', views.roadMap, name="roadMap"),
    path('waitListClearance', views.waitListClearance, name="waitListClearance"),
    path('openSeat/', views.openSeat, name="openSeat"),
    path('sectionRec/', views.sectionRec, name="sectionRec"),
    path('courses/', views.course_list, name='course_list'),
]