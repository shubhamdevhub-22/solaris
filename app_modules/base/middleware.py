from app_modules.users.models import CustomErrorLogs, WorkingHours, User
from datetime import datetime, timedelta
from app_modules.utils.timezone import utc_to_localtime

from allauth.account.adapter import get_adapter
from django.contrib import messages


class CustomMiddleware:
    def __init__(self, get_response):
        """
        One-time configuration and initialisation.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Code to be executed for each request before the view (and later
        middleware) are called.
        """

        if request.user.is_authenticated and request.user.role in [User.SALES_REPRESENTATIVE, User.ACCOUNTANT]:
            week_day = datetime.today().weekday()
            current_time = datetime.today()
            local_time = utc_to_localtime("Asia/Kolkata", current_time.time()).time()

            working_hours = WorkingHours.objects.filter(user = request.user, week_day = week_day, day_status = True, start_time__lte = local_time, end_time__gte = local_time)

            if working_hours.count() == 0:
                adapter = get_adapter(request)
                messages.add_message(request, messages.ERROR, "You are not allowed to login !!!")
                adapter.logout(request)
                
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        """

        return None

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        log = CustomErrorLogs(url = request.build_absolute_uri(), logs=exception)
        log.save()

        return None

    def process_template_response(self, request, response):
        """
        Called just after the view has finished executing.
        """

        return response