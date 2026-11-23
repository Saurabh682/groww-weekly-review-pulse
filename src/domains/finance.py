from src.domains.pack import ActionBlueprint, DomainPack, OneLinerRule

FINANCE_PACK = DomainPack(
    name="finance",
    label_keywords={
        "Payments & UPI": ["upi", "payment", "wallet", "gpay", "phonepe", "add fund", "credited", "debit"],
        "Account Opening & KYC": ["kyc", "document", "onboarding", "verification", "bank account", "digilocker", "pan"],
        "Withdrawals & Payouts": ["withdraw", "redemption", "settlement", "payout", "delayed payout"],
        "App Performance & Bugs": ["crash", "lag", "login", "biometric", "freeze", "blank screen", "stuck", "bug", "glitch", "slow"],
        "Charges & Pricing": ["charge", "brokerage", "hidden", "fee", "stt", "amc", "deducted"],
        "Customer Support": ["support", "ticket", "bot", "call", "agent", "executive", "reply", "helpline"],
        "Mutual Funds & SIPs": ["sip", "mutual fund", "nav", "portfolio", "returns", "index fund"],
        "Positive UX & Simplicity": ["easy", "simple", "love", "awesome", "excellent", "superb", "clean", "best app"],
    },
    one_liners=(
        OneLinerRule(("charge", "pricing", "fee"),
                     "Users report unexpected charges and request transparent fee breakdowns on equity and DP deductions."),
        OneLinerRule(("bug", "performance", "lag"),
                     "Frequent app lag and freezing reported during peak trading hours, impacting order execution."),
        OneLinerRule(("support", "service", "help"),
                     "Customer service tickets experience delayed response times and automated bot reply loops."),
        OneLinerRule(("kyc", "verification", "onboard"),
                     "Delays in bank account verification and repeated video KYC link expiries during onboarding."),
        OneLinerRule(("payment", "transfer", "wallet", "deposit", "withdraw"),
                     "Users report UPI transfers debited from banks that do not reflect in the app wallet immediately."),
    ),
    positive_one_liner="Users praise intuitive navigation, clean interface design, and straightforward mutual fund investing.",
    actions={
        "Charges & Pricing": ActionBlueprint(
            "Core Brokerage Team",
            "Deploy in-app fee breakdown calculator and display itemized DP charges on order confirmation screens."),
        "App Performance & Bugs": ActionBlueprint(
            "Mobile Reliability Team",
            "Conduct load testing on morning market-open websocket channels and patch chart rendering memory leaks."),
        "Customer Support": ActionBlueprint(
            "Customer Operations",
            "Implement priority escalation routing for unresolved payment tickets older than 48 hours."),
        "Onboarding & KYC": ActionBlueprint(
            "Identity Verification Team",
            "Extend video KYC session timeout to 15 minutes and integrate automated DigiLocker retry webhooks."),
        "Payments & Withdrawals": ActionBlueprint(
            "Banking Integrations Team",
            "Implement real-time UPI transaction reconciliation with partner bank gateways to prevent debit/credit lag."),
        "Trading & Order Execution": ActionBlueprint(
            "Order Engine Team",
            "Optimize stop-loss order trigger latency during high market volatility at 9:15 AM opening."),
        "Positive UX & Simplicity": ActionBlueprint(
            "Product Design Team",
            "Maintain current simplified mutual fund dashboard layout while streamlining advanced equity analytics."),
    },
)
