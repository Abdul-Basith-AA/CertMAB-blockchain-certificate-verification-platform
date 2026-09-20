from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, send_from_directory
import firebase_admin
from firebase_admin import credentials, firestore, auth
from werkzeug.datastructures import FileStorage
import secrets
import hashlib
import os
import threading
import pandas as pd

from datetime import datetime, timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

# --- Import utility functions ---
from firebase_utils import (
    get_admin_dashboard_stats, get_all_certificates,
    get_institution_details, get_company_details, get_student_details,
    get_data_by_hash, record_verification, store_to_firebase,
    get_certificates_by_email, get_institution_certificates,
    get_students_by_institution, get_institution_verification_count,
    create_notification, get_notifications, delete_notifications, get_admin_report_data
)
from email_utils import (
    send_admin_signup_notification, send_approval_email, send_denial_email,
    send_certificate_issuance_email, send_verification_email,
    send_contact_form_email, send_password_reset_email
)
from pinata_utils import upload_to_pinata
from web3_utils import store_on_blockchain, verify_on_blockchain

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a-very-secret-key-that-is-long-and-secure')

# --- Firebase Admin Initialization ---
# Render stores secret files at /etc/secrets/<filename>. This handles both Render and local.
_firebase_key_path = '/etc/secrets/firebase-key1.json' if os.path.exists('/etc/secrets/firebase-key1.json') else 'firebase-key1.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(_firebase_key_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

from firebase_auth_utils import login_user, send_password_reset


