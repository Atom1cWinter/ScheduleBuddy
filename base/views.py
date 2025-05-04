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
from .utils import sort_sections_by_survey  # Ensure this utility function exists
import random
import datetime

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------

def filter_sections_by_survey(survey, sections):
    """Filter sections based on survey preferences."""
    # Exclude night classes if the user prefers not to take them
    if not survey.night_classes_ok:
        sections = sections.filter(begins__lt="18:00:00")

    # Filter by preferred time distribution
    if survey.time_distribution == "morning":
        sections = sections.filter(begins__lt="12:00:00")
    elif survey.time_distribution == "afternoon":
        sections = sections.filter(begins__gte="12:00:00", begins__lt="16:00:00")
    elif survey.time_distribution == "evening":
        sections = sections.filter(begins__gte="16:00:00")

    # Filter by preferred meeting days
    preferred_days = {
        'MWF': ['mo', 'we', 'fr'],
        'TTH': ['tu', 'th'],
        'Spread': ['mo', 'tu', 'we', 'th', 'fr']
    }.get(survey.preferred_distribution, [])

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

    return sections.order_by('begins')


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
            score -= 5

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

# -------------------------------------------------
# Views: Home and Authentication
# -------------------------------------------------

def home(request):
    return render(request, 'base/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'base/register.html', {'form': form})


@login_required
def profile_view(request):
    schedules = Schedule.objects.filter(user=request.user)
    last_schedule = schedules.last()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'base/profile.html', {
        'schedules': schedules,
        'last_schedule': last_schedule,
        'form': form,
    })

# -------------------------------------------------
# Views: Survey and Recommendations
# -------------------------------------------------

def survey_view(request):
    if request.method == 'POST':
        form = SchedulingSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.save()

            profile = request.user.profile
            profile.survey = survey
            profile.save()

            return redirect('survey_thankyou')
    else:
        profile = request.user.profile
        form = SchedulingSurveyForm(instance=profile.survey if profile.survey else None)

    return render(request, 'base/survey.html', {'form': form})


@login_required
def recommend_sections(request):
    survey = request.user.profile.survey
    if not survey:
        return render(request, 'base/recommended_section.html', {'error': 'No survey found. Please complete the survey first.'})

    course_code = request.GET.get('course_code', '').strip()
    if not course_code:
        return render(request, 'base/recommended_section.html', {'error': 'No course code provided.'})

    sections = Section.objects.filter(course_code__iexact=course_code)
    if not sections.exists():
        return render(request, 'base/recommended_section.html', {'error': f'No sections found for course code: {course_code}'})

    sorted_sections = sort_sections_by_survey(survey, sections)

    return render(request, 'base/recommended_section.html', {
        'course_code': course_code,
        'sections': sorted_sections,
    })


@login_required
def recommend_section(request, course_id):
    """Recommend a specific section for a given course."""
    survey = request.user.profile.survey
    if not survey:
        return render(request, 'base/recommended_section.html', {'error': 'No survey found. Please complete the survey first.'})

    # Get the course and its sections
    course = get_object_or_404(Course, id=course_id)
    sections = Section.objects.filter(course=course)

    if not sections.exists():
        return render(request, 'base/recommended_section.html', {'error': f'No sections found for course: {course.name}'})

    # Sort sections based on survey preferences
    sorted_sections = sort_sections_by_survey(survey, sections)

    return render(request, 'base/recommended_section.html', {
        'course': course,
        'sections': sorted_sections,
    })


def thank_you(request):
    """Render a thank-you page after completing the survey."""
    return render(request, 'base/thank_you.html')

# -------------------------------------------------
# Views: Schedule Management
# -------------------------------------------------

