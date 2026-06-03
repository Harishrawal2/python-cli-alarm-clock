import argparse
import sys
import time

from alarm_clock import __version__
from alarm_clock.clock import AlarmClock
from alarm_clock.constants import (
    ALARM_RING_SECONDS,
    DEFAULT_RING_COUNT,
    MAX_RING_COUNT,
    MAX_RING_DURATION_SECONDS,
    MIN_RING_DURATION_SECONDS,
)
from alarm_clock.models import Alarm
from alarm_clock.weekdays import format_weekdays, parse_weekdays


def run(argv: list[str] | None = None):
    parser = build_parser()
    parser.parse_args(argv)
    alarm_clock = AlarmClock()

    try:
        while True:
            alarm_clock.check_due_alarms()
            show_menu(alarm_clock)
            choice = prompt(alarm_clock, "Choose an option: ").strip()

            if choice == "1":
                set_alarm(alarm_clock)
            elif choice == "2":
                list_alarms(alarm_clock)
            elif choice == "3":
                edit_alarm(alarm_clock)
            elif choice == "4":
                toggle_alarm(alarm_clock)
            elif choice == "5":
                show_next_alarm(alarm_clock)
            elif choice == "6":
                show_upcoming_alarms(alarm_clock)
            elif choice == "7":
                delete_alarm(alarm_clock)
            elif choice == "8":
                test_alarm_sound(alarm_clock)
            elif choice == "9":
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid option. Please try again.\n")
    except KeyboardInterrupt:
        print("\n\nAlarm clock stopped. Goodbye!")
    finally:
        alarm_clock.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm-clock",
        description="Run the interactive Python CLI alarm clock.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"alarm-clock {__version__}",
    )
    return parser


def show_menu(alarm_clock: AlarmClock | None = None):
    if alarm_clock:
        next_alarm = alarm_clock.next_alarm()
        if next_alarm:
            print(f"\nNext alarm: {alarm_clock.format_next_alarm_preview(next_alarm)}")
        else:
            print("\nNext alarm: None")

    print("Alarm Clock CLI")
    print("1. Set alarm")
    print("2. View alarms")
    print("3. Edit alarm")
    print("4. Enable/disable alarm")
    print("5. Show next alarm")
    print("6. Show upcoming alarms")
    print("7. Delete alarm")
    print("8. Test alarm sound")
    print("9. Exit")


def set_alarm(alarm_clock: AlarmClock):
    try:
        fields = collect_alarm_fields(alarm_clock)
        alarm = alarm_clock.add_alarm(**fields)
        print_alarm_saved(alarm_clock, alarm, "Alarm set")
    except ValueError as error:
        print(f"\nError: {error}\n")


def edit_alarm(alarm_clock: AlarmClock):
    try:
        alarm_id = read_alarm_id(alarm_clock, "Enter alarm ID to edit: ")
        alarm = alarm_clock.get_alarm(alarm_id)

        if not alarm:
            print("\nAlarm not found.\n")
            return

        print("\nEditing alarm:")
        print_alarm_line(alarm_clock, alarm)
        fields = collect_alarm_fields(alarm_clock, alarm)
        edited_alarm = alarm_clock.edit_alarm(alarm_id=alarm_id, **fields)

        if not edited_alarm:
            print("\nAlarm not found.\n")
            return

        print_alarm_saved(alarm_clock, edited_alarm, "Alarm updated")
    except ValueError as error:
        print(f"\nError: {error}\n")


