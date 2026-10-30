"""Global test configuration.

Tests run against the local SQLite database and must never call the live Gmail
edge function.  Setting the mode here (before any app module is imported) keeps
the outbox fully exercised while delivery stays simulated.

``DATABASE_URL`` is pinned to the tracked SQLite file *before* ``app.config``
loads ``.env``, so a developer whose ``.env`` points at Supabase can still run
the suite without mutating production data.
"""

import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TEST_DB = os.path.join(_BACKEND_DIR, "data", "campusops.db").replace(os.sep, "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

os.environ["EMAIL_DELIVERY_MODE"] = "simulated"
