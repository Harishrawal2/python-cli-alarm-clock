from alarm_clock.constants import WEEKDAY_NAMES


WEEKDAY_LOOKUP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def parse_weekdays(day_text: str, allow_blank: bool = False) -> tuple[int, ...]:
    if not day_text.strip():
        if allow_blank:
            return ()
        raise ValueError("Please enter at least one weekday.")

    weekdays = set()

    for part in day_text.split(","):
        value = part.strip().lower()

        if value in WEEKDAY_LOOKUP:
            weekdays.add(WEEKDAY_LOOKUP[value])
        elif value in ("1", "2", "3", "4", "5", "6", "7"):
            weekdays.add(int(value) - 1)
        else:
            raise ValueError(
                "Invalid weekday. Use names like Mon,Wed,Fri or numbers 1-7."
            )

    return tuple(sorted(weekdays))


def format_weekdays(weekdays: tuple[int, ...]) -> str:
    return ", ".join(WEEKDAY_NAMES[day] for day in weekdays)
