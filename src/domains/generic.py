from src.domains.pack import ActionBlueprint, DomainPack

GENERIC_PACK = DomainPack(
    name="generic",
    label_keywords={
        "App Performance & Bugs": ["crash", "lag", "login", "freeze", "blank screen", "stuck", "bug", "glitch", "slow", "error"],
        "Customer Support": ["support", "ticket", "customer care", "agent", "executive", "reply", "helpline", "refund"],
        "Positive UX & Simplicity": ["easy", "simple", "love", "awesome", "excellent", "superb", "clean", "best app"],
    },
    actions={
        "App Performance & Bugs": ActionBlueprint(
            "Mobile Reliability Team",
            "Triage the crash and freeze flows named in these reviews and track crash-free sessions weekly."),
        "Customer Support": ActionBlueprint(
            "Customer Operations",
            "Audit unresolved tickets behind these reviews and set a first-response time target for them."),
        "Positive UX & Simplicity": ActionBlueprint(
            "Product Design Team",
            "Reuse the flow users praise here in one more screen and track its completion rate."),
    },
)
