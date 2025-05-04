from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Profile  # need to import your Profile model
from .forms import ProfileForm  # need to create this form
from .models import Course # course template import
from .forms import SchedulingSurveyForm
from .models import SchedulingSurvey, Course, Section
from .models import Schedule # Calendar setup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.db.models import Q # used for section rec
from django.contrib.auth.forms import UserCreationForm # for user registration
from django.contrib import messages # also for user registration

import random
import datetime

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
            ids = request.GET.get('ids', '')  # Extract 'ids' from query parameters
            id_list = ids.split(',') if ids else []  # Split only if 'ids' is not empty
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

def create_schedule(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        section_ids = request.POST.getlist('sections') # List of section IDs
        sections = Section.objects.filter(id__in = section_ids)

        schedule = Schedule.objects.create(user = request.user, name = name)
        schedule.sections.set(sections)

        return JsonResponse({'message' : 'Schedule created successfully!', 'schedule_id' : schedule.id})
    else:
        sections = Section.objects.all()
        return render(request, 'create_schedule.html', {'sections' : sections})
    
def export_schedule_to_google_calendar(request, schedule_id):
    # Load the schedule
    schedule = Schedule.objects.get(id = schedule_id, user=request.user)
    sections = schedule.sections.all()

    # Load Google Calendar credentials
    creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    # Iterate through sections and add them to Google Calendar
    for section in sections:
        # Format the recurrence rule for meeting days
        meeting_days = []
        if section.mo: meeting_days.append('MO')
        if section.tu: meeting_days.append('TU')
        if section.we: meeting_days.append('WE')
        if section.th: meeting_days.append('TH')
        if section.fr: meeting_days.append('FR')
        if section.sa: meeting_days.append('SA')
        if section.su: meeting_days.append('SU')

        # create the event
        event = {
            'summary': section.course.name, # Course name
            'description': f"Start Date: {section.start_date}, End Date: {section.end_date}",
            'start': {
                'dateTime': f"{section.start_date}T{section.begins}", # Start date and time
                'TimeZone': 'America/New_York', # Default Timezone for UNCC
            },
            'end': {
                'dateTime': f"{section.start_date}T{section.ends}", # End date and time
                'timeZone': 'America/New_York',
            },
            'recurrence': [
                f"RRULE:FREQ=WEEKLY;BYDAY={','.join(meeting_days)};UNTIL={section.end_date.strftime('%Y%m%d')}T235959Z"
            ],
        }

        # Insert the event into Google Calendar
        service.events().insert(calendarId='primary', body = event).execute()

    return JsonResponse({'message' : 'Schedule exported to Google Calendar successfully!'})

@login_required
def calendarySync(request):
    # Retrive the user's schedule (assuming one schedule per user)
    try:
        schedule = Schedule.objects.get(user=request.user)
    except Schedule.DoesNotExist:
        return render(request, 'base/calendarSync.html', {'error': 'No schedule found.'})
    
    return render(request, 'base/calendarSync.html', {'schedule_id' : 'schedlue.id'})

@login_required
def recommend_section(request, course_id):
    user = request.user

    # Get the user's survey
    try:
        survey = SchedulingSurvey.objects.get(user=user)
    except SchedulingSurvey.DoesNotExist:
        return JsonResponse({'error': 'No survey found for the user'}, status=404)
    
    # Get the course
    course = get_object_or_404(Course, id=course_id)

    # Filter sections based on survey preferences
    sections = Section.objects.filter(course=course)

    # Apply filters based on survey preferences
    if not survey.night_classes_ok:
        sections = sections.filter(begins__lt="18:00:00") # Exclude sections starting after 6pm
    
    if survey.max_classes_per_day:
        # Example: Limit number of sections per day (requires more work and might be implemented later)
        pass

    # Example: Filter sections based on preferred days
    preferred_days = []
    if survey.clustered_or_spread == "Clustered":
        # Check if the user prefers Monday/Wednesday/Friday or Tuesday/Thursday
        if survey.preferred_distribution == "MWF":
            preferred_days = ['MO', 'WE', 'FR']
        elif survey.preferred_distribution == "TTH":
            preferred_days = ['TU', 'TH']
    elif survey.clustered_or_spread == "Spread":
        preferred_days = ['MO', 'TU', 'WE', 'TH', 'FR']

    if preferred_days:
        sections = sections.filter(
            Q(mo=True) & Q(mo__in=preferred_days) |
            Q(tu=True) & Q(tu__in=preferred_days) |
            Q(we=True) & Q(we__in=preferred_days) |
            Q(th=True) & Q(th__in=preferred_days) |
            Q(fr=True) & Q(fr__in=preferred_days)
        )

    # Filter sections based on time distribution
    if survey.time_distribution == "morning":
        sections = sections.filter(begins__lt="12:00:00")
    elif survey.time_distribution == "afternoon":
        sections = sections.filter(begins__gte="12:00:00", begins__lt="16:00:00")
    elif survey.time_distribution == "even":
        pass # No filter needed for evenly distributed
    
    # Sort sections by start time
    sections = sections.order_by('begins')

    # Return the recommended section
    if sections.exists():
        recommended_section = sections.first()
        return render(request, 'recommended_section.html', {
            'course': course,
            'section': recommended_section})
    else:
        return JsonResponse({'error' : 'No suitable sections found for the course'}, status=404)
    

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()  # Initialize an empty form for GET requests

    # Always pass the form to the template
    return render(request, 'base/register.html', {'form': form})

@login_required
def profile_view(request):
    # pass the logged-in user to the template
    return render(request, 'base/profile.html', {'user' : request.user})