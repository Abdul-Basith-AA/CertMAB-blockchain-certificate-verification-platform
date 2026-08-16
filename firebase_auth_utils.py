import pyrebase

# Firebase configuration using your project's details
firebase_config = {
    "apiKey": "AIzaSyBl5XDuPhhno1aqKNgo76nygif1koukUDc",
    "authDomain": "samp-133ee.firebaseapp.com",
    "projectId": "samp-133ee",
    "storageBucket": "samp-133ee.appspot.com",
    "messagingSenderId": "500451175963",
    "appId": "1:500451175963:web:e2b7e0a7c4a17b0d2d3e4f",  # Optional
    "measurementId": "G-L5Q1EDG1N8",  # Optional
    "databaseURL": ""  # Leave this blank if not using Realtime DB
}

# Initialize Firebase with Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Create a new user (Signup)
def create_user(email, password):
    try:
        auth.create_user_with_email_and_password(email, password)
        return True, "User created successfully"
    except Exception as e:
        print("❌ Error:", e)
        return False, str(e)

# Log in a user (Signin)
def login_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return True, user
    except Exception as e:
        print("❌ Login error:", e)
        return False, str(e)

# In firebase_auth_utils.py

def send_password_reset(email):
    """
    Sends a password reset email with enhanced debugging.
    """
    print(f"\n---  DEBUG: Attempting to send reset email to {email} ---")
    try:
        # This is the line that calls the Firebase service
        auth.send_password_reset_email(email)
    
    except Exception as e:
        # This block runs ONLY if an error occurs
        print(f"❌ DEBUG: An exception was caught!")
        print(f"❌ Reset error type: {type(e).__name__}")
        print(f"❌ Reset error details: {e}")
        return False, str(e)
    
    else:
        # This block runs ONLY if the 'try' block completes with NO errors
        print("✅ DEBUG: The Pyrebase function completed without raising an exception.")
        return True, "Password reset email sent"
        
    finally:
        # This block runs NO MATTER WHAT (success or failure)
        print(f"--- DEBUG: Finished password reset attempt for {email} ---\n")