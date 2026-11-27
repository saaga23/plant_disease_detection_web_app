"""Plant Disease Detection Web App - application package.

The public repository previously exposed a hardcoded MySQL root credential in
the application source. All credentials are now supplied exclusively through
environment variables (see .env.example). If a legacy deployment relies on the
old hardcoded credential, treat it as compromised and rotate it.
"""