def collect_alarm_fields(
    alarm_clock: AlarmClock,
    alarm: Alarm | None = None,
) -> dict[str, object]:
    time_text = read_time_text(alarm_clock, alarm)
    repeat_type = choose_repeat_type(alarm_clock, alarm.repeat_type if alarm else None)
    date_text = ""
    weekdays = ()
    skip_weekdays = ()

    if repeat_type == "once":
        date_text = read_date_text(alarm_clock, alarm)
    elif repeat_type == "daily":
        skip_weekdays = read_skip_weekdays(alarm_clock, alarm)
    elif repeat_type == "weekly":
        weekdays = read_weekdays(alarm_clock, alarm)

    ring_count = choose_ring_count(alarm_clock, alarm.ring_count if alarm else None)
    ring_duration_seconds = choose_ring_duration(
        alarm_clock,
        alarm.ring_duration_seconds if alarm else None,
    )
    sound_style = choose_sound_style(alarm_clock, alarm.sound_style if alarm else None)
    label = read_label(alarm_clock, alarm)
    note = read_note(alarm_clock, alarm)

    return {
        "time_text": time_text,
        "label": label,
        "note": note,
        "date_text": date_text,
        "repeat_type": repeat_type,
        "weekdays": weekdays,
        "skip_weekdays": skip_weekdays,
        "ring_count": ring_count,
        "ring_duration_seconds": ring_duration_seconds,
        "sound_style": sound_style,
    }


def list_alarms(alarm_clock: AlarmClock):
    alarms = alarm_clock.alarms_for_display()

    if not alarms:
        print("\nNo alarms.\n")
        return

    print("\nAlarms:")
    for alarm in alarms:
        print_alarm_line(alarm_clock, alarm)
    print()


def show_next_alarm(alarm_clock: AlarmClock):
    next_alarm = alarm_clock.next_alarm()

    if not next_alarm:
        print("\nNo active enabled alarms.\n")
        return

    print(f"\nNext alarm: {alarm_clock.format_next_alarm_preview(next_alarm)}\n")


def show_upcoming_alarms(alarm_clock: AlarmClock):
    try:
        count_text = prompt(
            alarm_clock,
            "How many upcoming alarms? Enter 3 or 5 (blank for 5): ",
        ).strip()
        count = 5 if not count_text else int(count_text)

        if count not in (3, 5):
            raise ValueError("Upcoming alarm count must be 3 or 5.")

        alarms = alarm_clock.upcoming_alarms(count)

        if not alarms:
            print("\nNo alarms.\n")
            return

        print(f"\nNext {len(alarms)} alarms:")
        for alarm in alarms:
            print_alarm_line(alarm_clock, alarm)
        print()
    except ValueError as error:
        print(f"\nError: {error}\n")


def toggle_alarm(alarm_clock: AlarmClock):
    try:
        alarm_id = read_alarm_id(alarm_clock, "Enter alarm ID to enable/disable: ")
        alarm = alarm_clock.toggle_alarm_enabled(alarm_id)

        if not alarm:
            print("\nAlarm not found.\n")
            return

        print(f"\nAlarm {alarm.id} is now {alarm_clock.format_status(alarm)}.\n")
    except ValueError as error:
        print(f"\nError: {error}\n")


def delete_alarm(alarm_clock: AlarmClock):
    try:
        alarm_id = read_alarm_id(alarm_clock, "Enter alarm ID to delete: ")
        deleted = alarm_clock.delete_alarm(alarm_id)

        if deleted:
            print("\nAlarm deleted successfully.\n")
        else:
            print("\nAlarm not found.\n")
    except ValueError as error:
        print(f"\nError: {error}\n")


def test_alarm_sound(alarm_clock: AlarmClock):
    try:
        sound_style = choose_sound_style(alarm_clock)
        ring_count = choose_ring_count(alarm_clock)

        print("\nTesting alarm sound...\n")
        for _ in range(ring_count):
            alarm_clock.sound_player.play(sound_style)
    except ValueError as error:
        print(f"\nError: {error}\n")


