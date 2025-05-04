from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, Course, Section, Schedule, SchedulingSurvey
from .forms import ProfileForm, SchedulingSurveyForm, CourseForm
import random


# Utility Functions
def filter_sections_by_survey(survey, sections):
    """Filter sections based on survey preferences."""
    # Exclude night classes if the user prefers not to take them
    if not survey.night_classes_ok:
        sections = sections.filter(begins__lt="18:00:00")  # Exclude sections starting after 6 PM

    # Filter by preferred time distribution
    if survey.time_distribution == "morning":
        sections = sections.filter(begins__lt="12:00:00")  # Morning classes before noon
    elif survey.time_distribution == "afternoon":
        sections = sections.filter(begins__gte="12:00:00", begins__lt="16:00:00")  # Afternoon classes
    elif survey.time_distribution == "evening":
        sections = sections.filter(begins__gte="16:00:00")  # Evening classes

    # Filter by preferred meeting days
    preferred_days = []
    if survey.preferred_distribution == "MWF":
        preferred_days = ['mo', 'we', 'fr']
    elif survey.preferred_distribution == "TTH":
        preferred_days = ['tu', 'th']
    elif survey.preferred_distribution == "Spread":
        preferred_days = ['mo', 'tu', 'we', 'th', 'fr']

    if preferred_days:
        day_filters = Q()
        if 'mo' in preferred_days:
            day_filters |= Q(mo=True)
        if 'tu' in preferred_days:
            day_filters |= Q(tu=True)
        if 'we' in preferred_days:
            day_filters |= Q(we=True)
        if 'th' in preferred_days:
            day_filters |= Q(th=True)
        if 'fr' in preferred_days:
            day_filters |= Q(fr=True)
        sections = sections.filter(day_filters)

    return sections.order_by('begins')  # Order by start time


def sort_sections_by_survey(survey, sections):
    """Sort sections based on how well they match the user's survey preferences."""
    def calculate_score(section):
        score = 0

        # Time preference scoring
        if survey.time_distribution == "morning" and section.begins and section.begins < "12:00:00":
            score += 3
        elif survey.time_distribution == "afternoon" and section.begins and "12:00:00" <= section.begins < "16:00:00":
            score += 2
        elif survey.time_distribution == "evening" and section.begins and section.begins >= "16:00:00":
            score += 1

        # Night class preference
        if not survey.night_classes_ok and section.begins and section.begins >= "18:00:00":
            score -= 5  # Penalize night classes if not preferred

        # Day preference scoring
        preferred_days = {
            'MWF': ['mo', 'we', 'fr'],
            'TTH': ['tu', 'th'],
            'Spread': ['mo', 'tu', 'we', 'th', 'fr']
        }.get(survey.preferred_distribution, [])

        if section.mo and 'mo' in preferred_days:
            score += 1
        if section.tu and 'tu' in preferred_days:
            score += 1
        if section.we and 'we' in preferred_days:
            score += 1
        if section.th and 'th' in preferred_days:
            score += 1
        if section.fr and 'fr' in preferred_days:
            score += 1

        return score

    # Annotate sections with scores and sort them
    sections_with_scores = [(section, calculate_score(section)) for section in sections]
    sorted_sections = sorted(sections_with_scores, key=lambda x: x[1], reverse=True)

    # Return only the sections, sorted by score
    return [section for section, score in sorted_sections]


def export_schedule_to_google_calendar(schedule):
    """Export a schedule to Google Calendar."""
    creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    for section in schedule.sections.all():
        meeting_days = []
        if section.mo: meeting_days.append('MO')
        if section.tu: meeting_days.append('TU')
        if section.we: meeting_days.append('WE')
        if section.th: meeting_days.append('TH')
        if section.fr: meeting_days.append('FR')
        if section.sa: meeting_days.append('SA')
        if section.su: meeting_days.append('SU')

        event = {
            'summary': section.course.name,
            'description': f"Start Date: {section.start_date}, End Date: {section.end_date}",
            'start': {'dateTime': f"{section.start_date}T{section.begins}", 'timeZone': 'America/New_York'},
            'end': {'dateTime': f"{section.start_date}T{section.ends}", 'timeZone': 'America/New_York'},
            'recurrence': [
                f"RRULE:FREQ=WEEKLY;BYDAY={','.join(meeting_days)};UNTIL={section.end_date.strftime('%Y%m%d')}T235959Z"
            ],
        }
        service.events().insert(calendarId='primary', body=event).execute()


