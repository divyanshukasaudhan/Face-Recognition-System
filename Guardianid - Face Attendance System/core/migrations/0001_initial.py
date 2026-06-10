# Generated manually for template project.
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CampusConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("campus_lat", models.FloatField(default=0.0)),
                ("campus_lng", models.FloatField(default=0.0)),
                ("allowed_radius_m", models.IntegerField(default=200)),
                ("allowed_start_time", models.TimeField(blank=True, null=True)),
                ("allowed_end_time", models.TimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("roll_no", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("department", models.CharField(blank=True, max_length=120)),
                ("year", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="FaceSample",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="faces/")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="face_samples", to="core.student")),
            ],
        ),
        migrations.CreateModel(
            name="AttendanceLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("action", models.CharField(choices=[("ENTRY", "Entry"), ("EXIT", "Exit")], max_length=10)),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("status", models.CharField(default="PRESENT", max_length=30)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                ("distance_m", models.FloatField(blank=True, null=True)),
                ("location_status", models.CharField(default="UNKNOWN", max_length=20)),
                ("message", models.CharField(blank=True, max_length=255)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_logs", to="core.student")),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="attendancelog",
            index=models.Index(fields=["date", "student"], name="core_attend_date_4a6c3f_idx"),
        ),
        migrations.AddIndex(
            model_name="attendancelog",
            index=models.Index(fields=["date", "action"], name="core_attend_date_9b0b6b_idx"),
        ),
    ]