def convert_firestore_timestamps(data):
    """
    Recursively searches a dictionary or list for Firestore timestamp objects
    and converts them to simple, JSON-serializable strings.
    """
    if isinstance(data, dict):
        return {key: convert_firestore_timestamps(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_firestore_timestamps(element) for element in data]
    # This specifically targets the class from your debug log
    elif hasattr(data, '__class__') and data.__class__.__name__ == 'DatetimeWithNanoseconds':
        return data.strftime('%Y-%m-%d %H:%M:%S UTC')
    # This is a fallback for standard python datetime objects
    elif isinstance(data, datetime):
        return data.strftime('%Y-%m-%d %H:%M:%S UTC')
    else:
        return data
# ----------------------------
# --- Main and Login Routes ---
# ----------------------------



@app.route('/')
def landing():
    return render_template('home_page.html')

@app.route('/robots.txt')
def robots():
    response = app.make_response("User-agent: *\nAllow: /\nSitemap: https://certificate-verification-blockchain.onrender.com/sitemap.xml")
    response.headers['Content-Type'] = 'text/plain'
    response.headers['X-Robots-Tag'] = 'all'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/sitemap.xml')
def sitemap():
    response = app.make_response(send_from_directory('static', 'sitemap.xml'))
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin1234':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

#--------------------------------
@app.route('/api/admin/reports')
def admin_reports():
    """Provides aggregated data for the admin reports/analytics page."""
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        report_data = get_admin_report_data()
        return jsonify(report_data)
    except Exception as e:
        print(f"Error generating admin report: {e}")
        return jsonify({"error": "An internal server error occurred while generating report data"}), 500


# ---------------------------------
# --- Admin Routes ---
# ---------------------------------
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'admin' not in session: return redirect(url_for('admin_login'))
    stats = get_admin_dashboard_stats()
    all_institutions = [dict(req.to_dict(), email=req.id) for req in db.collection('institution_requests').limit(50).stream()]
    all_companies = [dict(req.to_dict(), email=req.id) for req in db.collection('company_requests').limit(50).stream()]
    all_students = [dict(s.to_dict(), uid=s.id) for s in db.collection('students').limit(50).stream()]
    all_certificates = get_all_certificates(limit=50)
    approved_institutions = [inst for inst in all_institutions if inst.get('approved')]
    institution_names = sorted(list(set(inst.get('institution_name') for inst in approved_institutions if inst.get('institution_name'))))
    pending_institutions = [inst for inst in all_institutions if not inst.get('approved')]
    pending_companies = [comp for comp in all_companies if not comp.get('approved')]
    all_feedback = []
    try:
        feedbacks_ref = db.collection('feedbacks').order_by(
            'timestamp', direction=firestore.Query.DESCENDING
        ).stream()
        
        for doc in feedbacks_ref:
            feedback_data = doc.to_dict()
            feedback_data['id'] = doc.id
            all_feedback.append(feedback_data)
            
    except Exception as e:
        print(f"Error fetching feedback: {e}")
    

    return render_template('admin_dashboard.html', stats=stats,all_feedback=all_feedback, all_institutions=all_institutions, all_companies=all_companies, all_students=all_students, pending_institutions=pending_institutions, pending_companies=pending_companies, all_certificates=all_certificates, institution_names=institution_names)


@app.route('/api/admin/view/<type>/<id>')
def view_details(type, id):
    if 'admin' not in session: return jsonify({"error": "Unauthorized"}), 401
    details = None
    if type == 'institution': details = get_institution_details(id)
    elif type == 'company': details = get_company_details(id)
    elif type == 'student': details = get_student_details(id)
    if details:
        details.pop('password', None)
        return jsonify(details)
    return jsonify({"error": "Not Found"}), 404

# --- Admin Action Routes with Notifications ---
@app.route('/approve-institution/<email>')
def approve_institution(email):
    if 'admin' not in session: return redirect(url_for('admin_login'))
    doc_ref = db.collection('institution_requests').document(email)
    doc_ref.update({'approved': True})
    institution_data = doc_ref.get().to_dict()
    send_approval_email(email, 'Institution', institution_data.get('institution_name', email))
    flash(f"Institution {institution_data.get('institution_name', email)} approved.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/deny-institution/<email>')
def deny_institution(email):
    if 'admin' not in session: return redirect(url_for('admin_login'))
    doc_ref = db.collection('institution_requests').document(email)
    institution_data = doc_ref.get().to_dict()
    send_denial_email(email, 'Institution', institution_data.get('institution_name', email))
    doc_ref.delete()
    flash(f"Institution request for {email} denied and removed.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/approve-company/<email>')
def approve_company(email):
    if 'admin' not in session: return redirect(url_for('admin_login'))
    doc_ref = db.collection('company_requests').document(email)
    doc_ref.update({'approved': True})
    company_data = doc_ref.get().to_dict()
    send_approval_email(email, 'Company', company_data.get('company_name', email))
    flash(f"Company {company_data.get('company_name', email)} approved.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/deny-company/<email>')
def deny_company(email):
    if 'admin' not in session: return redirect(url_for('admin_login'))
    doc_ref = db.collection('company_requests').document(email)
    company_data = doc_ref.get().to_dict()
    send_denial_email(email, 'Company', company_data.get('company_name', email))
    doc_ref.delete()
    flash(f"Company request for {email} denied and removed.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/remove-student/<uid>')
def remove_student_admin(uid):
    if 'admin' not in session: return redirect(url_for('admin_login'))
    try:
        auth.delete_user(uid)
        db.collection('students').document(uid).delete()
        flash('Student removed successfully.', 'success')
    except Exception as e:
        flash(f'Error removing student: {e}', 'error')
    return redirect(url_for('admin_dashboard'))

# ----------------------------
# --- Sign Up Routes ---
# ----------------------------
@app.route('/institution-signup', methods=['GET', 'POST'])
def institution_signup():
    if request.method == 'POST':
        data = {key: request.form[key] for key in request.form}
        data['approved'] = False
        data['registration_certificate_url'] = upload_to_pinata(request.files['registration_certificate'])
        data['accreditation_certificate_url'] = upload_to_pinata(request.files['accreditation_certificate'])
        if 'affiliation_proof' in request.files and request.files['affiliation_proof'].filename != '':
            data['affiliation_proof_url'] = upload_to_pinata(request.files['affiliation_proof'])
        doc_ref = db.collection('institution_requests').document(data['email'])
        if doc_ref.get().exists:
            return render_template('institution_signup.html', error="Request already exists.")
        data['timestamp'] = datetime.now(timezone.utc)
        doc_ref.set(data)
        send_admin_signup_notification('Institution', data)
        create_notification('admin', f"New institution '{data['institution_name']}' requested approval.", '/admin-dashboard')
        return render_template('institution_signup.html', message="Signup request sent to admin for approval.")
    return render_template('institution_signup.html')

@app.route('/company-signup', methods=['GET', 'POST'])
def company_signup():
    if request.method == 'POST':
        data = {key: request.form[key] for key in request.form}
        data['approved'] = False
        data['certificate_incorporation_url'] = upload_to_pinata(request.files['certificate_incorporation'])
        data['business_license_url'] = upload_to_pinata(request.files['business_license'])
        data['gst_certificate_url'] = upload_to_pinata(request.files['gst_certificate'])
       
        doc_ref = db.collection('company_requests').document(data['email'])
        if doc_ref.get().exists:
            return render_template('company_signup.html', error="A request with this email already exists.")
        data['timestamp'] = datetime.now(timezone.utc)
        doc_ref.set(data)
        send_admin_signup_notification('Company', data)
        create_notification('admin', f"New company '{data['company_name']}' requested approval.", '/admin-dashboard')
        return render_template('company_signup.html', message="Signup request sent successfully!")
    return render_template('company_signup.html')

@app.route('/student-signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        email, password, name = request.form['email'], request.form['password'], request.form['name']
        if password != request.form['confirm_password']:
            institutions = [inst.to_dict().get('institution_name') for inst in db.collection('institution_requests').where('approved', '==', True).stream()]
            return render_template('student_signup.html', error='Passwords do not match.', institutions=institutions)
        try:
            user = auth.create_user(email=email, password=password, display_name=name)
            student_data = {key: request.form[key] for key in request.form if key not in ['password', 'confirm_password']}
            student_data['uid'] = user.uid
            student_data['timestamp'] = datetime.now(timezone.utc)
            db.collection('students').document(user.uid).set(student_data)
            create_notification('admin', f"New student '{name}' registered from '{student_data['institution_name']}'.", '/admin-dashboard')
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('student_login'))
        except Exception as e:
            error = 'An account with this email already exists.' if 'EMAIL_EXISTS' in str(e) else 'An error occurred.'
            institutions = [inst.to_dict().get('institution_name') for inst in db.collection('institution_requests').where('approved', '==', True).stream()]
            return render_template('student_signup.html', error=error, institutions=institutions)
    institutions = [inst.to_dict().get('institution_name') for inst in db.collection('institution_requests').where('approved', '==', True).stream()]
    return render_template('student_signup.html', institutions=institutions)

# ----------------------------
# --- User Dashboards & Logins ---
# ----------------------------
@app.route('/institution-login', methods=['GET', 'POST'])
def institution_login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        
        doc_ref = db.collection('institution_requests').document(email)
        doc = doc_ref.get()

        if not doc.exists or not doc.to_dict().get('approved') or doc.to_dict().get('password') != password:
            return render_template('institution_login.html', error="Invalid credentials or not approved.")
        
        data = doc.to_dict()
        session['uid'] = doc.id
        session['user_type'] = 'institution'
        session['name'] = data.get('institution_name', 'Institution')
        session['email'] = email
        session['institution_email'] = email
        
        return redirect(url_for('institution_dashboard'))
        
    return render_template('institution_login.html')

@app.route('/institution-dashboard')
def institution_dashboard():
    if 'institution_email' not in session: return redirect(url_for('institution_login'))
    email = session['institution_email']
    doc = db.collection('institution_requests').document(email).get()
    institution_data = doc.to_dict() if doc.exists else {}
    institution_name = institution_data.get('institution_name', '')
    certificates_raw = get_institution_certificates(email)
    certificates = []
    for cert in certificates_raw:
        if cert.get('timestamp') and hasattr(cert['timestamp'], 'strftime'):
            cert['display_date'] = cert['timestamp'].strftime('%b %d, %Y')
            cert['display_time'] = cert['timestamp'].strftime('%H:%M UTC')
        else:
            cert['display_date'] = 'N/A'; cert['display_time'] = ''
        cert['verifiers_formatted'] = []
        if 'verifiers' in cert and cert['verifiers']:
            sorted_verifiers = sorted(cert['verifiers'], key=lambda v: v.get('timestamp'), reverse=True)
            for verifier in sorted_verifiers:
                if 'timestamp' in verifier and hasattr(verifier['timestamp'], 'strftime'):
                    formatted_time = verifier['timestamp'].strftime('%b %d, %Y at %I:%M %p')
                    cert['verifiers_formatted'].append({'company_name': verifier.get('company_name', 'Unknown'), 'timestamp': formatted_time})
            verifier_names = [v.get('company_name') for v in cert['verifiers_formatted']]
            cert['verifier_tooltip_text'] = ", ".join(verifier_names)
        else:
            cert['verifier_tooltip_text'] = "No verifications yet."
        certificates.append(cert)
    stats = {'total_certificates': len(certificates), 'total_verifications': get_institution_verification_count(email)}
    students = get_students_by_institution(institution_name) if institution_name else []
    return render_template('institution_dashboard.html', institution=institution_data, certificates=certificates, stats=stats, students=students)

@app.route('/company-login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        doc = db.collection('company_requests').document(email).get()
        if not doc.exists or not doc.to_dict().get('approved') or doc.to_dict().get('password') != password:
            return render_template('company_login.html', error="Invalid credentials or not approved.")
        data = doc.to_dict()
        session['uid'] = doc.id
        session['user_type'] = 'company'
        session['name'] = data.get('company_name', 'Company') 
        session['email'] = email
        session['company_email'] = email
        session['company_name'] = data.get('company_name', 'Company')
        return redirect(url_for('company_dashboard'))
    return render_template('company_login.html')

@app.route('/company-dashboard')
def company_dashboard():
    if 'company_email' not in session: return redirect(url_for('company_login'))
    company_email = session.get('company_email')
    company_data = db.collection('company_requests').document(company_email).get().to_dict() or {}
    verified_certs = []
    try:
        for doc in db.collection('verified_status').stream():
            for verifier in doc.to_dict().get('verifiers', []):
                if verifier.get('email') == company_email:
                    cert_data = get_data_by_hash(doc.id)
                    if cert_data:
                        cert_data['verification_date'] = verifier['timestamp'].strftime('%B %d, %Y')
                        cert_data['hash'] = doc.id
                        verified_certs.append(cert_data)
                        break
    except Exception as e:
        print(f"Error fetching verification history: {e}")
    return render_template('company_dashboard.html', company=company_data, verified_certs=verified_certs)

@app.route('/download/<filename>')
def download_template(filename):
    if 'institution_email' not in session: return redirect(url_for('institution_login'))
    allowed_files = ['degree_template.xlsx', 'additional_template.xlsx']
    if filename not in allowed_files:
        return "File not found.", 404
    return send_from_directory('static/templates', filename, as_attachment=True)

@app.route('/api/bulk-upload', methods=['POST'])
def bulk_upload():
    if 'institution_email' not in session:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
    if 'bulk-file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in the request.'}), 400
    
    file = request.files['bulk-file']
    cert_type = request.form.get('cert_type')

    if file.filename == '' or not cert_type:
        return jsonify({'success': False, 'message': 'No file selected or certificate type missing.'}), 400
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload a .xlsx or .csv file.'}), 400

    institution_email = session['institution_email']
    institution_name = db.collection('institution_requests').document(institution_email).get().to_dict().get('institution_name', 'Institution')
    success_count, failure_count, errors, successful_uploads = 0, 0, [], []

    try:
        df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

        for index, row in df.iterrows():
            try:
                data = row.to_dict()
                data['institution_name'] = institution_name
                data['institution_email'] = institution_email
                data['cert_type'] = cert_type

                if 'email' not in data or pd.isna(data['email']): raise ValueError("Missing 'email'")
                image_path = data.get('image')
                if not image_path or pd.isna(image_path): raise ValueError("Missing 'image' column in the spreadsheet")

                # On cloud (Render), local file paths don't work.
                # The 'image' column must be a public URL (e.g., from Google Drive, Imgur, etc.)
                image_url_str = str(image_path).strip()
                if image_url_str.startswith('http://') or image_url_str.startswith('https://'):
                    # It's already a URL — use it directly without uploading to Pinata
                    data['image_url'] = image_url_str
                elif os.path.exists(image_url_str):
                    # Local path (works only when running locally, not on Render)
                    with open(image_url_str, 'rb') as image_file:
                        image_filename = os.path.basename(image_url_str)
                        image_file_for_upload = FileStorage(stream=image_file, filename=image_filename, content_type=f'image/{image_filename.split(".")[-1]}')
                        data['image_url'] = upload_to_pinata(image_file_for_upload)
                else:
                    raise ValueError(f"Image not accessible: '{image_url_str}'. On the cloud, 'image' must be a public URL (https://...).")

                if cert_type == 'degree':
                    concat_str = (f"{data.get('name', '')}{data.get('institute', '')}"
                                  f"{data.get('stream', '')}{data.get('course', '')}"
                                  f"{data.get('email', '')}{data.get('cid', '')}"
                                  f"{data.get('batch', '')}{data.get('student_id', '')}"
                                  f"{data.get('cgpa', '')}{data.get('issue_date', '')}")
                else: # additional
                     concat_str = (f"{data.get('name', '')}{data.get('main_institute', '')}"
                                   f"{data.get('course', '')}{data.get('email', '')}"
                                   f"{data.get('cid', '')}{data.get('start', '')}{data.get('end', '')}")

                hash_val = hashlib.sha256(concat_str.encode()).hexdigest()

                with open(image_path, 'rb') as image_file:
                    image_filename = os.path.basename(image_path)
                    image_file_for_upload = FileStorage(stream=image_file, filename=image_filename, content_type=f'image/{image_filename.split(".")[-1]}')
                    data["image_url"] = upload_to_pinata(image_file_for_upload)
                
                store_to_firebase(hash_val, data)
                # --- ✅ THE FIX IS HERE ---
                store_on_blockchain(hash_val, data) # Pass the entire data dictionary
                send_certificate_issuance_email(data['email'], data['name'], data['course'], institution_name)
                create_notification('admin', f"'{institution_name}' issued a '{data['course']}' cert to '{data['name']}'.", '/admin-dashboard')
                success_count += 1
                successful_uploads.append({"name": data.get('name'), "hash": hash_val})
            except Exception as row_error:
                failure_count += 1
                errors.append(f"Row {index + 2}: {str(row_error)}")
        
        return jsonify({'success': True, 'message': 'Bulk upload completed.', 'success_count': success_count, 'failure_count': failure_count, 'errors': errors, 'successful_uploads': successful_uploads})
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        
        # Use the function from firebase_auth_utils
        success, user_or_error = login_user(email, password)
        if not success:
            return render_template('student_login.html', error="Invalid email or password.")

        students_ref = db.collection('students').where(filter=FieldFilter('email', '==', email)).limit(1).stream()
        student_data = next((s.to_dict() for s in students_ref), None)
        if not student_data: 
            return render_template('student_login.html', error="Student profile not found.")
        
        session['uid'] = student_data['uid']
        session['user_type'] = 'student'
        session['email'] = student_data['email']
        session['name'] = student_data['name']
        session['student_email'] = student_data['email']
        return redirect(url_for('student_dashboard'))
            
    return render_template('student_login.html')

@app.route('/student-dashboard')
def student_dashboard():
    if 'student_email' not in session: return redirect(url_for('student_login'))
    try:
        user = auth.get_user_by_email(session['student_email'])
        student_data = db.collection('students').document(user.uid).get().to_dict() or {}
        certificates_raw = get_certificates_by_email(session['student_email'])
        certificates = []
        for cert in certificates_raw:
            if cert.get('timestamp') and hasattr(cert['timestamp'], 'strftime'):
                cert['display_date'] = cert['timestamp'].strftime('%B %d, %Y')
            else: cert['display_date'] = 'N/A'
            if 'verifiers' in cert and cert['verifiers']:
                cert['verifiers_formatted'] = []
                for verifier in cert['verifiers']:
                    if 'timestamp' in verifier and hasattr(verifier['timestamp'], 'strftime'):
                        formatted_time = verifier['timestamp'].strftime('%b %d, %Y at %I:%M %p')
                        cert['verifiers_formatted'].append({'company_name': verifier.get('company_name', 'Unknown'), 'timestamp': formatted_time})
            certificates.append(cert)
        return render_template('student_dashboard.html', student=student_data, certificates=certificates)
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(url_for('student_login'))
        
# ------------------------------------
# --- Certificate & Verification ---
# ------------------------------------
@app.route('/certificate-type', methods=['GET', 'POST'])
def certificate_type():
    if request.method == 'POST':
        cert_type = request.form['cert_type']
        return redirect(url_for('form', cert_type=cert_type))
    return render_template('certificate_type.html')

@app.route('/form/<cert_type>')
def form(cert_type):
    if 'institution_email' not in session: return redirect(url_for('institution_login'))
    institution_name = db.collection('institution_requests').document(session['institution_email']).get().to_dict().get('institution_name', '')
    template = 'degree_cert.html' if cert_type == 'degree' else 'additional_cert.html'
    return render_template(template, institution_name=institution_name)

@app.route('/upload', methods=['POST'])
def upload():
    if 'institution_email' not in session: 
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401
    
    data = {key: request.form[key] for key in request.form}
    data['institution_email'] = session['institution_email']
    image = request.files['image']
    institution_name = db.collection('institution_requests').document(session['institution_email']).get().to_dict().get('institution_name', 'Institution')
    data['institution_name'] = institution_name

    if data['cert_type'] == 'degree':
        concat_str = (f"{data.get('name', '')}{data.get('institute', '')}"
                      f"{data.get('stream', '')}{data.get('course', '')}"
                      f"{data.get('email', '')}{data.get('cid', '')}"
                      f"{data.get('batch', '')}{data.get('student_id', '')}"
                      f"{data.get('cgpa', '')}{data.get('issue_date', '')}")
    else: # For 'additional' certificates
        concat_str = (f"{data.get('name', '')}{data.get('main_institute', '')}"
                      f"{data.get('course', '')}{data.get('email', '')}"
                      f"{data.get('cid', '')}{data.get('start', '')}{data.get('end', '')}")

    hash_val = hashlib.sha256(concat_str.encode()).hexdigest()
    
    try:
        data["image_url"] = upload_to_pinata(image)
        store_to_firebase(hash_val, data)
        store_on_blockchain(hash_val, data)

        # ✅ Send email & notification in a background thread so the response
        # is returned immediately. Render blocks SMTP, so this prevents a
        # gunicorn worker timeout from crashing the upload.
        def send_notifications_async(app_ctx, email, name, course, inst_name):
            with app_ctx:
                try:
                    send_certificate_issuance_email(email, name, course, inst_name)
                    create_notification('admin', f"'{inst_name}' issued a '{course}' certificate to '{name}'.", '/admin-dashboard')
                except Exception as e:
                    print(f"Background notification error: {e}")

        import threading
        threading.Thread(
            target=send_notifications_async,
            args=(app.app_context(), data['email'], data['name'], data['course'], institution_name),
            daemon=True
        ).start()

        return jsonify({'success': True, 'hash': hash_val, 'message': 'Certificate uploaded!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {e}'}), 500

@app.route('/verify', methods=['POST'])
def verify():
    if "company_email" not in session: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    hash_val = request.form['hash']

    # Step 1: Check if certificate data exists in Firebase
    data = get_data_by_hash(hash_val)
    if not data:
        return jsonify({'success': False, 'message': 'Certificate hash not found in our records!'})

    # Step 2: ✅ THE REAL BLOCKCHAIN CHECK — Verify the hash actually exists on Sepolia
    # This is the core security feature: it catches any tampering with Firebase data.
    blockchain_verified = verify_on_blockchain(hash_val)
    if not blockchain_verified:
        return jsonify({
            'success': False,
            'message': '⚠️ SECURITY ALERT: This certificate hash was found in our database but DOES NOT exist on the blockchain. It may have been tampered with!'
        })

    # Step 3: Both checks passed — record the verification and notify parties
    company_name = session.get('company_name', 'A Company')
    record_verification(hash_val, company_name, session['company_email'])

    # ✅ Send all emails and notifications in a background thread
    def send_verify_notifications_async(app_ctx, cert_data, co_name, co_email):
        with app_ctx:
            try:
                send_verification_email(cert_data['email'], cert_data['name'], co_name)
                try:
                    student_user = auth.get_user_by_email(cert_data['email'])
                    create_notification(student_user.uid, f"Your '{cert_data.get('course')}' certificate was verified by {co_name}.", '/student-dashboard')
                except Exception as e:
                    print(f"Could not create student notification: {e}")
                create_notification('admin', f"'{co_name}' verified a certificate for '{cert_data['name']}'.", '/admin-dashboard')
            except Exception as e:
                print(f"Background verify notification error: {e}")

    import threading
    threading.Thread(
        target=send_verify_notifications_async,
        args=(app.app_context(), data, company_name, session['company_email']),
        daemon=True
    ).start()

    return jsonify({'success': True, 'data': data})



# ---------------------------------------------
# --- Notification API Routes & Logout ---
# ---------------------------------------------
@app.route('/api/notifications')
def api_get_notifications():
    user_id = None
    if 'admin' in session: user_id = 'admin'
    elif 'student_email' in session:
        try: user_id = auth.get_user_by_email(session['student_email']).uid
        except: return jsonify({"error": "User not found"}), 404
    if not user_id: return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_notifications(user_id))

@app.route('/api/notifications/delete-viewed', methods=['POST'])
def api_delete_viewed():
    user_id = None
    if 'admin' in session: user_id = 'admin'
    elif 'student_email' in session:
        try: user_id = auth.get_user_by_email(session['student_email']).uid
        except: return jsonify({"error": "User not found"}), 404
    if not user_id: return jsonify({"error": "Unauthorized"}), 401
    if delete_notifications(user_id): return jsonify({"success": True})
    return jsonify({"success": False}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')
    
@app.route('/api/remove-student', methods=['POST'])
def remove_student():
    if 'institution_email' not in session: return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    uid = request.json.get('uid')
    if not uid: return jsonify({'success': False, 'message': 'Student UID is missing.'}), 400
    try:
        auth.delete_user(uid)
        db.collection('students').document(uid).delete()
        flash('Student removed successfully.', 'success')
        return jsonify({'success': True, 'message': 'Student removed successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {e}'}), 500
        
@app.route('/api/dashboard-stats')
def dashboard_stats():
    if 'institution_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    institution_email = session['institution_email']
    degree_certs_query = db.collection('degree_certificates').where('institution_email', '==', institution_email).stream()
    additional_certs_query = db.collection('additional_certificates').where('institution_email', '==', institution_email).stream()
    
    total = len(list(degree_certs_query)) + len(list(additional_certs_query))
    return jsonify({'total_certificates_issued': total})

@app.route('/api/submit-feedback', methods=['POST'])
def submit_feedback():
    user_type = session.get('user_type')
    sender_uid = session.get('uid')
    sender_email = session.get('email')
    sender_name = session.get('name')

    if not all([user_type, sender_uid, sender_email, sender_name]):
        return jsonify({'error': 'User not authenticated or session incomplete'}), 401

    try:
        data = request.get_json()
        feedback_data = {
            'sender_uid': sender_uid, 'sender_email': sender_email,
            'sender_name': sender_name, 'sender_type': user_type,
            'category': data.get('category'), 'subject': data.get('subject'),
            'message': data.get('message'), 'timestamp': datetime.now(timezone.utc), 'read': False
        }
        db.collection('feedbacks').add(feedback_data)
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'}), 200
    except Exception as e:
        print(f"An error occurred in submit_feedback: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# PASTE THIS DEBUG VERSION INTO app.py
# --- Password Reset Routes ---

@app.route('/forgot-password/<user_type>', methods=['GET', 'POST'])
def forgot_password(user_type):
    if request.method == 'POST':
        email = request.form['email']
        
        # --- Handle Students via Firebase ---
        if user_type == 'student':
            # Use the function from firebase_auth_utils
            success, message = send_password_reset(email)
            if success:
                flash('A password reset link has been sent to your email.', 'success')
            else:
                flash('Failed to send reset email. Please check if the email is registered.', 'error')
            return redirect(url_for('student_login'))

        # --- Handle Institutions & Companies with Custom Tokens ---
        collection_name = 'institution_requests' if user_type == 'institution' else 'company_requests'
        doc_ref = db.collection(collection_name).document(email)
        
        if not doc_ref.get().exists:
            flash('This email is not registered with us.', 'error')
            return render_template('forgot_password.html', user_type=user_type)

        token = secrets.token_urlsafe(20)
        expiry = datetime.now(timezone.utc) + timedelta(hours=1) # Token valid for 1 hour
        
        # Store token in a new collection
        db.collection('password_reset_tokens').document(token).set({
            'email': email,
            'user_type': user_type,
            'expires_at': expiry
        })

        send_password_reset_email(email, token)

        
        flash('A password reset link has been sent to your email.', 'success')
        return redirect(url_for(f'{user_type}_login'))

    return render_template('forgot_password.html', user_type=user_type)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_ref = db.collection('password_reset_tokens').document(token)
    token_doc = token_ref.get()

    if not token_doc.exists or datetime.now(timezone.utc) > token_doc.to_dict()['expires_at']:
        flash('This password reset link is invalid or has expired.', 'error')
        return redirect(url_for('landing'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('reset_password.html', token=token, error='Passwords do not match.')

        token_data = token_doc.to_dict()
        email = token_data['email']
        user_type = token_data['user_type']
        
        

        collection_name = 'institution_requests' if user_type == 'institution' else 'company_requests'
        db.collection(collection_name).document(email).update({'password': password})

        # Invalidate the token
        token_ref.delete()

        flash('Your password has been updated successfully. Please log in.', 'success')
        return redirect(url_for(f'{user_type}_login'))

    return render_template('reset_password.html', token=token)


@app.route('/contact-us', methods=['POST'])
def contact_us():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not all([name, email, subject, message]):
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('landing') + '#contact')
        
        # Send the email using the new utility function
        send_contact_form_email(name, email, subject, message)
        
        flash('Thank you for your message! We will get back to you shortly.', 'success')
    except Exception as e:
        print(f"Error sending contact form email: {e}")
        flash('Sorry, there was an error sending your message. Please try again later.', 'error')

    return redirect(url_for('landing') + '#contact')




if __name__ == '__main__':
    # debug=False is important for production safety.
    # On Render, gunicorn is used instead of this block.
    app.run(debug=False, use_reloader=False)
