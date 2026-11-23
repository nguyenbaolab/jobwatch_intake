"""Lớp: adapters.outbound.
Vai trò: Đồng hồ hệ thống, UTC, làm tròn tới giây.
Phụ thuộc: thư viện chuẩn.
"""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)