def read_time_text(alarm_clock: AlarmClock, alarm: Alarm | None = None) -> str:
    current = ""
    if alarm:
        hour = alarm.schedule_hour if alarm.schedule_hour is not None else alarm.alarm_time.hour
        minute = alarm.schedule_minute if alarm.schedule_minute is not None else alarm.alarm_time.minute
        current = f"{hour:02d}:{minute:02d}"

    time_text = prompt_with_default(
        alarm_clock,
        "Enter alarm time HH:MM or 09:20 PM",
        current,
    )
    if not time_text:
        raise ValueError("Alarm time is required.")
    return time_text


def read_date_text(alarm_clock: AlarmClock, alarm: Alarm | None = None) -> str:
    current = ""
    if alarm and alarm.repeat_type == "once":
        current = alarm.alarm_time.strftime("%Y-%m-%d")

    return prompt_with_default(
        alarm_clock,
        "Enter date YYYY-MM-DD (blank for today)",
        current,
    )


def read_skip_weekdays(alarm_clock: AlarmClock, alarm: Alarm | None = None):
    current = ""
    if alarm and alarm.repeat_type == "daily":
        current = format_weekdays(alarm.skip_weekdays)

    skip_text = prompt_with_default(
        alarm_clock,
        "Skip days? Example Sat,Sun or blank for none",
        current,
    )
    skip_weekdays = parse_weekdays(skip_text, allow_blank=True)

    if len(skip_weekdays) == 7:
        raise ValueError("Daily alarm cannot skip all 7 days.")

    return skip_weekdays


def read_weekdays(alarm_clock: AlarmClock, alarm: Alarm | None = None):
    current = ""
    if alarm and alarm.repeat_type == "weekly":
        current = format_weekdays(alarm.weekdays)

    day_text = prompt_with_default(
        alarm_clock,
        "Enter weekdays. Example Mon,Wed,Fri or 1,3,5",
        current,
    )
    return parse_weekdays(day_text)


def read_label(alarm_clock: AlarmClock, alarm: Alarm | None = None) -> str:
    current = alarm.label if alarm else ""
    return prompt_with_default(alarm_clock, "Enter alarm label", current) or "Alarm"


def read_note(alarm_clock: AlarmClock, alarm: Alarm | None = None) -> str:
    if not alarm:
        return prompt(alarm_clock, "Enter optional note (blank for none): ").strip()

    note = prompt(
        alarm_clock,
        "Enter optional note (blank keeps current, '-' clears): ",
    ).strip()

    if note == "":
        return alarm.note
    if note == "-":
        return ""
    return note


def choose_repeat_type(
    alarm_clock: AlarmClock,
    current: str | None = None,
) -> str:
    print("\nAlarm type")
    print("1. One-time")
    print("2. Daily")
    print("3. Weekly")

    suffix = f" (blank for {format_repeat_choice(current)})" if current else ""
    repeat_choice = prompt(alarm_clock, f"Choose alarm type{suffix}: ").strip()

    if not repeat_choice and current:
        return current
    if repeat_choice == "1":
        return "once"
    if repeat_choice == "2":
        return "daily"
    if repeat_choice == "3":
        return "weekly"

    raise ValueError("Invalid alarm type.")


def choose_ring_count(
    alarm_clock: AlarmClock,
    current: int | None = None,
) -> int:
    default = current if current is not None else DEFAULT_RING_COUNT
    ring_text = prompt(
        alarm_clock,
        f"How many rings per cycle? (blank for {default}): ",
    ).strip()

    if not ring_text:
        return default

    try:
        ring_count = int(ring_text)
    except ValueError:
        raise ValueError("Ring count must be a number.")

    if ring_count < 1 or ring_count > MAX_RING_COUNT:
        raise ValueError(f"Ring count must be between 1 and {MAX_RING_COUNT}.")

    return ring_count


