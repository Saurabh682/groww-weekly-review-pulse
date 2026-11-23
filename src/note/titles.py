def pulse_doc_title(app_name: str, week_start: str) -> str:
    return f"{app_name} Weekly Review Pulse: Week of {week_start}"


def pulse_email_subject(app_name: str, week_start: str) -> str:
    return f"{app_name} Weekly Review Pulse | Week of {week_start}"
