# CampusOps · Demo Access

Sign-in uses **Continue with Google**. There are no shared passwords and no
one-click persona buttons: the server looks up the role for the signed-in
Google email in that role's dedicated allowlist table.

| Portal | Google account | Role / sub-role |
| :--- | :--- | :--- |
| **Operations Admin** | `rajesekersudharsan@gmail.com` | `admin` / `system_admin` |
| **Technician** | `techtroveversion3@gmail.com` | `technician` / `maintenance_technician` |
| **Faculty** | `susen469@gmail.com` | `faculty` |
| **Student** | `192573020.simats@saveetha.com` | `student` |

* Only these four Google accounts can sign in; any other account gets `403`.
* Your role is applied by the server and cannot be chosen or changed from the
  browser.
* The system administrator can preview the other portals from inside the admin
  portal.
* Password sign-in is disabled by default. It can be re-enabled for a local
  fallback with `PASSWORD_LOGIN_ENABLED=true`, in which case the accounts use
  the password set by `provision_roles.py` (default `password123`).
