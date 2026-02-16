from django.urls import path
from app_modules.users.views import UserCreateView, UserDataTablesAjaxPagination, UserDeleteAjaxView, UserListView, UserUpdateView, ProfileUpdateView , RoleCreateView,UpdateWorkingHoursView,UserPasswordResetView

app_name = "users"

urlpatterns = [
    # url for user
    path("", UserListView.as_view(), name="user_list"),
    path("create/", UserCreateView.as_view(), name="user_create"),
    path("role-create/", RoleCreateView.as_view(), name="role_create"),
    path("<int:pk>/update/", UserUpdateView.as_view(), name="user_update"),
    path("user-delete-ajax/", UserDeleteAjaxView.as_view(), name="user_delete"),
    path('user-list-ajax/', UserDataTablesAjaxPagination.as_view(), name='user_list_ajax'),
    path("<int:pk>/profile/", ProfileUpdateView.as_view(), name="user_profile"),
    # path("<int:pk>/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path('update-working-hours/', UpdateWorkingHoursView.as_view(), name='update_working_hours'),
    path('user-reset-password/', UserPasswordResetView.as_view(), name='user_account_reset_password'),
]


handler404 = "app_modules.users.views.handler404"
handler403 = "app_modules.users.views.handler403"
