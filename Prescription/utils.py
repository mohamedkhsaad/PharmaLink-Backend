# utils.py

import random

def generate_session_id():
    """
    Generate a random session ID.
    """
    return random.randint(100000, 999999)

def generate_otp():
    """
    Generate a random OTP.
    """
    return random.randint(1000, 9999)

def validate_session(session_id):
    """
    Validate the session ID.
    For demonstration purposes, always return True.
    """
    return True

def send_otp(phone_number, otp):
    """
    Send OTP to the provided phone number.
    For demonstration purposes, just print the OTP.
    """
    print(f"OTP: {otp} sent to {phone_number}")

import smtplib
from email.mime.text import MIMEText

def send_custom_email_otp(user_id, email, otp):
    subject = 'Your OTP for PharmaLink'
    message = f'Your OTP for PharmaLink is: {otp}'
    sender_email = 'pharmalink1190264@gmail.com'
    receiver_email = email
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, "azuk ngik jmqo udcb")
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

