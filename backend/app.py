from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import json
from datetime import datetime
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "database" / "data.json"
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)


def load_data():
    with open(DATA_FILE, encoding="utf-8") as file:
        return json.load(file)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def public_doctor(doctor):
    return {key: value for key, value in doctor.items() if key != "password"}


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    scope = payload.get("scope")
    data = load_data()
    collection = "doctors" if scope == "doctor" else "patients"
    user = next((item for item in data[collection] if item["email"] == email and item["password"] == password), None)
    if not user:
        return jsonify({"message": "Invalid email, password, or login type."}), 401
    safe_user = public_doctor(user) if scope == "doctor" else {k: v for k, v in user.items() if k != "password"}
    return jsonify({"user": safe_user, "scope": scope})


@app.get("/api/doctors")
def get_doctors():
    data = load_data()
    symptom = request.args.get("symptom", "").lower()
    city = request.args.get("city", "").lower()
    specialization = request.args.get("specialization", "").lower()
    mapping = data["symptom_department_map"]
    suggested = next((department for keyword, department in mapping.items() if keyword in symptom), "")
    doctors = data["doctors"]
    if suggested:
        doctors = [doctor for doctor in doctors if doctor["specialization"].lower() == suggested.lower()]
    if specialization:
        doctors = [doctor for doctor in doctors if doctor["specialization"].lower() == specialization]
    if city:
        doctors = [doctor for doctor in doctors if doctor["city"].lower() == city]
    doctors = sorted(doctors, key=lambda doctor: doctor["rating"], reverse=True)
    return jsonify({"suggested_specialization": suggested or None, "doctors": [public_doctor(d) for d in doctors]})


@app.get("/api/appointments")
def get_appointments():
    data = load_data()
    patient_id = request.args.get("patient_id")
    doctor_id = request.args.get("doctor_id")
    appointments = data["appointments"]
    if patient_id:
        appointments = [item for item in appointments if item["patient_id"] == patient_id]
    if doctor_id:
        appointments = [item for item in appointments if item["doctor_id"] == doctor_id]
    appointments = sorted(appointments, key=lambda item: (item["date"], item["time"]))
    return jsonify(appointments)


@app.post("/api/appointments")
def create_appointment():
    payload = request.get_json(silent=True) or {}
    needed = ["patient_id", "doctor_id", "date", "time"]
    if any(not payload.get(field) for field in needed):
        return jsonify({"message": "patient_id, doctor_id, date and time are required."}), 400
    data = load_data()
    patient = next((p for p in data["patients"] if p["id"] == payload["patient_id"]), None)
    doctor = next((d for d in data["doctors"] if d["id"] == payload["doctor_id"]), None)
    if not patient or not doctor:
        return jsonify({"message": "Patient or doctor not found."}), 404
    # FIFO queue number for each doctor's selected appointment slot.
    queue_position = 1 + sum(1 for item in data["appointments"] if item["doctor_id"] == doctor["id"] and item["date"] == payload["date"] and item["time"] == payload["time"])
    appointment = {
        "id": str(uuid4()), "patient_id": patient["id"], "patient_name": patient["name"],
        "doctor_id": doctor["id"], "doctor_name": doctor["name"], "specialization": doctor["specialization"],
        "hospital": doctor["hospital"], "date": payload["date"], "time": payload["time"],
        "symptom": payload.get("symptom", "Not specified"), "status": "Booked", "queue_position": queue_position,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    data["appointments"].append(appointment)
    save_data(data)
    return jsonify(appointment), 201


@app.put("/api/appointments/<appointment_id>")
def update_appointment(appointment_id):
    payload = request.get_json(silent=True) or {}
    data = load_data()
    appointment = next((a for a in data["appointments"] if a["id"] == appointment_id), None)
    if not appointment:
        return jsonify({"message": "Appointment not found."}), 404
    for field in ("date", "time", "status", "symptom"):
        if field in payload:
            appointment[field] = payload[field]
    save_data(data)
    return jsonify(appointment)


@app.delete("/api/appointments/<appointment_id>")
def delete_appointment(appointment_id):
    data = load_data()
    before = len(data["appointments"])
    data["appointments"] = [a for a in data["appointments"] if a["id"] != appointment_id]
    if len(data["appointments"]) == before:
        return jsonify({"message": "Appointment not found."}), 404
    save_data(data)
    return "", 204


if __name__ == "__main__":
    app.run(debug=True, port=5000)