@login_required
def create_schedule(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_course':
            section_id = request.POST.get('section_id')
            if 'selected_courses' not in request.session:
                request.session['selected_courses'] = []
            if section_id not in request.session['selected_courses']:
                request.session['selected_courses'].append(section_id)
                request.session.modified = True
            return redirect('create_schedule')

        elif action == 'create_schedule':
            schedule_name = request.POST.get('schedule_name', 'My Schedule')
            section_ids = request.session.get('selected_courses', [])

            schedule = Schedule.objects.create(user=request.user, name=schedule_name)
            sections = Section.objects.filter(id__in=section_ids)
            schedule.sections.set(sections)

            request.session['selected_courses'] = []
            return redirect('view_schedule', schedule_id=schedule.id)

    else:
        query = request.GET.get('query', '').strip()
        sections = Section.objects.all()

        if query:
            query_no_space = query.replace(' ', '')
            sections = sections.filter(
                Q(subject__icontains=query) |
                Q(course_number__icontains=query) |
                Q(course_code__icontains=query_no_space)
            )

        selected_courses = Section.objects.filter(id__in=request.session.get('selected_courses', []))

        return render(request, 'base/create_schedule.html', {
            'sections': sections,
            'selected_courses': selected_courses,
            'query': query,
        })


@login_required
def export_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    export_schedule_to_google_calendar(schedule)
    return JsonResponse({'message': 'Schedule exported to Google Calendar successfully!'})


@login_required
def view_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    return render(request, 'base/view_schedule.html', {'schedule': schedule})


@login_required
def add_to_schedule(request):
    """Add a section to the user's schedule."""
    if request.method == 'POST':
        section_id = request.POST.get('section_id')
        schedule_id = request.POST.get('schedule_id')

        if not section_id or not schedule_id:
            return JsonResponse({'error': 'Section ID and Schedule ID are required.'}, status=400)

        try:
            schedule = Schedule.objects.get(id=schedule_id, user=request.user)
            section = Section.objects.get(id=section_id)
            schedule.sections.add(section)
            return JsonResponse({'message': 'Section added to schedule successfully!'})
        except Schedule.DoesNotExist:
            return JsonResponse({'error': 'Schedule not found.'}, status=404)
        except Section.DoesNotExist:
            return JsonResponse({'error': 'Section not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

# -------------------------------------------------
# Views: Miscellaneous
# -------------------------------------------------

@login_required
def courseLoad(request):
    user = request.user
    try:
        survey = SchedulingSurvey.objects.get(user=user)
    except SchedulingSurvey.DoesNotExist:
        return render(request, 'base/no_survey.html')

    all_courses = Course.objects.all()
    suggested_courses = random.sample(list(all_courses), min(5, len(all_courses)))

    schedule = []
    for course in suggested_courses:
        sections = Section.objects.filter(course=course)
        if sections.exists():
            schedule.append(sections.first())

    return render(request, 'base/course_load.html', {
        'survey': survey,
        'schedule': schedule,
    })


def filter_courses(request):
    """Filter courses based on a query parameter."""
    query = request.GET.get('query', '').strip()
    if query:
        courses = Course.objects.filter(name__icontains=query)
    else:
        courses = Course.objects.all()

    return render(request, 'base/course_list.html', {'courses': courses})


@login_required
def add_course(request):
    """Add a new course to the system."""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added successfully!')
            return redirect('course_list')  # Redirect to the course list page
    else:
        form = CourseForm()

    return render(request, 'base/add_course.html', {'form': form})


def get_courses(request, ids):
    """Retrieve courses based on a list of IDs."""
    course_ids = ids.split(',')
    courses = Course.objects.filter(id__in=course_ids).values('id', 'code', 'name', 'credits', 'description')
    return JsonResponse(list(courses), safe=False)


@login_required
def course_list(request):
    """Display a list of all courses."""
    courses = Course.objects.all()
    return render(request, 'base/course_list.html', {'courses': courses})


@login_required
def calendarSync(request):
    """Sync the user's schedule with Google Calendar."""
    try:
        # Load Google API credentials
        creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
        service = build('calendar', 'v3', credentials=creds)

        # Example: Add a test event to the user's Google Calendar
        event = {
            'summary': 'Test Event',
            'start': {'dateTime': '2025-05-05T10:00:00-07:00', 'timeZone': 'America/Los_Angeles'},
            'end': {'dateTime': '2025-05-05T12:00:00-07:00', 'timeZone': 'America/Los_Angeles'},
        }
        service.events().insert(calendarId='primary', body=event).execute()

        return JsonResponse({'message': 'Calendar synced successfully!'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


