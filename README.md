# CareLink Hospital Appointment System

Flask REST API + HTML, CSS and JavaScript patient/doctor portal. Emergency-priority functionality is intentionally excluded.

## Run

Install Python 3.10+ and then run these commands in PowerShell:

```powershell
py -m pip install -r backend/requirements.txt
py backend/app.py
```

Open http://127.0.0.1:5000.

## Demo accounts

- Patients: `patient1@demo.com` through `patient10@demo.com`, password `patient123`
- Doctors: `doctor1@demo.com` through `doctor10@demo.com`, password `doctor123`

The API supports `GET /api/doctors`, `GET/POST /api/appointments`, and `PUT/DELETE /api/appointments/<id>`. Data is stored in `database/data.json`.

## Data-structure coverage

- A hash map (`symptom_department_map`) provides fast symptom-to-specialization lookups.
- Doctor recommendations are ranked with descending rating sort.
- Appointments use a normal FIFO queue position when multiple patients select the same doctor, date, and time.
- Doctor/patient records use unique IDs for direct lookup, while the symptom map models the symptom → department → doctor relationship.
