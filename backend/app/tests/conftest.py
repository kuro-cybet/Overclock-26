"""Global test configuration.

Tests run against an isolated copy of the SQLite database in a temporary directory
and must never mutate the tracked `backend/data/campusops.db` or call live edge functions.

``DATABASE_URL`` is pinned to the isolated test copy *before* ``app.config`` loads ``.env``,
so a developer whose ``.env`` points at Supabase can still run the suite without mutating production data.
Password login is enabled in the test suite so existing API contracts can be exercised against seeded accounts.
"""

import os
import shutil
import tempfile
import atexit

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ORIGINAL_DB = os.path.join(_BACKEND_DIR, "data", "campusops.db").replace(os.sep, "/")

# Create an isolated temporary test database copy so tracked campusops.db is never mutated
_TEMP_DIR = tempfile.mkdtemp(prefix="campusops_test_")
_TEST_DB = os.path.join(_TEMP_DIR, "test_campusops.db").replace(os.sep, "/")

if os.path.exists(_ORIGINAL_DB):
    shutil.copy2(_ORIGINAL_DB, _TEST_DB)

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["PASSWORD_LOGIN_ENABLED"] = "true"
os.environ["EMAIL_DELIVERY_MODE"] = "simulated"

def _cleanup_temp_db():
    try:
        shutil.rmtree(_TEMP_DIR, ignore_errors=True)
    except Exception:
        pass

atexit.register(_cleanup_temp_db)
