"""
SpeakUp — Email Utility
Sends verification emails using Gmail SMTP
"""

import smtplib
import os
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")

# Change this to your Netlify URL
FRONTEND_URL = "https://your-netlify-site.netlify.app"


def generate_token():
    """Generate a random secure token."""
    return secrets.token_urlsafe(32)


def send_verification_email(to_email: str, name: str, token: str):
    """Send a verification email to a new user."""
    verify_link = f"{FRONTEND_URL}/verify.html?token={token}"

    # Build the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your SpeakUp account"
    msg["From"]    = GMAIL_USER
    msg["To"]      = to_email

    html = f"""
    <div style="font-family:Helvetica,Arial,sans-serif;max-width:520px;margin:0 auto;background:#1a2b3c;color:#EDE8DC;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#213448,#4A7899);padding:32px;text-align:center;">
        <div style="font-size:28px;font-weight:900;letter-spacing:0.1em;">SPEAKUP</div>
        <div style="font-size:13px;opacity:0.7;margin-top:4px;">Public Speaking Simulator</div>
      </div>
      <div style="padding:32px;">
        <h2 style="margin:0 0 12px;">Hi {name} 👋</h2>
        <p style="color:rgba(237,232,220,0.7);line-height:1.7;margin:0 0 24px;">
          Thanks for joining SpeakUp! Click the button below to verify your
          email address and activate your account.
        </p>
        <a href="{verify_link}"
           style="display:inline-block;background:#4A7899;color:#fff;
                  padding:14px 32px;border-radius:999px;text-decoration:none;
                  font-weight:700;font-size:14px;letter-spacing:0.04em;">
          Verify My Account
        </a>
        <p style="color:rgba(237,232,220,0.4);font-size:12px;margin:24px 0 0;line-height:1.6;">
          This link expires in 24 hours. If you didn't create a SpeakUp account,
          you can safely ignore this email.
        </p>
      </div>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
         server.ehlo()
        server.starttls()
    server.login(GMAIL_USER, GMAIL_PASS)
    server.sendmail(GMAIL_USER, to_email, msg.as_string())
    return True
    except Exception as e:
    print(f"Email send failed: {e}")
    return False
