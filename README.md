# Alarm Clock CLI

A professional terminal-only alarm clock built with Python. It uses in-memory
storage, the Python standard library, and a small package structure. There is
no web UI, no React app, and no database.

## Features

- One-time alarms for today or a future date
- Daily alarms, with optional skipped weekdays such as `Sat,Sun`
- Weekly alarms, using names like `Mon,Wed,Fri` or numbers like `1,3,5`
- 24-hour time input such as `21:20`
- AM/PM time input such as `09:20 PM`, `9:20 PM`, or `09:20 AM`
- Edit alarm time, label, note, repeat type, date, weekdays, sound, and duration
- Enable or disable alarms without deleting them
- Disabled alarms stay visible and show `[disabled]`
- Next active alarm preview above the main menu
- Menu option to show the next active alarm
- Menu option to show the next 3 or 5 upcoming alarms
- Alarm notes shown on the ring screen
- Snooze with `S`; close with `C`
- Default snooze duration of 5 minutes, with optional custom snooze minutes
- Per-alarm sound style: normal, fast, long, or silent
- Per-alarm ring duration
- Windows sound support with terminal bell fallback
- CLI package command: `alarm-clock`
- `alarm-clock --help`
- `alarm-clock --version`

## Installation

Requirements:

- Python 3.10 or newer
- No external runtime dependencies

Install locally from the project directory:

```bash
pip install .
```

Run without installing:

```bash
python alarm.py
```

Run after installing:

```bash
alarm-clock
```

Show help and version:

```bash
alarm-clock --help
alarm-clock --version
```

## Share And Install From PyPI

If this package is published on PyPI, share these instructions with users:

```text
Install Python 3.10 or newer:
https://www.python.org/downloads/

Then open Terminal or PowerShell and run:

pip install alarm-clock-cli
alarm-clock
```

If `pip` is not recognized or the install does not start, try:

```bash
python -m pip install alarm-clock-cli
```

On Windows, this may also work:

```bash
py -m pip install alarm-clock-cli
```

If pip is old, upgrade pip first:

```bash
python -m pip install --upgrade pip
python -m pip install alarm-clock-cli
```

If the package installs but `alarm-clock` is not recognized, close and reopen
the terminal. If it still fails, run:

```bash
python -m pip show alarm-clock-cli
```

That confirms whether the package is installed in the current Python
environment.

Reviewer note: this project is a Python CLI package. The install command adds a
console command named `alarm-clock`, which starts the interactive alarm clock.
No browser, server, database, or background service is required.

## Menu

```text
Next alarm: Today 09:30 PM - Meeting
Alarm Clock CLI
1. Set alarm
2. View alarms
3. Edit alarm
4. Enable/disable alarm
5. Show next alarm
6. Show upcoming alarms
7. Delete alarm
8. Test alarm sound
9. Exit
```

## Usage Examples

### One-Time Alarm

```text
Choose an option: 1
Enter alarm time HH:MM or 09:20 PM: 09:20 PM
Choose alarm type: 1
Enter date YYYY-MM-DD (blank for today): 2026-06-05
How many rings per cycle? (blank for 5): 3
Ring duration in seconds? (blank for 60): 45
Choose sound (blank for Normal): 1
Enter alarm label: Study break
Enter optional note (blank for none): Review chapter notes
```

Leave the date blank to use today. One-time alarms must be scheduled for a
future date and time.

### Daily Alarm

```text
Choose an option: 1
Enter alarm time HH:MM or 09:20 PM: 07:00
Choose alarm type: 2
Skip days? Example Sat,Sun or blank for none: Sat,Sun
How many rings per cycle? (blank for 5):
Ring duration in seconds? (blank for 60):
Choose sound (blank for Normal): 2
Enter alarm label: Office alarm
Enter optional note (blank for none): Pack laptop charger
```

### Weekly Alarm

```text
Choose an option: 1
Enter alarm time HH:MM or 09:20 PM: 9:20 PM
Choose alarm type: 3
Enter weekdays. Example Mon,Wed,Fri or 1,3,5: Mon,Wed,Fri
How many rings per cycle? (blank for 5): 5
Ring duration in seconds? (blank for 60): 60
Choose sound (blank for Normal): 4
Enter alarm label: Gym reminder
Enter optional note (blank for none): Take water bottle
```

Weekday numbers use `1 = Mon` through `7 = Sun`.

## AM/PM Examples

Accepted:

```text
21:20
09:20 PM
9:20 PM
09:20 AM
```

