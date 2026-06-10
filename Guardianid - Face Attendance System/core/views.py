import csv
import os
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import StudentForm, CampusConfigForm
from .models import Student, FaceSample, AttendanceLog, CampusConfig
from .utils import decode_base64_image, train_lbph, predict_lbph, haversine_m

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username","").strip()
        password = request.POST.get("password","")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "auth/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    today = timezone.localdate()
    present_today = AttendanceLog.objects.filter(date=today, status="PRESENT", action="ENTRY").count()
    total_students = Student.objects.filter(is_active=True).count()
    absent_today = max(total_students - present_today, 0)

    latest_logs = AttendanceLog.objects.select_related("student").all()[:10]
    return render(request, "dashboard.html", {
        "present_today": present_today,
        "absent_today": absent_today,
        "total_students": total_students,
        "latest_logs": latest_logs,
        "today": today
    })

@login_required
def students_list(request):
    q = request.GET.get("q","").strip()
    qs = Student.objects.all().order_by("roll_no")
    if q:
        qs = qs.filter(roll_no__icontains=q) | qs.filter(name__icontains=q)
    return render(request, "students/list.html", {"students": qs, "q": q})

@login_required
def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added.")
            return redirect("students_list")
    else:
        form = StudentForm()
    return render(request, "students/form.html", {"form": form, "title":"Add Student"})

@login_required
def student_update(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated.")
            return redirect("students_list")
    else:
        form = StudentForm(instance=obj)
    return render(request, "students/form.html", {"form": form, "title":"Edit Student"})

@login_required
def student_delete(request, pk):
    obj = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Student deleted.")
        return redirect("students_list")
    return render(request, "students/delete.html", {"student": obj})

@login_required
def campus_settings(request):
    cfg = CampusConfig.objects.first()
    if not cfg:
        cfg = CampusConfig.objects.create(campus_lat=0.0, campus_lng=0.0, allowed_radius_m=200)

    if request.method == "POST":
        form = CampusConfigForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "Campus settings saved.")
            return redirect("campus_settings")
    else:
        form = CampusConfigForm(instance=cfg)
    return render(request, "settings/campus.html", {"form": form})

@login_required
def enroll_page(request):
    students = Student.objects.filter(is_active=True).order_by("roll_no")
    return render(request, "enroll/enroll.html", {"students": students})

@login_required
def enroll_capture(request):
    # AJAX: student_id + image (base64)
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    student_id = request.POST.get("student_id")
    img_data = request.POST.get("image")
    if not student_id or not img_data:
        return JsonResponse({"ok": False, "error": "Missing student_id or image"}, status=400)

    student = get_object_or_404(Student, pk=int(student_id))
    img = decode_base64_image(img_data)

    # Save raw image as sample
    # (We store the file so we can re-train model anytime)
    ts = timezone.now().strftime("%Y%m%d_%H%M%S_%f")
    rel_path = f"faces/{student.roll_no}_{ts}.jpg"
    abs_path = os.path.join(timezone.get_current_timezone_name() and "" or "", "")  # no-op
    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")  # not used

    # Django ImageField needs File object; simplest: write into MEDIA_ROOT and set name.
    from django.core.files.base import ContentFile
    import base64 as _b64

    # Re-encode to jpg bytes
    import cv2, numpy as np
    ok, buf = cv2.imencode(".jpg", img)
    if not ok:
        return JsonResponse({"ok": False, "error": "Could not encode image"}, status=500)
    content = ContentFile(buf.tobytes(), name=os.path.basename(rel_path))
    FaceSample.objects.create(student=student, image=content)
    return JsonResponse({"ok": True, "message": "Sample saved."})

@login_required
def train_model(request):
    # Collect samples and train LBPH model
    mapping = {}
    for s in Student.objects.filter(is_active=True):
        paths = []
        for fs in s.face_samples.all():
            if fs.image and fs.image.path and os.path.exists(fs.image.path):
                paths.append(fs.image.path)
        if paths:
            mapping[s.id] = paths

    ok, msg = train_lbph(mapping)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("enroll_page")

@login_required
def attendance_page(request):
    return render(request, "attendance/attendance.html")

def _get_cfg():
    cfg = CampusConfig.objects.first()
    if not cfg:
        cfg = CampusConfig.objects.create(campus_lat=0.0, campus_lng=0.0, allowed_radius_m=200)
    return cfg

