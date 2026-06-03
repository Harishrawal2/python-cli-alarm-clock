from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alarm:
    id: int
    alarm_time: datetime
    label: str
    note: str = ""
    repeat_type: str = "once"
    weekdays: tuple[int, ...] = ()
    skip_weekdays: tuple[int, ...] = ()
    ring_count: int = 5
    ring_duration_seconds: int = 60
    sound_style: str = "normal"
    active: bool = True
    enabled: bool = True
    schedule_hour: int | None = None
    schedule_minute: int | None = None
