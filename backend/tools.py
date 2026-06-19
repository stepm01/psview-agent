from datetime import datetime, timedelta, timezone
from schemas import Schedule, ScheduleSlot, ConversationState

def build_schedule(state: ConversationState) -> Schedule:
    """Deterministic 'tool' the agent calls when it proposes a next step.
    Produces concrete slots (next 3 weekdays) with Google-Calendar-ready UTC timestamps."""
    fmt = "%Y%m%dT%H%M%SZ"
    plan = [("10:00 AM PT", 17), ("2:00 PM PT", 21), ("10:00 AM PT", 17)]  # PT->UTC (PDT = UTC-7)
    slots, day, i = [], datetime.now(timezone.utc), 0
    while len(slots) < 3:
        day = day + timedelta(days=1)
        if day.weekday() >= 5:  # skip weekend
            continue
        label_time, hour = plan[i]; i += 1
        start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=15)
        slots.append(ScheduleSlot(
            label=start.strftime("%a, %b %d · ") + label_time,
            start_iso=start.strftime(fmt), end_iso=end.strftime(fmt)))
    return Schedule(
        title=f"{state.company.name} × {state.candidate.name} — intro chat",
        duration_minutes=15,
        agenda=f"A quick 15-min intro about {state.company.name} and the {state.candidate.role} role.",
        slots=slots)