from django import forms
from .models import Student, CampusConfig

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["roll_no", "name", "department", "year", "email", "phone", "is_active"]
        widgets = {
            "roll_no": forms.TextInput(attrs={"class":"form-control"}),
            "name": forms.TextInput(attrs={"class":"form-control"}),
            "department": forms.TextInput(attrs={"class":"form-control"}),
            "year": forms.TextInput(attrs={"class":"form-control"}),
            "email": forms.EmailInput(attrs={"class":"form-control"}),
            "phone": forms.TextInput(attrs={"class":"form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class":"form-check-input"}),
        }

class CampusConfigForm(forms.ModelForm):
    class Meta:
        model = CampusConfig
        fields = ["campus_lat", "campus_lng", "allowed_radius_m", "allowed_start_time", "allowed_end_time"]
        widgets = {
            "campus_lat": forms.NumberInput(attrs={"class":"form-control", "step":"any"}),
            "campus_lng": forms.NumberInput(attrs={"class":"form-control", "step":"any"}),
            "allowed_radius_m": forms.NumberInput(attrs={"class":"form-control"}),
            "allowed_start_time": forms.TimeInput(attrs={"class":"form-control", "type":"time"}),
            "allowed_end_time": forms.TimeInput(attrs={"class":"form-control", "type":"time"}),
        }
