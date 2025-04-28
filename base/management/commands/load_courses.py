import csv
from django.core.management.base import BaseCommand
from base.models import Course

class Command(BaseCommand):
    help = 'Load course data from CSV'

    def handle(self, *args, **kwargs):
        with open('path/to/your/courses.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Course.objects.update_or_create(
                    code=row['code'],
                    defaults={
                        'name': row['name'],
                        'credits': int(row['credits']),
                        'prerequisites': row.get('prerequisites', ''),
                        'corequisites': row.get('corequisites', ''),
                        'crosslisted_courses': row.get('crosslisted_courses', ''),
                        'description': row.get('description', ''),
                    }
                )
            self.stdout.write(self.style.SUCCESS('Courses loaded successfully!'))

