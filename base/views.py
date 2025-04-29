from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Profile  #need to import your Profile model
from .forms import ProfileForm  # need to create this form
from .models import Course # course template import
from .forms import SchedulingSurveyForm
from .models import SchedulingSurvey, Course, Section
import random

def home(request):
    return render(request, 'base/home.html')

def calendarSync(request):
    return render(request, 'base/calendarSync.html')



def roadMap(request):
    return render(request, 'base/roadMap.html')

def waitListClearance(request):
    return render(request, 'base/waitListClearance.html')

def openSeat(request):
    return render(request, 'base/openSeat.html')

def sectionRec(request):
    return render(request, 'base/sectionRec.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        Profile.objects.create(user=request.user)
        profile = request.user.profile
    
    return render(request, 'profiles/profile.html', {'profile': profile})

@login_required
def profile_edit(request):
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'profiles/profile_edit.html', {'form': form})


def course_list(request):
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})

def add_course(request):
    if request.method == 'POST':
        # Extract data from request
        title = request.POST.get('title')
        course_number = request.POST.get('course_number')
        professor = request.POST.get('professor')
        start_date = request.POST.get('start_date')
        meeting_dates = request.POST.get('meeting_dates')
        meeting_times = request.POST.get('meeting_times')
        end_date = request.POST.get('end_date')
        class_type = request.POST.get('class_type')
        location = request.POST.get('location')

        # create and save course
        course = Course.objects.create(
            title = title,
            course_number = course_number,
            professor = professor,
            start_date = start_date,
            meeting_dates = meeting_dates,
            meeting_times = meeting_times,
            end_date = end_date,
            class_type = class_type,
            location = location
        )
        return JsonResponse({'message' : 'Course added successfully!', 'course_id' : course.id})
    else:
        return JsonResponse({'error' : 'Invalid request method. Use POST.'}, status = 400)
    
    
def get_courses(request):
        # Function requires course grabbing course ID using dynamic URL parameter
        # Add course ID at the end of URL request
        if request.method == 'GET':
            # split URL into IDs and fetch courses
            id_list = ids.split(',')
            courses = Course.objects.filter(id__in = id_list).values(
                'id',
                'title',
                'course_number',
                'professor',
                'start_date',
                'meeting_dates',
                'meeting_times',
                'end_date',
                'class_type',
                'location',
            )
            # return course details as JSON
            return JsonResponse({'courses' : list(courses)})
        else:
            return JsonResponse({'error': 'Invalid request method. Use GET'}, status = 400)
        
def survey_view(request):
    if request.method == 'POST':
        form = SchedulingSurveyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('survey_thankyou')
    else:
        form = SchedulingSurveyForm()
    return render(request, 'base/survey.html', {'form': form})

def thank_you(request):
    return render(request, 'base/thankyou.html')
@login_required
def courseLoad(request):
    user = request.user
    try:
        survey = SchedulingSurvey.objects.get(user=user)
    except SchedulingSurvey.DoesNotExist:
        return render(request, 'no_survey.html')

    all_courses = Course.objects.all()
    suggested_courses = random.sample(list(all_courses), min(5, len(all_courses)))

    schedule = []
    for course in suggested_courses:
        sections = Section.objects.filter(course=course)
        if sections.exists():
            schedule.append(sections.first())

    return render(request, 'courseLoad.html', {
        'survey': survey,
        'schedule': schedule,
    })