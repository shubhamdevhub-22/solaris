from django import forms
from app_modules.company.models import CompanyUsers
from app_modules.expanse_management.models import ExpanseBudget, ExpanseCategory, ExpanseManagement
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import pytz

class ExpanseManagementForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=ExpanseCategory.objects.none(),
        empty_label="Select Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ExpanseManagement
        fields = ("category", "expanse", "date", "note")
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ExpanseManagementForm, self).__init__(*args, **kwargs)
        
        if user:
            company = CompanyUsers.objects.get(user=user).company
            self.fields['category'].queryset = ExpanseCategory.objects.filter(company=company)
        
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.field.label

        self.fields["expanse"].required = True
        self.fields["note"].required = True
        self.fields["date"].required = True
        if not self.instance.pk and 'date' not in self.initial:
            kolkata_tz = pytz.timezone('Asia/Kolkata')
            now_in_kolkata = datetime.now(tz=kolkata_tz)
            # now_in_utc = now_in_kolkata.astimezone(pytz.utc)
            self.initial['date'] = now_in_kolkata

    def clean(self):
        cleaned_data = super().clean()
        expanse = cleaned_data.get("expanse")
        if expanse is None or expanse <= 0.00:
            raise ValidationError({'expanse': 'Expanse amount must be greater than 0.00.'})
        return cleaned_data