Invalid values show a clear validation error. For example, `13:20 PM` is
invalid because AM/PM hours must be between 1 and 12.

## Edit Alarms

Use menu option `3`:

```text
Choose an option: 3
Enter alarm ID to edit: 1
Enter alarm time HH:MM or 09:20 PM [21:20]: 09:45 PM
Choose alarm type (blank for One-time):
Enter date YYYY-MM-DD (blank for today) [2026-06-05]:
How many rings per cycle? (blank for 3):
Ring duration in seconds? (blank for 45): 60
Choose sound (blank for Normal):
Enter alarm label [Study break]: Study break updated
Enter optional note (blank keeps current, '-' clears): Send progress update
```

After an edit, the app recalculates the next alarm time.

## Enable Or Disable Alarms

Use menu option `4`:

```text
Choose an option: 4
Enter alarm ID to enable/disable: 2
Alarm 2 is now disabled.
```

Disabled alarms:

- Do not ring
- Stay visible in the alarm list
- Show `[disabled]`
- Are ignored by the next active alarm preview

Run option `4` again for the same ID to enable the alarm.

## Snooze Behavior

When an alarm rings:

```text
ALARM: Meeting
Note: Join Google Meet and send update
Press C to close now.
Press S to snooze for 5 minutes.
```

- Press `S` to snooze.
- Enter a custom snooze duration, or press Enter for the default 5 minutes.
- A snoozed one-time alarm stays active and rings again later.
- Daily and weekly alarms do not calculate their next normal occurrence until
  the alarm is finally closed or the ring duration finishes.
- Press `C` to close.
- One-time alarms become inactive after close.
- Daily and weekly alarms move to their next valid occurrence after close.

## Alarm List Output

Menu option `2` shows active and disabled alarms sorted by next alarm time:

```text
Alarms:
2. 2026-06-03 21:30 (09:30 PM) - Meeting | daily | normal sound | 60s | 5 rings/cycle | [disabled]
1. 2026-06-04 07:00 (07:00 AM) - Office alarm | daily except Sat, Sun | fast sound | 45s | 3 rings/cycle | [active]
3. 2026-06-05 21:20 (09:20 PM) - Gym | weekly on Mon, Wed, Fri | silent sound | 60s | 5 rings/cycle | [active]
```

## Upcoming Alarms

Use menu option `6`:

```text
Choose an option: 6
How many upcoming alarms? Enter 3 or 5 (blank for 5): 3
```

The output includes ID, date/time, label, repeat type, sound style, ring
duration, and status.

## Flow Diagrams

Create alarm flow:

```text
Start
  |
  v
Main menu -> Set alarm
  |
  v
Read time -> repeat type -> date/weekdays -> sound/duration -> label/note
  |
  v
Validate inputs -> calculate next alarm time -> store in memory
  |
  v
Return to menu
```

Ring flow:

```text
Scheduler checks active enabled alarms
  |
  v
Alarm due?
  |
  +-- no --> Return to menu/prompt loop
  |
  +-- yes --> Ring screen
                  |
                  +-- S --> Ask snooze minutes -> schedule temporary snooze time
                  |
                  +-- C --> Close alarm
                  |
                  +-- duration ends --> Close alarm
```

Recurring close flow:

```text
Daily/weekly alarm closes
  |
  v
Use original scheduled hour/minute
  |
  v
Find next allowed day
  |
  v
Update alarm's next ring time
```

## Project Structure

```text
python-project/
  alarm.py
  pyproject.toml
  README.md
  alarm_clock/
    __init__.py
    cli.py
    clock.py
    constants.py
    models.py
    sound.py
    weekdays.py
```

## Assumptions

- Alarms only need to exist while the program is running.
- The app is intentionally interactive and terminal-first.
- The main loop checks due alarms while waiting for typed input.
- Windows uses `winsound`; other systems use a terminal bell fallback.
- Disabled alarms keep their calculated date/time for display.

## Limitations

- No persistence; alarms are lost when the app exits.
- No database, files, cloud sync, or user accounts.
- No web UI or mobile notifications.
- Alarm timing depends on the Python process staying open.
- Terminal sound behavior depends on OS and terminal settings.

## AI-Assisted Planning

AI assistance was used to plan and implement the CLI feature set while keeping
the project intentionally small:

- Preserve a CLI-only architecture
- Keep alarms in memory
- Use the Python standard library
- Keep scheduling logic separate from menu/input logic
- Add professional alarm-clock behaviors without introducing a database,
  browser UI, or framework overhead
