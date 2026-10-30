"""Global test configuration.

Tests run against the local SQLite database and must never call the live Gmail
edge function.  Setting the mode here (before any app module is imported) keeps
the outbox fully exercised while delivery stays simulated.
"""

import os

os.environ["EMAIL_DELIVERY_MODE"] = "simulated"
