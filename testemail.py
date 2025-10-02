#!/usr/bin/env python3
"""Quick email test - just paste your credentials and run"""

import smtplib
from email.mime.text import MIMEText

# ============ PASTE YOUR CREDENTIALS HERE ============
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "o.fmwmf.o@gmail.com"  # ← Change this
EMAIL_TO = "spisolja@gmail.com"  # ← Change this
# Gmail App Password (16 chars, NO spaces!)
PASSWORD = "gg"  # ← Change this
# =====================================================

print(f"Testing email from {EMAIL_FROM} to {EMAIL_TO}...")
print(f"Password length: {len(PASSWORD)}")

if len(PASSWORD) != 16:
    print("⚠️  WARNING: Gmail App Password should be exactly 16 chars!")
    print("   Did you remove all spaces?")

try:
    print("\n1. Connecting...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
    print("   ✅ Connected")

    print("2. Starting TLS...")
    server.starttls()
    print("   ✅ TLS started")

    print("3. Logging in...")
    server.login(EMAIL_FROM, PASSWORD)
    print("   ✅ Logged in")

    print("4. Sending email...")
    msg = MIMEText("Test successful! 🎉")
    msg['Subject'] = "Quick Test"
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    server.send_message(msg)
    print("   ✅ Email sent")

    server.quit()

    print("\n✅✅✅ SUCCESS! Check your inbox! ✅✅✅")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nIf authentication error:")
    print("  → Create App Password: https://myaccount.google.com/apppasswords")
    print("  → Remove ALL spaces from the password")