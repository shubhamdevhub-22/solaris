from django.core.management import BaseCommand, call_command
from django.contrib.auth import get_user_model
User = get_user_model()

class Command(BaseCommand):
    help = "Update Vendor information."

    def handle(self, *args, **options):
        self.save_client_full_name()

    def save_client_full_name(self):
        users = User.objects.all()
        for user in users:
            if not user.full_name:
                user.full_name = user.email.split("@")[0]
                user.save()
