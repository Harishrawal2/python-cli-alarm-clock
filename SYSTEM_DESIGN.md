# System Design: Alarm Clock CLI

This document explains the flow and module design of the Python CLI alarm clock.

## High-Level Architecture

```mermaid
flowchart TD
    A[User opens terminal] --> B[Run python alarm.py]
    B --> C[alarm.py entrypoint]
    C --> D[alarm_clock.cli.run]
    D --> E[Show next alarm summary and CLI menu]

    E --> F{User choice}
    F -->|1 Set alarm| G[Collect alarm details]
    F -->|2 View alarms| H[List alarms with status]
    F -->|3 Show next alarm| I[Display nearest enabled alarm]
    F -->|4 Enable/disable alarm| J[Toggle selected alarm]
    F -->|5 Delete alarm| K[Cancel selected alarm]
    F -->|6 Test alarm sound| L[Play selected sound]
    F -->|7 Exit| M[Stop app]

    G --> L[Validate time/date/repeat rules]
    L --> M[Create Alarm model]
    M --> N[Store alarm in memory]
    N --> E

    H --> E
    I --> E
    J --> E
    K --> E
    L --> E
```

## Folder Responsibility

```mermaid
flowchart LR
    A[alarm.py] --> B[alarm_clock.cli]
    B --> C[alarm_clock.clock]
    B --> D[alarm_clock.weekdays]
    C --> E[alarm_clock.models]
    C --> F[alarm_clock.sound]
    C --> G[alarm_clock.constants]
    D --> G

    A1[Entrypoint] -.-> A
    B1[Menu and user prompts] -.-> B
    C1[Scheduling and ringing logic] -.-> C
    D1[Parse Mon Wed Fri or 1 3 5] -.-> D
    E1[Alarm dataclass] -.-> E
    F1[Windows sound and terminal fallback] -.-> F
    G1[Shared config] -.-> G
```

## Alarm Creation Flow

```mermaid
flowchart TD
    A[Choose Set alarm] --> B[Enter time HH:MM or AM/PM]
    B --> C{Alarm type}

    C -->|One-time| D[Optional date YYYY-MM-DD]
    C -->|Daily| E[Optional skip days]
    C -->|Weekly| F[Required weekdays]

    D --> G[Choose ring count]
    E --> G
    F --> G

    G --> H[Choose sound style]
    H --> I[Enter label]
    I --> J[Validate input]
    J --> K{Valid?}

    K -->|No| L[Show error]
    L --> M[Return to menu]

    K -->|Yes| N[Calculate next alarm datetime]
    N --> O[Create Alarm object]
    O --> P[Add to active alarm list]
    P --> M
```

Supported time inputs include `21:20`, `09:20 PM`, `09:20 AM`, and `9:20 PM`.

## Repeat Scheduling Flow

```mermaid
flowchart TD
    A[Alarm time is calculated] --> B{Repeat type}

    B -->|One-time| C[Use selected date or today]
    C --> D{Is date/time future?}
    D -->|No| E[Reject with error]
    D -->|Yes| F[Save alarm]

    B -->|Daily| G[Check today at selected time]
    G --> H{Already passed today?}
    H -->|Yes| I[Move to next day]
    H -->|No| J[Use today]
    I --> K{Day skipped?}
    J --> K
    K -->|Yes| I
    K -->|No| F

    B -->|Weekly| L[Find next selected weekday]
    L --> M{Candidate is future?}
    M -->|No| L
    M -->|Yes| F
```

## Runtime Alarm Check Flow

```mermaid
flowchart TD
    A[CLI waits for user input] --> B[Check due enabled alarms repeatedly]
    B --> C{Any enabled alarm due?}
    C -->|No| A
    C -->|Yes| D[Start ringing alarm]

    D --> E[Show alarm message]
    E --> F[Play sound cycles for up to 60 seconds]
    F --> G{User pressed C?}
    G -->|Yes| H[Close alarm immediately]
    G -->|No| I{User pressed S?}
    I -->|Yes| J[Snooze for 5 minutes]
    I -->|No| K{60 seconds complete?}
    K -->|No| F
    K -->|Yes| L[Finish ringing]

    H --> M{Repeat type}
    L --> M
    J --> A
    M -->|One-time| N[Mark inactive]
    M -->|Daily or weekly| O[Calculate next valid occurrence]
    N --> A
    O --> A
```

## Sound Flow

```mermaid
flowchart TD
    A[Alarm needs sound] --> B{Sound style}
    B -->|Normal| C[SystemExclamation + beep]
    B -->|Fast| D[SystemAsterisk + fast beep pattern]
    B -->|Long| E[SystemHand + long beep]
    B -->|Silent| F[Wait without sound]

    C --> G{Windows winsound available?}
    D --> G
    E --> G

    G -->|Yes| H[Play Windows system sound]
    H --> I[Play winsound.Beep pattern]
    G -->|No| J[Use terminal bell fallback]
```

## Data Model

```mermaid
classDiagram
    class Alarm {
        int id
        datetime alarm_time
        str label
        str repeat_type
        tuple weekdays
        tuple skip_weekdays
        int ring_count
        str sound_style
        bool active
        bool enabled
        int schedule_hour
        int schedule_minute
    }

    class AlarmClock {
        list alarms
        int next_id
        bool running
        AlarmSoundPlayer sound_player
        add_alarm()
        active_alarms()
        alarms_for_display()
        next_alarm()
        delete_alarm()
        toggle_alarm_enabled()
        check_due_alarms()
        format_repeat()
    }

    class AlarmSoundPlayer {
        SOUND_PATTERNS
        play()
    }

    AlarmClock --> Alarm
    AlarmClock --> AlarmSoundPlayer
```

## Current Storage Design

The app stores alarms in memory only.

```mermaid
flowchart LR
    A[User sets alarm] --> B[Alarm object]
    B --> C[In-memory list]
    C --> D[Available while app is running]
    D --> E[Lost when app exits]
```

This matches the current project requirement: no database. If persistence is
needed later, a JSON file can be added without changing the CLI flow much.

## Main Design Decisions

- CLI only, no web UI
- No database
- Simple in-memory alarm list
- Separate modules for clean architecture
- `alarm.py` kept as a small launcher
- Windows sound support through `winsound`
- Terminal fallback for non-Windows systems
- 24-hour and AM/PM time input are both accepted
- Disabled alarms remain visible but do not ring
- Next alarm preview uses the nearest enabled alarm
- Snoozed alarms ring again after 5 minutes
- Daily and weekly recurrence calculated from the next valid future date
- Alarm ringing lasts up to 60 seconds
- User can close a ringing alarm with `C`
- User can snooze a ringing alarm with `S`
