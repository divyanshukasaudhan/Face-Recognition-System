from django.contrib import admin
from .models import Student, FaceSample, AttendanceLog, CampusConfig

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_no", "name", "department", "year", "is_active", "created_at")
    search_fields = ("roll_no", "name", "department")
    list_filter = ("department", "year", "is_active")

@admin.register(FaceSample)
class FaceSampleAdmin(admin.ModelAdmin):
    list_display = ("student", "created_at")

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "action", "status", "location_status", "distance_m", "timestamp")
    search_fields = ("student__roll_no", "student__name")
    list_filter = ("date", "action", "status", "location_status")

@admin.register(CampusConfig)
class CampusConfigAdmin(admin.ModelAdmin):
    list_display = ("campus_lat", "campus_lng", "allowed_radius_m", "allowed_start_time", "allowed_end_time", "updated_at")
