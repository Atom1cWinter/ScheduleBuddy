import csv
from django.core.management.base import BaseCommand
from base.models import Section, Course


class Command(BaseCommand):
    help = 'Load section data from sections.csv'

    def handle(self, *args, **kwargs):
        csv_file_path = 'base/sections.csv'  # Update this path if necessary

        def convert_time_format(time_str):
            """
            Converts time from '1300' format to '13:00' format.
            If the input is invalid or empty, returns None.
            """
            if not time_str or len(time_str) != 4 or not time_str.isdigit():
                return None
            return f"{time_str[:2]}:{time_str[2:]}"

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Get or create the course
                        course, _ = Course.objects.get_or_create(
                            code=row['SUBJECT'] + row['COURSE_NUMBER'],
                            defaults={
                                'name': row['COURSE_TITLE'],
                                'credits': int(row['CREDIT']),
                                'description': 'No description provided.',  # Default description
                            }
                        )

                        # Convert time fields
                        begins = convert_time_format(row['BEGINS'])
                        ends = convert_time_format(row['ENDS'])

                        # Create the section
                        Section.objects.update_or_create(
                            crn=row['CRN'],
                            defaults={
                                'course': course,
                                'term': row['TERM'],
                                'section_code': row['SECTION'],
                                'subject': row['SUBJECT'],
                                'course_number': row['COURSE_NUMBER'],
                                'course_code': row['SUBJECT'] + row['COURSE_NUMBER'],
                                'begins': begins,
                                'ends': ends,
                                'mo': row['MO'] == '1',
                                'tu': row['TU'] == '1',
                                'we': row['WE'] == '1',
                                'th': row['TH'] == '1',
                                'fr': row['FR'] == '1',
                                'sa': row['SA'] == '1',
                                'su': row['SU'] == '1',
                            }
                        )
                        self.stdout.write(self.style.SUCCESS(f"Processed section: {row['CRN']}"))
                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f"Missing field in row: {row}. Error: {e}"))
                    except ValueError as e:
                        self.stderr.write(self.style.ERROR(f"Invalid data in row: {row}. Error: {e}"))

            self.stdout.write(self.style.SUCCESS('Sections loaded successfully!'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {csv_file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))