from django.db import models
from django.utils import timezone

class Student(models.Model):
    roll_no = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    department = models.CharField(max_length=120, blank=True)
    year = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.roll_no} - {self.name}"

class FaceSample(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="face_samples")
    image = models.ImageField(upload_to="faces/")
    created_at = models.DateTimeField(default=timezone.now)

class CampusConfig(models.Model):
    campus_lat = models.FloatField(default=0.0)
    campus_lng = models.FloatField(default=0.0)
    allowed_radius_m = models.IntegerField(default=200)  # meters
    allowed_start_time = models.TimeField(null=True, blank=True)
    allowed_end_time = models.TimeField(null=True, blank=True)

    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "Campus Configuration"

class AttendanceLog(models.Model):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ACTIONS = [(ENTRY, "Entry"), (EXIT, "Exit")]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_logs")
    date = models.DateField()
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(default=timezone.now)

    status = models.CharField(max_length=30, default="PRESENT")  # PRESENT / DENIED / UNKNOWN
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    distance_m = models.FloatField(null=True, blank=True)
    location_status = models.CharField(max_length=20, default="UNKNOWN")  # ALLOWED / DENIED / UNKNOWN
    message = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["date", "student"]),
            models.Index(fields=["date", "action"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.student.roll_no} {self.date} {self.action} {self.status}"
