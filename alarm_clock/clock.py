from datetime import datetime, timedelta
import re
import time

from alarm_clock.constants import (
    ALARM_RING_SECONDS,
    DEFAULT_SNOOZE_MINUTES,
    MAX_RING_COUNT,
    MAX_RING_DURATION_SECONDS,
    MAX_SNOOZE_MINUTES,
    MIN_RING_DURATION_SECONDS,
    MIN_SNOOZE_MINUTES,
)
from alarm_clock.models import Alarm
from alarm_clock.sound import AlarmSoundPlayer
from alarm_clock.weekdays import format_weekdays


class AlarmClock:
    def __init__(self, sound_player: AlarmSoundPlayer | None = None):
        self.alarms: list[Alarm] = []
        self.next_id = 1
        self.running = True
        self.sound_player = sound_player or AlarmSoundPlayer()

    def add_alarm(
        self,
        time_text: str,
        label: str,
        date_text: str = "",
        repeat_type: str = "once",
        weekdays: tuple[int, ...] = (),
        skip_weekdays: tuple[int, ...] = (),
        ring_count: int = 5,
        sound_style: str = "normal",
        ring_duration_seconds: int = ALARM_RING_SECONDS,
        note: str = "",
    ) -> Alarm:
        hour, minute = self._parse_clock_time(time_text)
        self._validate_repeat_type(repeat_type)
        self._validate_repeat_days(repeat_type, weekdays, skip_weekdays)
        self._validate_ring_count(ring_count)
        self._validate_ring_duration(ring_duration_seconds)
        alarm_time = self._parse_alarm_time(
            hour,
            minute,
            date_text,
            repeat_type,
            weekdays,
            skip_weekdays,
        )

        alarm = Alarm(
            id=self.next_id,
            alarm_time=alarm_time,
            label=label or "Alarm",
            note=note,
            repeat_type=repeat_type,
            weekdays=weekdays,
            skip_weekdays=skip_weekdays,
            ring_count=ring_count,
            ring_duration_seconds=ring_duration_seconds,
            sound_style=sound_style,
            schedule_hour=hour,
            schedule_minute=minute,
        )

        self.alarms.append(alarm)
        self.next_id += 1
        return alarm

    def edit_alarm(
        self,
        alarm_id: int,
        time_text: str,
        label: str,
        note: str,
        date_text: str,
        repeat_type: str,
        weekdays: tuple[int, ...],
        skip_weekdays: tuple[int, ...],
        ring_count: int,
        ring_duration_seconds: int,
        sound_style: str,
    ) -> Alarm | None:
        alarm = self.get_alarm(alarm_id)
        if not alarm:
            return None

        hour, minute = self._parse_clock_time(time_text)
        self._validate_repeat_type(repeat_type)
        self._validate_repeat_days(repeat_type, weekdays, skip_weekdays)
        self._validate_ring_count(ring_count)
        self._validate_ring_duration(ring_duration_seconds)
        alarm_time = self._parse_alarm_time(
            hour,
            minute,
            date_text,
            repeat_type,
            weekdays,
            skip_weekdays,
        )

        alarm.alarm_time = alarm_time
        alarm.label = label or "Alarm"
        alarm.note = note
        alarm.repeat_type = repeat_type
        alarm.weekdays = weekdays
        alarm.skip_weekdays = skip_weekdays
        alarm.ring_count = ring_count
        alarm.ring_duration_seconds = ring_duration_seconds
        alarm.sound_style = sound_style
        alarm.schedule_hour = hour
        alarm.schedule_minute = minute
        return alarm

    def active_alarms(self) -> list[Alarm]:
        return [alarm for alarm in self.alarms if alarm.active and alarm.enabled]

    def alarms_for_display(self) -> list[Alarm]:
        return sorted(
            (alarm for alarm in self.alarms if alarm.active),
            key=lambda alarm: (alarm.alarm_time, alarm.id),
        )

    def upcoming_alarms(self, limit: int = 5) -> list[Alarm]:
        if limit < 1:
            raise ValueError("Upcoming alarm count must be at least 1.")

        return self.alarms_for_display()[:limit]

    def get_alarm(self, alarm_id: int) -> Alarm | None:
        for alarm in self.alarms:
            if alarm.id == alarm_id and alarm.active:
                return alarm
        return None

    def next_alarm(self) -> Alarm | None:
        active_alarms = self.active_alarms()
        if not active_alarms:
            return None

        return min(active_alarms, key=lambda alarm: (alarm.alarm_time, alarm.id))

    def delete_alarm(self, alarm_id: int) -> bool:
        for alarm in self.alarms:
            if alarm.id == alarm_id and alarm.active:
                alarm.active = False
                return True
        return False

    def set_alarm_enabled(self, alarm_id: int, enabled: bool) -> bool:
        for alarm in self.alarms:
            if alarm.id == alarm_id and alarm.active:
                alarm.enabled = enabled
                return True
        return False

    def toggle_alarm_enabled(self, alarm_id: int) -> Alarm | None:
        for alarm in self.alarms:
            if alarm.id == alarm_id and alarm.active:
                alarm.enabled = not alarm.enabled
                return alarm
        return None

    def check_due_alarms(self):
        now = datetime.now()

        for alarm in self.alarms:
            if alarm.active and alarm.enabled and now >= alarm.alarm_time:
                action, snooze_minutes = self._ring_alarm(alarm)

                if action == "snoozed":
                    alarm.alarm_time = datetime.now() + timedelta(
                        minutes=snooze_minutes or DEFAULT_SNOOZE_MINUTES,
                    )
                elif alarm.repeat_type == "once":
                    alarm.active = False
                else:
                    alarm.alarm_time = self._next_recurring_time(
                        alarm,
                        datetime.now(),
                    )

    def stop(self):
        self.running = False

    def format_repeat(self, alarm: Alarm) -> str:
        if alarm.repeat_type == "once":
            return "one-time"

        if alarm.repeat_type == "daily" and alarm.skip_weekdays:
            return f"daily except {format_weekdays(alarm.skip_weekdays)}"

        if alarm.repeat_type == "daily":
            return "daily"

        return f"weekly on {format_weekdays(alarm.weekdays)}"

    def format_status(self, alarm: Alarm) -> str:
        if not alarm.active:
            return "deleted"

        if alarm.enabled:
            return "active"

        return "disabled"

    def format_alarm_time(self, alarm: Alarm) -> str:
        return alarm.alarm_time.strftime("%Y-%m-%d %H:%M")

    def format_alarm_time_with_ampm(self, alarm: Alarm) -> str:
        return alarm.alarm_time.strftime("%Y-%m-%d %H:%M (%I:%M %p)")

    def format_next_alarm_preview(self, alarm: Alarm) -> str:
        today = datetime.now().date()
        alarm_date = alarm.alarm_time.date()

        if alarm_date == today:
            day_text = "Today"
        elif alarm_date == today + timedelta(days=1):
            day_text = "Tomorrow"
        else:
            day_text = alarm.alarm_time.strftime("%Y-%m-%d")

        return f"{day_text} {alarm.alarm_time.strftime('%I:%M %p')} - {alarm.label}"

    def _parse_alarm_time(
        self,
        hour: int,
        minute: int,
        date_text: str,
        repeat_type: str,
        weekdays: tuple[int, ...],
        skip_weekdays: tuple[int, ...],
    ) -> datetime:
        now = datetime.now()

        if repeat_type in ("daily", "weekly"):
            alarm = Alarm(
                id=0,
                alarm_time=now,
                label="",
                repeat_type=repeat_type,
                weekdays=weekdays,
                skip_weekdays=skip_weekdays,
                schedule_hour=hour,
                schedule_minute=minute,
            )
            return self._next_recurring_time(alarm, now, hour, minute)

        if date_text:
            try:
                alarm_date = datetime.strptime(date_text, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")

            alarm_time = alarm_date.replace(hour=hour, minute=minute)
        else:
            alarm_time = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )

        if alarm_time <= now:
            raise ValueError(
                "That date and time has already passed. "
                "Please enter a future date/time."
            )

        return alarm_time

    def _parse_clock_time(self, time_text: str) -> tuple[int, int]:
        value = time_text.strip()
        match = re.fullmatch(r"(\d{1,2}):(\d{2})(?:\s*([AaPp][Mm]))?", value)

        if not match:
            raise ValueError(
                "Invalid time format. Use HH:MM, 09:20 PM, or 9:20 AM."
            )

        hour = int(match.group(1))
        minute = int(match.group(2))
        meridiem = match.group(3)

        if meridiem:
            if hour < 1 or hour > 12 or minute > 59:
                raise ValueError(
                    "Invalid time format. AM/PM times must use hours 1-12."
                )

            if meridiem.lower() == "am":
                hour = 0 if hour == 12 else hour
            else:
                hour = 12 if hour == 12 else hour + 12
        elif hour > 23 or minute > 59:
            raise ValueError(
                "Invalid time format. 24-hour times must use hours 00-23 "
                "and minutes 00-59."
            )

        return hour, minute

    def _next_recurring_time(
        self,
        alarm: Alarm,
        after_time: datetime,
        hour: int | None = None,
        minute: int | None = None,
    ) -> datetime:
        alarm_hour = hour if hour is not None else alarm.schedule_hour
        alarm_minute = minute if minute is not None else alarm.schedule_minute

        if alarm_hour is None or alarm_minute is None:
            alarm_hour = alarm.alarm_time.hour
            alarm_minute = alarm.alarm_time.minute

        for day_offset in range(14):
            candidate_date = after_time.date() + timedelta(days=day_offset)
            candidate = datetime.combine(candidate_date, datetime.min.time())
            candidate = candidate.replace(
                hour=alarm_hour,
                minute=alarm_minute,
                second=0,
                microsecond=0,
            )

            if candidate > after_time and self._is_allowed_day(alarm, candidate):
                return candidate

        raise ValueError("No valid day found for this recurring alarm.")

    def _is_allowed_day(self, alarm: Alarm, candidate: datetime) -> bool:
        weekday = candidate.weekday()

        if alarm.repeat_type == "daily":
            return weekday not in alarm.skip_weekdays

        if alarm.repeat_type == "weekly":
            return weekday in alarm.weekdays

        return True

    def _ring_alarm(self, alarm: Alarm) -> tuple[str, int | None]:
        print("\n" + "=" * 40)
        print(f"ALARM: {alarm.label}")
        if alarm.note:
            print(f"Note: {alarm.note}")
        print(f"Time: {alarm.alarm_time.strftime('%Y-%m-%d %H:%M')}")
        print("Press C to close now.")
        print(f"Press S to snooze for {DEFAULT_SNOOZE_MINUTES} minutes.")
        print("=" * 40)

        end_time = time.monotonic() + alarm.ring_duration_seconds

        while time.monotonic() < end_time:
            action = self._read_alarm_action()

            if action == "c":
                print("\nAlarm closed.\n")
                return "closed", None

            if action == "s":
                snooze_minutes = self._ask_snooze_minutes()
                print(f"\nAlarm snoozed for {snooze_minutes} minutes.\n")
                return "snoozed", snooze_minutes

            for _ in range(alarm.ring_count):
                if time.monotonic() >= end_time:
                    break

                action = self._read_alarm_action()

                if action == "c":
                    print("\nAlarm closed.\n")
                    return "closed", None

                if action == "s":
                    snooze_minutes = self._ask_snooze_minutes()
                    print(f"\nAlarm snoozed for {snooze_minutes} minutes.\n")
                    return "snoozed", snooze_minutes

                self.sound_player.play(alarm.sound_style)

        print(f"\nAlarm finished after {alarm.ring_duration_seconds} seconds.\n")
        return "closed", None

    def _read_alarm_action(self) -> str:
        try:
            import msvcrt
        except ImportError:
            return ""

        if not msvcrt.kbhit():
            return ""

        key = msvcrt.getwch().lower()

        if key in ("c", "s"):
            return key

        return ""

    def _ask_snooze_minutes(self) -> int:
        while True:
            try:
                snooze_text = input(
                    f"\nSnooze minutes (blank for {DEFAULT_SNOOZE_MINUTES}): "
                ).strip()
            except EOFError:
                return DEFAULT_SNOOZE_MINUTES

            if not snooze_text:
                return DEFAULT_SNOOZE_MINUTES

            try:
                snooze_minutes = int(snooze_text)
            except ValueError:
                print("Snooze minutes must be a number.")
                continue

            if (
                snooze_minutes < MIN_SNOOZE_MINUTES
                or snooze_minutes > MAX_SNOOZE_MINUTES
            ):
                print(
                    "Snooze minutes must be between "
                    f"{MIN_SNOOZE_MINUTES} and {MAX_SNOOZE_MINUTES}."
                )
                continue

            return snooze_minutes

    def _validate_repeat_type(self, repeat_type: str):
        if repeat_type not in ("once", "daily", "weekly"):
            raise ValueError("Repeat type must be one-time, daily, or weekly.")

    def _validate_repeat_days(
        self,
        repeat_type: str,
        weekdays: tuple[int, ...],
        skip_weekdays: tuple[int, ...],
    ):
        if repeat_type == "weekly" and not weekdays:
            raise ValueError("Weekly alarm requires at least one weekday.")

        if repeat_type == "daily" and len(skip_weekdays) == 7:
            raise ValueError("Daily alarm cannot skip all 7 days.")

        if repeat_type != "weekly" and weekdays:
            raise ValueError("Weekdays can only be set for weekly alarms.")

        if repeat_type != "daily" and skip_weekdays:
            raise ValueError("Skipped weekdays can only be set for daily alarms.")

        for day in (*weekdays, *skip_weekdays):
            if day < 0 or day > 6:
                raise ValueError("Weekday values must be between 0 and 6.")

    def _validate_ring_count(self, ring_count: int):
        if ring_count < 1 or ring_count > MAX_RING_COUNT:
            raise ValueError(f"Ring count must be between 1 and {MAX_RING_COUNT}.")

    def _validate_ring_duration(self, ring_duration_seconds: int):
        if (
            ring_duration_seconds < MIN_RING_DURATION_SECONDS
            or ring_duration_seconds > MAX_RING_DURATION_SECONDS
        ):
            raise ValueError(
                "Ring duration must be between "
                f"{MIN_RING_DURATION_SECONDS} and {MAX_RING_DURATION_SECONDS} seconds."
            )
