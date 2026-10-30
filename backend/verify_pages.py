import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"

def test_endpoint(endpoint, method="GET", data=None, token=None):
    url = f"{base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# 1. Login as Admin
print("[Check 1] Authenticating Admin...")
status, auth_data = test_endpoint("/auth/login", method="POST", data={"email": "admin@campusops.edu", "password": "password123"})
assert status == 200, f"Admin login failed: {auth_data}"
admin_token = auth_data["access_token"]
print(" -> OK: Admin Token issued")

# 2. Check Admin Dashboard & Analytics
print("[Check 2] Verifying Admin Dashboard & Dedicated Analytics...")
s, d = test_endpoint("/dashboard/admin", token=admin_token)
assert s == 200, f"Admin dashboard failed: {d}"
assert "kpi" in d and "recent_incidents" in d
s2, d2 = test_endpoint("/analytics", token=admin_token)
assert s2 == 200, f"Analytics endpoint failed: {d2}"
assert "incidents_by_category" in d2 and "sla_monthly_trend" in d2
print(" -> OK: Admin Dashboard & Analytics operational")

# 3. Check Incidents, Work Orders, Rooms, Bookings, Inventory, Approvals, Staff
print("[Check 3] Verifying Core Tables Data Feeds...")
endpoints = [
    ("/incidents?limit=20", "Incidents"),
    ("/reports", "Reports"),
    ("/work-orders?limit=20", "Work Orders"),
    ("/rooms?limit=20", "Rooms"),
    ("/bookings?limit=20", "Bookings"),
    ("/inventory?limit=20", "Inventory"),
    ("/approvals", "Approvals"),
    ("/staff", "Staff Matrix"),
    ("/intelligence/predictive-alerts", "Predictive Alerts")
]
for ep, name in endpoints:
    st, res = test_endpoint(ep, token=admin_token)
    assert st == 200, f"{name} failed with {st}"
    print(f" -> OK: {name} count={len(res)}")

# 4. Check Technician Dashboard
print("[Check 4] Authenticating Technician...")
st, tech_auth = test_endpoint("/auth/login", method="POST", data={"email": "tech@campusops.edu", "password": "password123"})
assert st == 200
tech_token = tech_auth["access_token"]
st, tech_dash = test_endpoint("/dashboard/technician", token=tech_token)
assert st == 200 and "my_tasks" in tech_dash
print(f" -> OK: Technician dashboard operational (My Tasks: {len(tech_dash['my_tasks'])})")

# 5. Check Faculty Dashboard
print("[Check 5] Authenticating Faculty...")
st, fac_auth = test_endpoint("/auth/login", method="POST", data={"email": "faculty@campusops.edu", "password": "password123"})
assert st == 200
fac_token = fac_auth["access_token"]
st, fac_dash = test_endpoint("/dashboard/faculty", token=fac_token)
assert st == 200 and "timetable" in fac_dash
print(f" -> OK: Faculty dashboard operational (Timetable: {len(fac_dash['timetable'])})")

# 6. Check Student Dashboard
print("[Check 6] Authenticating Student...")
st, stu_auth = test_endpoint("/auth/login", method="POST", data={"email": "student@campusops.edu", "password": "password123"})
assert st == 200
stu_token = stu_auth["access_token"]
st, stu_dash = test_endpoint("/dashboard/student", token=stu_token)
assert st == 200 and "my_requests" in stu_dash
print(f" -> OK: Student dashboard operational (My Requests: {len(stu_dash['my_requests'])})")

print("\n==================================================")
print("ALL BACKEND & PORTAL DATA PATHS VERIFIED CLEANLY!")
print("==================================================")

