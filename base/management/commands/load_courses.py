import os
import csv
from django.core.management.base import BaseCommand
from base.models import Course


class Command(BaseCommand):
    help = 'Load course data from CSV'

    def handle(self, *args, **kwargs):
        csv_file_path = 'base/courses.csv'  # Update this path if necessary

        # Check if the file exists
        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
            return

        def clean_credits(credits_str):
            """
            Cleans and converts the credits field to an integer.
            Removes non-numeric characters and handles invalid values.
            """
            try:
                # Remove non-numeric characters (e.g., parentheses)
                cleaned = ''.join(c for c in credits_str if c.isdigit())
                return int(cleaned) if cleaned else 0
            except ValueError:
                return 0  # Default to 0 if conversion fails

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Clean and convert the credits field
                        credits = clean_credits(row['credits'])

                        # Create or update the course
                        Course.objects.update_or_create(
                            code=row['code'],
                            defaults={
                                'name': row['name'],
                                'credits': credits,
                                'prerequisites': row.get('prerequisites', ''),
                                'corequisites': row.get('corequisites', ''),
                                'crosslisted_courses': row.get('crosslisted_courses', ''),
                                'description': row.get('description', ''),
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f"Processed course: {row['code']}"))
                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f"Missing field in row: {row}. Error: {e}"))
                    except ValueError as e:
                        self.stderr.write(self.style.ERROR(f"Invalid data in row: {row}. Error: {e}"))

            self.stdout.write(self.style.SUCCESS('Courses loaded successfully!'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

