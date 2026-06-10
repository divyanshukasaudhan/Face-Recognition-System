# GuardianID — Face Recognition Attendance & Secure Entry (Django + OpenCV)

A ready-to-run Final Year Project:
- Face enrollment (capture from browser webcam)
- Face recognition for Entry/Exit
- Geo-location validation (campus radius)
- Attendance logs + dashboard + CSV export

## 1) Requirements
- Python 3.10+
- Webcam (laptop camera)
- Recommended (for face recognition): **opencv-contrib-python** (includes LBPH)

## 2) Setup (Quick Start)
```bash
cd guardianid
python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/linux:
# source .venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open: http://127.0.0.1:8000/

Login to admin: http://127.0.0.1:8000/admin/

## 3) Notes
- Default DB: SQLite (ready-to-run).
- For MySQL, see `guardianid/settings.py` section "MYSQL (OPTIONAL)".
- Campus location & radius can be set in **Settings > Campus Config** inside the web UI.

## 4) Folder Structure
- `guardianid/` Django project
- `core/` main app (students, face model, attendance, config)
- `templates/` Bootstrap UI templates
- `media/` stored face images + trained model files (auto-created)

## 5) Disclaimer
This is a student project template. Accuracy depends on lighting, camera quality, and enrollment samples.
