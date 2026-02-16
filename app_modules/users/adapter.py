from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
import warnings
from django.shortcuts import resolve_url
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
User = get_user_model()

class AccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse
        """
        return False
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        if request.user.role in [User.SALES_REPRESENTATIVE]:
            url = "order:order_list"
        elif check_password('solaris123',request.user.password):
            # url = "account_reset_password"
            # url = f"/accounts/password/reset/key/{request.user.id}-set-password/"
            url = "account_set_password"
        else:
            assert request.user.is_authenticated
            url = getattr(settings, "LOGIN_REDIRECT_URLNAME", None)
            if url:
                warnings.warn(
                    "LOGIN_REDIRECT_URLNAME is deprecated, simply"
                    " use LOGIN_REDIRECT_URL with a URL name",
                    DeprecationWarning,
                )
            else:
                url = settings.LOGIN_REDIRECT_URL
        return resolve_url(url)
    
    