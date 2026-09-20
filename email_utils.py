import os
from dotenv import load_dotenv
load_dotenv()
import smtplib
from flask import url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
# --- Hardcoded Credentials as Requested ---
# IMPORTANT: Replace "your_google_app_password" with your actual Google App Password.
# You can generate one from your Google Account settings under "Security" -> "2-Step Verification" -> "App passwords".
SENDER_EMAIL = "certchain.control@gmail.com"
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')  # Replace this!
ADMIN_EMAIL = "certchain.control@gmail.com"


def send_password_reset_email(recipient_email, token):
    """Sends an email with a password reset link."""
    # The _external=True is crucial to generate a full URL
    reset_url = url_for('reset_password', token=token, _external=True)
    
    subject = "CertChain - Password Reset Request"
    body = f"""
    <p>Hello,</p>
    <p>You requested a password reset for your CertChain account.</p>
    <p>Please click the link below to set a new password. This link is valid for 1 hour.</p>
    <p><a href="{reset_url}" style="color: #3B82F6; text-decoration: none;">Reset Your Password</a></p>
    <p>If you did not request this, please ignore this email.</p>
    <br>
    <p>Thank you,</p>
    <p>The CertChain Team</p>
    """
    
    # --- ADD THIS LINE ---
    send_email(recipient_email, subject, body)

    