# Views
def home(request):
    return render(request, 'base/home.html')

def thank_you(request):
    return render(request, 'base/thank_you.html')

def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('filter_courses')  # Redirect to the course filtering page after adding
    else:
        form = CourseForm()
    return render(request, 'base/add_course.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to the login page after successful registration
    else:
        form = UserCreationForm()
    return render(request, 'base/register.html', {'form': form})


@login_required
def profile_view(request):
    schedules = Schedule.objects.filter(user=request.user)
    last_schedule = schedules.last()  # Get the most recently created schedule

    # Handle profile editing
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'base/profile.html', {
        'schedules': schedules,
        'last_schedule': last_schedule,
        'form': form,
    })


@login_required
def survey_view(request):
    if request.method == 'POST':
        form = SchedulingSurveyForm(request.POST)
        if form.is_valid():
            # Save the survey
            survey = form.save(commit=False)
            survey.user = request.user
            survey.save()

            # Update the user's profile with the latest survey
            profile = request.user.profile
            profile.survey = survey
            profile.save()

            return redirect('survey_thankyou')
    else:
        # Prepopulate the form with the user's latest survey if it exists
        profile = request.user.profile
        form = SchedulingSurveyForm(instance=profile.survey if profile.survey else None)

    return render(request, 'base/survey.html', {'form': form})


def filter_courses(request):
    subject = request.GET.get('subject', '')
    course_number = request.GET.get('course_number', '')
    meeting_days = request.GET.getlist('meeting_days', [])
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')

    sections = Section.objects.all()
    if subject:
        sections = sections.filter(course__code__icontains=subject)
    if course_number:
        sections = sections.filter(course__name__icontains=course_number)
    if meeting_days:
        for day in meeting_days:
            sections = sections.filter(**{day.lower(): True})
    if start_time:
        sections = sections.filter(begins__gte=start_time)
    if end_time:
        sections = sections.filter(ends__lte=end_time)

    return render(request, 'base/filter_courses.html', {'sections': sections})


@login_required
def recommend_section(request, course_id):
    # Get the user's survey
    survey = request.user.profile.survey
    if not survey:
        return JsonResponse({'error': 'No survey found for the user. Please complete the survey first.'}, status=400)

    # Get the course
    course = get_object_or_404(Course, id=course_id)

    # Get all sections for the course
    sections = Section.objects.filter(course=course)

    # Filter sections based on survey preferences
    sections = filter_sections_by_survey(survey, sections)

    # Return the best-matching section
    if sections.exists():
        return render(request, 'base/recommended_section.html', {'course': course, 'section': sections.first()})
    else:
        return JsonResponse({'error': 'No suitable sections found for the course.'}, status=404)


@login_required
def recommend_sections(request):
    # Get the user's survey
    survey = request.user.profile.survey
    if not survey:
        return render(request, 'base/recommended_section.html', {'error': 'No survey found. Please complete the survey first.'})

    # Get the course_code input from the user
    course_code = request.GET.get('course_code', '').strip()
    if not course_code:
        return render(request, 'base/recommended_section.html', {'error': 'No course code provided.'})

    # Retrieve all sections for the specified course_code
    sections = Section.objects.filter(course_code__iexact=course_code)
    if not sections.exists():
        return render(request, 'base/recommended_section.html', {'error': f'No sections found for course code: {course_code}'})

    # Sort sections based on survey preferences
    sorted_sections = sort_sections_by_survey(survey, sections)

    return render(request, 'base/recommended_section.html', {
        'course_code': course_code,
        'sections': sorted_sections,
    })


