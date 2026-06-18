import os
import secrets
import resend

resend.api_key = os.getenv("RESEND_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://your-netlify-site.netlify.app")


def generate_token():
    return secrets.token_urlsafe(32)


def send_verification_email(to_email: str, name: str, token: str):
    verify_link = f"{FRONTEND_URL}/verify.html?token={token}"
    try:
        resend.Emails.send({
            "from": "SpeakUp <onboarding@resend.dev>",
            "to": to_email,
            "subject": "Verify your SpeakUp account",
            "html": f"""
                <div style="font-family:Helvetica,sans-serif;max-width:500px;margin:0 auto;background:#1a2b3c;color:#EDE8DC;border-radius:12px;overflow:hidden;">
                  <div style="background:linear-gradient(135deg,#213448,#4A7899);padding:32px;text-align:center;">
                    <h1 style="margin:0;letter-spacing:0.1em;">SPEAKUP</h1>
                  </div>
                  <div style="padding:32px;">
                    <h2>Hi {name}!</h2>
                    <p style="color:rgba(237,232,220,0.7);line-height:1.7;">
                      Click below to verify your email and activate your account.
                    </p>
                    <a href="{verify_link}"
                       style="display:inline-block;background:#4A7899;color:#fff;
                              padding:14px 32px;border-radius:999px;text-decoration:none;
                              font-weight:700;margin-top:8px;">
                      Verify My Account
                    </a>
                    <p style="color:rgba(237,232,220,0.4);font-size:12px;margin-top:24px;">
                      Link expires in 24 hours. Ignore this if you didn't sign up.
                    </p>
                  </div>
                </div>
            """
        })
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
