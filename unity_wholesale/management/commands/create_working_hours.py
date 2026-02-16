import datetime
from django.core.management.base import BaseCommand

from app_modules.users.models import User, WorkingHours

class Command(BaseCommand):
    help = "Create default working hours for users who are not SUPER_ADMIN, ADMIN, or COMPANY_ADMIN."

    def handle(self, *args, **options):
        self.create_default_working_hours()

    def create_default_working_hours(self):
        excluded_roles = [User.SUPER_ADMIN, User.ADMIN, User.COMPANY_ADMIN, User.COMPANY_SUPER_ADMIN]
        users = User.objects.exclude(role__in=excluded_roles)

        for user in users:
            existing_hours = WorkingHours.objects.filter(user=user)
            if not existing_hours.exists():
                for week_day, day_name in WorkingHours.DAYS_OF_WEEK:
                    WorkingHours.objects.create(
                        user=user,
                        week_day=week_day,
                        day_status=True,  
                        start_time=datetime.time(9, 0), 
                        end_time=datetime.time(18, 0) 
                    )
                self.stdout.write(self.style.SUCCESS(f'Default working hours created for user: {user.full_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Working hours already exist for user: {user.full_name}'))