@login_required
def add_to_schedule(request):
    if request.method == 'POST':
        section_ids = request.POST.getlist('section_ids')
        schedule_name = request.POST.get('schedule_name', 'My Schedule')
        schedule = Schedule.objects.create(user=request.user, name=schedule_name)
        sections = Section.objects.filter(id__in=section_ids)
        schedule.sections.set(sections)
        return JsonResponse({'message': 'Schedule created successfully!', 'schedule_id': schedule.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def export_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    export_schedule_to_google_calendar(schedule)
    return JsonResponse({'message': 'Schedule exported to Google Calendar successfully!'})


@login_required
def view_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    return render(request, 'base/view_schedule.html', {'schedule': schedule})


def get_courses(request, ids):
    # Split the comma-separated IDs
    course_ids = ids.split(',')

    # Query the database for the courses with the given IDs
    courses = Course.objects.filter(id__in=course_ids)

    # Serialize the course data into a JSON response
    course_data = [
        {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'credits': course.credits,
            'description': course.description,
        }
        for course in courses
    ]

    return JsonResponse({'courses': course_data})


@login_required
def create_schedule(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # Handle adding a course to the session-based list
        if action == 'add_course':
            section_id = request.POST.get('section_id')
            if 'selected_courses' not in request.session:
                request.session['selected_courses'] = []
            if section_id not in request.session['selected_courses']:
                request.session['selected_courses'].append(section_id)
                request.session.modified = True
            return redirect('create_schedule')

        # Handle schedule creation
        elif action == 'create_schedule':
            schedule_name = request.POST.get('schedule_name', 'My Schedule')
            section_ids = request.session.get('selected_courses', [])

            # Create a new schedule
            schedule = Schedule.objects.create(user=request.user, name=schedule_name)

            # Add selected sections to the schedule
            sections = Section.objects.filter(id__in=section_ids)
            schedule.sections.set(sections)

            # Clear the session-based list
            request.session['selected_courses'] = []

            return redirect('view_schedule', schedule_id=schedule.id)

    else:
        # Handle course filtering
        query = request.GET.get('query', '').strip()
        sections = Section.objects.all()

        if query:
            query_no_space = query.replace(' ', '')
            sections = sections.filter(
                Q(subject__icontains=query) |
                Q(course_number__icontains=query) |
                Q(course_code__icontains=query_no_space)
            )

        # Retrieve selected courses from the session
        selected_courses = Section.objects.filter(id__in=request.session.get('selected_courses', []))

        return render(request, 'base/create_schedule.html', {
            'sections': sections,
            'selected_courses': selected_courses,
            'query': query,
        })


@login_required
def calendarSync(request):
    # Get the user's latest schedule
    schedule = Schedule.objects.filter(user=request.user).last()
    if not schedule:
        return render(request, 'base/calendar_sync.html', {'message': 'No schedule found to sync.'})

    # Load Google Calendar API credentials
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

    # Export each section in the schedule to Google Calendar
    for section in schedule.sections.all():
        meeting_days = []
        if section.mo: meeting_days.append('MO')
        if section.tu: meeting_days.append('TU')
        if section.we: meeting_days.append('WE')
        if section.th: meeting_days.append('TH')
        if section.fr: meeting_days.append('FR')
        if section.sa: meeting_days.append('SA')
        if section.su: meeting_days.append('SU')

        event = {
            'summary': section.course.name,
            'description': f"CRN: {section.crn}, Instructor: {section.instructor}",
            'start': {'dateTime': f"{section.start_date}T{section.begins}", 'timeZone': 'America/New_York'},
            'end': {'dateTime': f"{section.start_date}T{section.ends}", 'timeZone': 'America/New_York'},
            'recurrence': [
                f"RRULE:FREQ=WEEKLY;BYDAY={','.join(meeting_days)};UNTIL={section.end_date.strftime('%Y%m%d')}T235959Z"
            ],
        }
        service.events().insert(calendarId='primary', body=event).execute()

    return render(request, 'base/calendar_sync.html', {'message': 'Schedule synced successfully with Google Calendar!'})

@login_required
def courseLoad(request):
    user = request.user
    try:
        survey = SchedulingSurvey.objects.get(user=user)
    except SchedulingSurvey.DoesNotExist:
        return render(request, 'base/no_survey.html')  # Ensure this template exists

    all_courses = Course.objects.all()
    suggested_courses = random.sample(list(all_courses), min(5, len(all_courses)))

    schedule = []
    for course in suggested_courses:
        sections = Section.objects.filter(course=course)
        if sections.exists():
            schedule.append(sections.first())

    return render(request, 'base/course_load.html', {  # Use the correct template path
        'survey': survey,
        'schedule': schedule,
    })
