import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from app_modules.base.models import BaseModel
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, **extra_fields):
        if not email:
            raise ValueError("User must have an email")

        user = self.model(email=self.normalize_email(email))
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("User must have an email")

        if not username:
            raise ValueError("User must have an username")

        if not password:
            raise ValueError("User must have a password")

        print("extra_fields.get(role) ", extra_fields.get("role"))

        user = self.model(email=self.normalize_email(email))
        user.username = username
        user.set_password(password)
        user.is_superuser = True
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.role = extra_fields.get("role")
        user.save(using=self._db)
        return user

# Create your models here.
class User(AbstractUser, BaseModel):
    
    SUPER_ADMIN = "super admin" #groumps.object.get(name=name).value_list("name"), 
    ADMIN = "admin"
    COMPANY_ADMIN = "company admin"
    COMPANY_SUPER_ADMIN = "company super admin"
    SALES_REPRESENTATIVE = "sales representative"
    DRIVER = "driver"
    ACCOUNTANT = "accountant"

    USER_ROLE = (
        (SUPER_ADMIN, "Super Admin"),
        # (ADMIN, "Admin"),
        (COMPANY_ADMIN, "Company Admin"),
        (COMPANY_SUPER_ADMIN, "Company Super Admin"),
        (SALES_REPRESENTATIVE, "Sales Representative"),
        (DRIVER, "Driver"),
        (ACCOUNTANT, "Accountant"),
    )
    email = models.EmailField(_('Email'),)
    full_name = models.CharField(_('Full Name'), max_length=50)
    phone = models.CharField(_('Phone'), max_length=20, null=True, blank=True)
    image = models.FileField(upload_to='user-profile', null=True)
    role = models.CharField(_('Role'), choices=USER_ROLE, max_length=20, default=ADMIN, null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return self.full_name
    

    @property
    def company(self):    # sourcery skip: assign-if-exp, reintroduce-else
        company_user = self.company_users.first()
        if company_user:
            return company_user.company.company_name
        return None
    
    @property
    def get_company_id(self):    # sourcery skip: assign-if-exp, reintroduce-else
        company_user = self.company_users.first()
        if company_user:
            return company_user.company.id
        return None
    
class DriverManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.DRIVER)
    

class Driver(User):
    role = User.DRIVER
    objects = DriverManager()
    
    class Meta:
        proxy = True


class SalesRepManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.SALES_REPRESENTATIVE)
    

class SalesRep(User):
    role = User.SALES_REPRESENTATIVE
    objects = SalesRepManager()
    
    class Meta:
        proxy = True

class CustomErrorLogs(BaseModel):
    url = models.CharField(("URL"), max_length=1000)
    logs = models.TextField(("Logs"))

    def __str__(self):
        return self.url
class WorkingHours(models.Model):
    DAYS_OF_WEEK = (
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="working_hours"
    )
    week_day = models.CharField(max_length=1, choices=DAYS_OF_WEEK)
    day_status = models.BooleanField(default=True)
    start_time = models.TimeField(default=datetime.time(9, 0))
    end_time = models.TimeField(default=datetime.time(18, 0))

    def __str__(self):
        return f"{self.user.full_name ,self.start_time,self.end_time}"
    
    @property
    def day_name(self):
        return dict(self.DAYS_OF_WEEK).get(self.week_day, 'Unknown')