@login_required
def attendance_mark(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error":"POST only"}, status=405)

    action = request.POST.get("action", "ENTRY")
    img_data = request.POST.get("image")
    lat = request.POST.get("lat")
    lng = request.POST.get("lng")

    if not img_data:
        return JsonResponse({"ok": False, "error":"Missing image"}, status=400)

    img = decode_base64_image(img_data)
    pred = predict_lbph(img)

    cfg = _get_cfg()
    dist = None
    loc_status = "UNKNOWN"
    msg_loc = ""

    try:
        if lat is not None and lng is not None and lat != "" and lng != "" and cfg.campus_lat != 0.0 and cfg.campus_lng != 0.0:
            latf = float(lat); lngf = float(lng)
            dist = haversine_m(latf, lngf, float(cfg.campus_lat), float(cfg.campus_lng))
            if dist <= float(cfg.allowed_radius_m):
                loc_status = "ALLOWED"
            else:
                loc_status = "DENIED"
                msg_loc = f"Outside campus radius ({int(dist)}m)."
        else:
            msg_loc = "Location not configured or not provided."
    except Exception:
        msg_loc = "Location check failed."

    # Time window check (optional)
    now_local = timezone.localtime()
    if cfg.allowed_start_time and cfg.allowed_end_time:
        if not (cfg.allowed_start_time <= now_local.time() <= cfg.allowed_end_time):
            loc_status = "DENIED"
            msg_loc = "Outside allowed attendance time window."

    today = timezone.localdate()

    if pred.student_id is None:
        AttendanceLog.objects.create(
            student=Student.objects.filter(is_active=True).first() or Student.objects.create(roll_no="UNKNOWN", name="Unknown"),
            date=today, action=action,
            status="UNKNOWN",
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            distance_m=dist,
            location_status=loc_status,
            message=pred.message
        )
        return JsonResponse({"ok": False, "status":"UNKNOWN", "message": pred.message})

    student = get_object_or_404(Student, pk=pred.student_id)

    if loc_status == "DENIED":
        AttendanceLog.objects.create(
            student=student, date=today, action=action,
            status="DENIED",
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            distance_m=dist,
            location_status=loc_status,
            message=msg_loc or "Location denied."
        )
        return JsonResponse({"ok": False, "status":"DENIED", "student": student.name, "message": msg_loc or "Location denied."})

    # Prevent duplicate Entry (same day)
    if action == "ENTRY":
        already = AttendanceLog.objects.filter(student=student, date=today, action="ENTRY", status="PRESENT").exists()
        if already:
            return JsonResponse({"ok": False, "status":"DUPLICATE", "student": student.name, "message":"Entry already marked today."})

    AttendanceLog.objects.create(
        student=student, date=today, action=action,
        status="PRESENT",
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
        distance_m=dist,
        location_status=loc_status,
        message=f"{action} marked successfully. (conf={pred.confidence:.1f})"
    )
    return JsonResponse({"ok": True, "status":"PRESENT", "student": student.name, "message": f"{action} marked successfully."})

@login_required
def reports_page(request):
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")
    roll = request.GET.get("roll","").strip()

    qs = AttendanceLog.objects.select_related("student").all()
    if from_date:
        qs = qs.filter(date__gte=from_date)
    if to_date:
        qs = qs.filter(date__lte=to_date)
    if roll:
        qs = qs.filter(student__roll_no__icontains=roll)

    logs = qs[:300]  # keep UI fast
    return render(request, "reports/reports.html", {"logs": logs, "from": from_date, "to": to_date, "roll": roll})

@login_required
def export_csv(request):
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    qs = AttendanceLog.objects.select_related("student").all()
    if from_date:
        qs = qs.filter(date__gte=from_date)
    if to_date:
        qs = qs.filter(date__lte=to_date)

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="guardianid_attendance.csv"'
    writer = csv.writer(resp)
    writer.writerow(["Roll No", "Name", "Date", "Action", "Status", "Time", "Location Status", "Distance(m)", "Message"])
    for l in qs.order_by("-timestamp")[:5000]:
        writer.writerow([
            l.student.roll_no, l.student.name,
            l.date, l.action, l.status,
            timezone.localtime(l.timestamp).strftime("%H:%M:%S"),
            l.location_status, "" if l.distance_m is None else int(l.distance_m),
            l.message
        ])
    return resp