def choose_ring_duration(
    alarm_clock: AlarmClock,
    current: int | None = None,
) -> int:
    default = current if current is not None else ALARM_RING_SECONDS
    duration_text = prompt(
        alarm_clock,
        f"Ring duration in seconds? (blank for {default}): ",
    ).strip()

    if not duration_text:
        return default

    try:
        duration = int(duration_text)
    except ValueError:
        raise ValueError("Ring duration must be a number.")

    if duration < MIN_RING_DURATION_SECONDS or duration > MAX_RING_DURATION_SECONDS:
        raise ValueError(
            "Ring duration must be between "
            f"{MIN_RING_DURATION_SECONDS} and {MAX_RING_DURATION_SECONDS} seconds."
        )

    return duration


def choose_sound_style(
    alarm_clock: AlarmClock,
    current: str | None = None,
) -> str:
    print("\nAlarm sound")
    print("1. Normal")
    print("2. Fast")
    print("3. Long")
    print("4. Silent")

    suffix = f" (blank for {current.title()})" if current else " (blank for Normal)"
    sound_choice = prompt(alarm_clock, f"Choose sound{suffix}: ").strip()

    if not sound_choice and current:
        return current
    if sound_choice in ("", "1"):
        return "normal"
    if sound_choice == "2":
        return "fast"
    if sound_choice == "3":
        return "long"
    if sound_choice == "4":
        return "silent"

    raise ValueError("Invalid sound choice.")


def read_alarm_id(alarm_clock: AlarmClock, prompt_text: str) -> int:
    alarm_id_text = prompt(alarm_clock, prompt_text).strip()

    try:
        return int(alarm_id_text)
    except ValueError:
        raise ValueError("Please enter a valid alarm ID.")


def prompt_with_default(
    alarm_clock: AlarmClock,
    prompt_text: str,
    current: str,
) -> str:
    if current:
        return prompt(alarm_clock, f"{prompt_text} [{current}]: ").strip() or current
    return prompt(alarm_clock, f"{prompt_text}: ").strip()


def format_repeat_choice(repeat_type: str | None) -> str:
    if repeat_type == "once":
        return "One-time"
    if repeat_type == "daily":
        return "Daily"
    if repeat_type == "weekly":
        return "Weekly"
    return "One-time"


def print_alarm_saved(alarm_clock: AlarmClock, alarm: Alarm, prefix: str):
    print(
        f"\n{prefix} for "
        f"{alarm_clock.format_alarm_time_with_ampm(alarm)} "
        f"- {alarm.label} "
        f"({alarm_clock.format_repeat(alarm)}, "
        f"{alarm.ring_count} rings/cycle, "
        f"{alarm.sound_style} sound, "
        f"{alarm.ring_duration_seconds}s duration) "
        f"[{alarm_clock.format_status(alarm)}]\n"
    )


def print_alarm_line(alarm_clock: AlarmClock, alarm: Alarm):
    print(
        f"{alarm.id}. "
        f"{alarm_clock.format_alarm_time_with_ampm(alarm)} "
        f"- {alarm.label} | "
        f"{alarm_clock.format_repeat(alarm)} | "
        f"{alarm.sound_style} sound | "
        f"{alarm.ring_duration_seconds}s | "
        f"{alarm.ring_count} rings/cycle | "
        f"[{alarm_clock.format_status(alarm)}]"
    )


def prompt(alarm_clock: AlarmClock, prompt_text: str) -> str:
    if not sys.stdin.isatty():
        return input(prompt_text)

    try:
        import msvcrt
    except ImportError:
        return input(prompt_text)

    print(prompt_text, end="", flush=True)
    characters = []

    while alarm_clock.running:
        alarm_clock.check_due_alarms()

        if msvcrt.kbhit():
            key = msvcrt.getwch()

            if key == "\r":
                print()
                return "".join(characters)

            if key == "\003":
                raise KeyboardInterrupt

            if key == "\b":
                if characters:
                    characters.pop()
                    print("\b \b", end="", flush=True)
                continue

            if key in ("\x00", "\xe0"):
                if msvcrt.kbhit():
                    msvcrt.getwch()
                continue

            characters.append(key)
            print(key, end="", flush=True)

        time.sleep(0.1)

    return "".join(characters)