def send_email(recipient_email, subject, html_content):
    """
    A robust and generic function to send HTML emails using a secure SSL connection.
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD or SENDER_PASSWORD == "your_google_app_password":
        print("❌ CRITICAL: Email credentials are not set or are using the default placeholder in email_utils.py. Email will not be sent.")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"CertChain Platform <{SENDER_EMAIL}>"
    message["To"] = recipient_email
    message.attach(MIMEText(html_content, "html"))

    try:
        # Using SMTP_SSL with a 10-second timeout.
        # Render's free tier blocks SMTP port 465, so this will fail fast
        # instead of hanging and killing the gunicorn worker.
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
        print(f"✅ Email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {recipient_email}. Error: {e}")
        return False

# --- Notification Helper Functions ---

def send_admin_signup_notification(user_type, user_data):
    """Notifies admin about a new signup request."""
    subject = f"New {user_type.capitalize()} Registration Request on CertChain"
    name = user_data.get('institution_name') or user_data.get('company_name')
    email = user_data.get('email')
    
    html_body = f"""
    <html><body style="font-family: sans-serif;">
        <h2>New {user_type.capitalize()} Registration Request</h2>
        <p>A new {user_type.lower()} has registered and is awaiting your approval.</p>
        <ul style="list-style-type: none; padding: 0;">
            <li style="margin-bottom: 10px;"><strong>Name:</strong> {name}</li>
            <li style="margin-bottom: 10px;"><strong>Email:</strong> {email}</li>
            <li style="margin-bottom: 10px;"><strong>Website:</strong> {user_data.get('website_url', 'N/A')}</li>
        </ul>
        <p>Please log in to the <strong><a href="#">Admin Dashboard</a></strong> to review and process the request.</p>
    </body></html>
    """
    send_email(ADMIN_EMAIL, subject, html_body)

def send_approval_email(recipient_email, user_type, name):
    """Informs a user that their registration has been approved."""
    subject = "Welcome to CertChain! Your Registration is Approved"
    html_body = f"""
    <html><body style="font-family: sans-serif;">
        <h2>Congratulations, {name}!</h2>
        <p>Your <strong>{user_type.lower()}</strong> registration on the CertChain platform has been <strong>approved</strong> by the administrator.</p>
        <p>You can now log in to your dashboard and start using the platform's features.</p>
        <p>Thank you for joining CertChain.</p>
    </body></html>
    """
    send_email(recipient_email, subject, html_body)

def send_denial_email(recipient_email, user_type, name):
    """Informs a user that their registration has been denied."""
    subject = "An Update on Your CertChain Registration"
    html_body = f"""
    <html><body style="font-family: sans-serif;">
        <h2>Dear {name},</h2>
        <p>We're writing to inform you that your <strong>{user_type.lower()}</strong> registration on the CertChain platform could not be approved at this time.</p>
        <p>This may be due to incomplete information or documentation that could not be verified. If you believe this is an error, please contact our support team by replying to this email.</p>
        <p>We appreciate your interest in CertChain.</p>
    </body></html>
    """
    send_email(recipient_email, subject, html_body)
    
def send_certificate_issuance_email(recipient_email, student_name, course_name, institution_name):
    """Informs a student that a new certificate has been issued to them."""
    subject = f"Your New '{course_name}' Certificate Has Been Issued!"
    html_body = f"""
    <html><body style="font-family: sans-serif;">
        <h2>Congratulations, {student_name}!</h2>
        <p>The institution, <strong>{institution_name}</strong>, has just issued a new certificate to you on the CertChain platform.</p>
        <ul style="list-style-type: none; padding: 0;">
            <li style="margin-bottom: 10px;"><strong>Certificate:</strong> {course_name}</li>
        </ul>
        <p>You can view your new certificate by logging into your student dashboard.</p>
        <p>Best regards,<br/>The CertChain Team</p>
    </body></html>
    """
    send_email(recipient_email, subject, html_body)

def send_verification_email(recipient_email, student_name, company_name):
    """Informs a student that their certificate has been verified."""
    subject = "Security Alert: Your Certificate Was Verified on CertChain"
    html_body = f"""
    <html><body style="font-family: sans-serif;">
        <h2>Hi {student_name},</h2>
        <p>This is a notification to let you know that one of your certificates was just verified by <strong>{company_name}</strong>.</p>
        <p>You can view your full verification history by logging into your student dashboard.</p>
        <p>If you do not recognize this activity, please contact support immediately.</p>
        <p>Thank you,<br/>The CertChain Team</p>
    </body></html>
    """
    send_email(recipient_email, subject, html_body)

# --- NEW FUNCTION FOR DISCREPANCY ALERTS ---
def send_discrepancy_alert_email(discrepancy_data):
    """Notifies the admin about a new data integrity discrepancy."""
    subject = "⚠️ SECURITY ALERT: Data Discrepancy Detected on CertChain"
    
    # Pretty-print the details dictionary for better readability in the email
    details_formatted = json.dumps(discrepancy_data.get('details', {}), indent=4)
    
    html_body = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6;">
        <h2 style="color: #d9534f;">Data Integrity Alert</h2>
        <p>The automated cross-verification system has detected a discrepancy between the blockchain record and the Firebase database.</p>
        <p>Please review the details below and take appropriate action by visiting the Admin Dashboard.</p>
        <hr>
        <h3 style="margin-bottom: 5px;">Discrepancy Details:</h3>
        <ul style="list-style-type: none; padding-left: 0;">
            <li><strong>Issue:</strong> {discrepancy_data.get('issue', 'N/A')}</li>
            <li><strong>Status:</strong> {discrepancy_data.get('status', 'N/A')}</li>
            <li><strong>Certificate Hash:</strong><br>
                <code style="font-size: 0.9em; background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; color: #333;">
                    {discrepancy_data.get('certificateHash', 'N/A')}
                </code>
            </li>
        </ul>
        <h3 style="margin-top: 20px; margin-bottom: 5px;">Data Comparison:</h3>
        <pre style="background-color: #2b2b2b; color: #f8f8f2; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;">{details_formatted}</pre>
        <p style="margin-top: 25px;">
            <a href="#" style="background-color: #c9302c; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">
                Go to Admin Dashboard
            </a>
        </p>
    </body>
    </html>
    """
    send_email(ADMIN_EMAIL, subject, html_body)

def send_contact_form_email(name, sender_email, subject, message):
    """Sends the contact form submission to the admin."""
    email_subject = f"New Contact Form Submission: {subject}"
    
    html_body = f"""
    <html><body style="font-family: sans-serif; line-height: 1.6;">
        <h2>New Message from CertChain Contact Form</h2>
        <p>You have received a new message from the website's contact form.</p>
        <hr>
        <ul style="list-style-type: none; padding: 0;">
            <li style="margin-bottom: 10px;"><strong>From:</strong> {name}</li>
            <li style="margin-bottom: 10px;"><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></li>
            <li style="margin-bottom: 10px;"><strong>Subject:</strong> {subject}</li>
        </ul>
        <h3 style="margin-top: 20px; margin-bottom: 5px;">Message:</h3>
        <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;">
            {message}
        </div>
    </body></html>
    """
    
    return send_email(ADMIN_EMAIL, email_subject, html_body)
