from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

app = FastAPI()

# Enable CORS so the React frontend can talk to the Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE (In-Memory for POC, easily switched to SQLite) ---
# We store these as lists. In a final version, these go in a real DB.
techs = [
    {"id": "1", "name": "Tech 1", "status": "Full-Time", "skills": ["Cardio", "Vascular", "Bubble Study", "Stress Echo"]},
    {"id": "2", "name": "Tech 2", "status": "Full-Time", "skills": ["Cardio", "Vascular"]},
    {"id": "3", "name": "Tech 3", "status": "Full-Time", "skills": ["Vascular Only"]},
    {"id": "4", "name": "Tech 4", "status": "Full-Time", "skills": ["Cardio Only"]},
    {"id": "5", "name": "Tech 5", "status": "Full-Time", "skills": ["Cardio", "Vascular", "Bubble Study"]},
    {"id": "26", "name": "Tech 26", "status": "PRN", "skills": ["Cardio", "Vascular"], "availability": "Mondays, Wednesdays"},
    {"id": "27", "name": "Tech 27", "status": "PRN", "skills": ["Vascular Only"], "availability": "Tuesdays, Thursdays"},
]

rooms = [
    {"id": "1", "name": "Room 1", "type": "General Echo", "equipment": ["Ultrasound Machine"]},
    {"id": "6", "name": "Room 6", "type": "Vascular Suite", "equipment": ["Ultrasound Machine", "Vascular Probe"]},
    {"id": "11", "name": "Room 11", "type": "Stress Lab A", "equipment": ["Ultrasound Machine", "Treadmill", "ECG"]},
    {"id": "14", "name": "Room 14", "type": "Specialized Echo", "equipment": ["High-End Machine", "Bubble Study Kit"]},
]

EXAM_REQUIREMENTS = {
    "Standard Echo": {"skill": "Cardio", "equipment": "Ultrasound Machine"},
    "Vascular Study": {"skill": "Vascular", "equipment": "Vascular Probe"},
    "Bubble Study": {"skill": "Bubble Study", "equipment": "Bubble Study Kit"},
    "Stress Echo": {"skill": "Stress Echo", "equipment": "Treadmill"},
}

# --- MODELS ---
class PatientRequest(BaseModel):
    name: str
    exam_type: str

class ScheduleRequest(BaseModel):
    day_name: str
    requests: List[PatientRequest]

# --- LOGIC ---
def is_tech_available(tech, day_of_week, time_slot):
    if tech["status"] == "Full-Time": return True
    avail = tech.get("availability", "").lower()
    day = day_of_week.lower()
    if day in avail or "any day" in avail: return True
    return False

@app.get("/techs")
def get_techs():
    return techs

@app.get("/rooms")
def get_rooms():
    return rooms

@app.post("/schedule")
def create_schedule(data: ScheduleRequest):
    room_busy = {}
    tech_busy = {}
    final_schedule = []
    start_time = datetime(2026, 10, 7, 8, 0)
    
    for req_item in data.requests:
        req = EXAM_REQUIREMENTS.get(req_item.exam_type)
        if not req:
            final_schedule.append({"error": f"Invalid exam {req_item.exam_type} for {req_item.name}"})
            continue
            
        assigned = False
        current_slot = start_time
        while current_slot.hour < 17:
            qualified_techs = [
                t for t in techs 
                if req["skill"] in t["skills"] 
                and is_tech_available(t, data.day_name, current_slot)
                and (t["name"], current_slot) not in tech_busy
            ]
            available_rooms = [
                r for r in rooms 
                if req["equipment"] in r["equipment"]
                and (r["name"], current_slot) not in room_busy
            ]
            
            if qualified_techs and available_rooms:
                tech = qualified_techs[0]
                room = available_rooms[0]
                room_busy[(room["name"], current_slot)] = True
                tech_busy[(tech["name"], current_slot)] = True
                final_schedule.append({
                    "patient": req_item.name,
                    "exam": req_item.exam_type,
                    "time": current_slot.strftime("%H:%M"),
                    "tech": tech["name"],
                    "room": room["name"]
                })
                assigned = True
                break
            current_slot += timedelta(minutes=60)
        
        if not assigned:
            final_schedule.append({"error": f"Could not schedule {req_item.name}"})
            
    return final_schedule

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
