"""Layer: adapters.outbound.
Role: System clock, UTC, rounded to the second.
Depends on: the standard library.
"""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)
