from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("", views.dashboard, name="dashboard"),
    path("students/", views.students_list, name="students_list"),
    path("students/add/", views.student_create, name="student_create"),
    path("students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),

    path("enroll/", views.enroll_page, name="enroll_page"),
    path("enroll/capture/", views.enroll_capture, name="enroll_capture"),
    path("train/", views.train_model, name="train_model"),

    path("attendance/", views.attendance_page, name="attendance_page"),
    path("attendance/mark/", views.attendance_mark, name="attendance_mark"),

    path("reports/", views.reports_page, name="reports_page"),
    path("reports/export/", views.export_csv, name="export_csv"),

    path("settings/campus/", views.campus_settings, name="campus_settings"),
]
