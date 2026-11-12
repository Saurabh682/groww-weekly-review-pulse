# Groww Weekly Review Pulse | Week of 2026-11-10
Window: 12 weeks | Reviews analyzed: 210 | Avg rating: 3.4★

## Top 3 Themes
1. **Payments & UPI** (38% of reviews, avg 2.1★): Pending wallet credits and UPI timeouts during peak market hours.
2. **Account Opening & KYC** (27% of reviews, avg 2.5★): Document verification delays and stuck video KYC links.
3. **App Performance** (19% of reviews, avg 2.8★): Market opening chart lag and biometric login failures.

## What Users Said
- "Money debited from bank account via UPI but not credited to Groww wallet."
- "KYC process is stuck since 4 days. Customer support is not responding to tickets."
- "App crashed right at 9:15 AM market opening. Could not place stop loss."

## Action Ideas
1. **Payments:** Add real-time bank status banner and auto-reconciliation retry within 15 minutes. (Owner: Payments Eng)
2. **KYC:** Instrument Digilocker retry telemetry and alert users on document blur before submission. (Owner: Onboarding PM)
3. **App Performance:** Optimize socket reconnect throttling between 9:10 and 9:25 AM. (Owner: Mobile Infra)