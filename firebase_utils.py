import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter
import pandas as pd
from collections import defaultdict

# Initialize Firebase app (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key1.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------------------------------------
# --- Notification Functions ---
# ---------------------------------------------

def create_notification(recipient_id, message, link=None):
    """
    Creates a new notification document in Firestore.
    recipient_id can be 'admin', a student's UID, etc.
    """
    try:
        db.collection('notifications').add({
            'recipient_id': recipient_id,
            'message': message,
            'link': link,
            'read': False,
            'timestamp': datetime.now(timezone.utc)
        })
        print(f"✅ Notification created for {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating notification: {e}")

def get_notifications(recipient_id):
    """
    Retrieves all notifications for a specific recipient, sorted by timestamp.
    NOTE: This query requires a composite index in Firestore.
    """
    try:
        notifications_ref = db.collection('notifications').where('recipient_id', '==', recipient_id).order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        notifications = []
        for notif in notifications_ref:
            data = notif.to_dict()
            data['id'] = notif.id
            # Convert timestamp to ISO 8601 format string for JSON serialization
            if isinstance(data.get('timestamp'), datetime):
                data['timestamp'] = data['timestamp'].isoformat()
            notifications.append(data)
        return notifications
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        return []

def delete_notifications(recipient_id):
    """
    Deletes all notifications for a specific recipient.
    """
    try:
        notifications_ref = db.collection('notifications').where('recipient_id', '==', recipient_id).stream()
        for notif in notifications_ref:
            notif.reference.delete()
        print(f"✅ Deleted notifications for {recipient_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting notifications: {e}")
        return False

# ---------------------------------------------
# --- Admin & Dashboard Functions ---
# ---------------------------------------------

def get_all_certificates(limit=None):
    """Fetches all degree and additional certificates from the database."""
    all_certs = []

    try:
        degree_query = db.collection('degree_certificates').order_by('timestamp', direction=firestore.Query.DESCENDING)
        if limit:
            degree_query = degree_query.limit(limit)
        
        degree_docs = degree_query.stream()
        for doc in degree_docs:
            data = doc.to_dict()
            data['id'] = doc.id
            data['cert_type'] = 'Degree'
            data['institution_name'] = data.get('institute')
            all_certs.append(data)
    except Exception as e:
        print(f"Error fetching degree certificates: {e}")

    try:
        additional_query = db.collection('additional_certificates').order_by('timestamp', direction=firestore.Query.DESCENDING)
        if limit:
            additional_query = additional_query.limit(limit)

        additional_docs = additional_query.stream()
        for doc in additional_docs:
            data = doc.to_dict()
            data['id'] = doc.id
            data['cert_type'] = 'Additional'
            data['institution_name'] = data.get('main_institute')
            all_certs.append(data)
    except Exception as e:
        print(f"Error fetching additional certificates: {e}")
    
    # Sort the combined list of limited results
    fallback_date = datetime.min.replace(tzinfo=timezone.utc)
    all_certs.sort(key=lambda x: x.get('timestamp', fallback_date), reverse=True)
    
    # If a limit was applied, we only need to return the limited number of items
    if limit:
        return all_certs[:limit]

    return all_certs

def get_admin_dashboard_stats():
    """Aggregates all key statistics for the main admin dashboard view."""
    try:
        institutions_count = db.collection('institution_requests').count().get()[0][0].value
        companies_count = db.collection('company_requests').count().get()[0][0].value
        students_count = db.collection('students').count().get()[0][0].value
        degree_certs_count = db.collection('degree_certificates').count().get()[0][0].value
        additional_certs_count = db.collection('additional_certificates').count().get()[0][0].value
        total_certs = degree_certs_count + additional_certs_count

        pending_inst = db.collection('institution_requests').where('approved', '==', False).count().get()[0][0].value
        pending_comp = db.collection('company_requests').where('approved', '==', False).count().get()[0][0].value
        
        return {
            'institutions': institutions_count,
            'companies': companies_count,
            'students': students_count,
            'certificates': total_certs,
            'pending_approvals': pending_inst + pending_comp
        }
    except Exception as e:
        print(f"Error getting admin dashboard stats: {e}")
        return {'institutions': 0, 'companies': 0, 'students': 0, 'certificates': 0, 'pending_approvals': 0}

def get_institution_details(email):
    """Gets full details for a single institution, including their students and certs."""
    inst_doc = db.collection('institution_requests').document(email).get()
    if not inst_doc.exists: return None
    
    details = inst_doc.to_dict()
    inst_name = details.get('institution_name', '')
    
    details['students'] = []
    if inst_name:
        student_query = db.collection('students').where('institution_name', '==', inst_name).stream()
        details['students'] = [s.to_dict() for s in student_query]

    degree_certs = db.collection('degree_certificates').where('institution_email', '==', email).stream()
    additional_certs = db.collection('additional_certificates').where('institution_email', '==', email).stream()
    details['certificates'] = [c.to_dict() for c in list(degree_certs) + list(additional_certs)]
    return details

def get_company_details(email):
    """Gets full details for a company, including their verification history."""
    comp_doc = db.collection('company_requests').document(email).get()
    if not comp_doc.exists: return None
    
    details = comp_doc.to_dict()
    history = []
    #all_verifications = db.collection('verified_status').stream()
    verified_docs_query = db.collection('verified_status').where('verifier_emails', 'array_contains', email).stream()
    for verification in verified_docs_query:
        verif_data = verification.to_dict()
        for verifier in verif_data.get('verifiers', []):
            if verifier.get('email') == email:
                cert_hash = verification.id
                cert_details = get_data_by_hash(cert_hash) or {}
                history.append({
                    'verified_at': verifier['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'certificate_hash': cert_hash,
                    'student_name': cert_details.get('name'),
                    'course': cert_details.get('course')
                })
    details['verification_history'] = sorted(history, key=lambda x: x['verified_at'], reverse=True)
    return details

def get_student_details(uid):
    """Gets full details for a student, including all their certificates."""
    student_doc = db.collection('students').document(uid).get()
    if not student_doc.exists: return None
        
    details = student_doc.to_dict()
    email = details.get('email')

    degree_certs = db.collection('degree_certificates').where('email', '==', email).stream()
    additional_certs = db.collection('additional_certificates').where('email', '==', email).stream()
    details['certificates'] = [c.to_dict() for c in list(degree_certs) + list(additional_certs)]
    return details

# ---------------------------------------------
# --- Core Certificate & Verification Functions ---
# ---------------------------------------------

def store_to_firebase(hash_val, data):
    data['timestamp'] = firestore.SERVER_TIMESTAMP
    data['status'] = 'verified'
    
    collection_name = 'degree_certificates' if data.get('cert_type', '').lower() == 'degree' else 'additional_certificates'
    db.collection(collection_name).document(hash_val).set(data)
    
    db.collection('verified_status').document(hash_val).set({'count': 0, 'verifiers': []})

def record_verification(hash_val, company_name, company_email):
    doc_ref = db.collection('verified_status').document(hash_val)
    verifier_data = {
        'company_name': company_name,
        'email': company_email,
        'timestamp': datetime.now(timezone.utc)
    }
    doc_ref.update({
        'count': firestore.Increment(1),
        'verifiers': firestore.ArrayUnion([verifier_data]),
        'verifier_emails': firestore.ArrayUnion([company_email])
    })

def get_data_by_hash(hash_val):
    try:
        degree_doc = db.collection('degree_certificates').document(hash_val).get()
        if degree_doc.exists: return degree_doc.to_dict()

        add_doc = db.collection('additional_certificates').document(hash_val).get()
        if add_doc.exists: return add_doc.to_dict()
        return None
    except Exception as e:
        print(f"❌ Error retrieving certificate by hash: {e}")
        return None

def get_institution_certificates(institution_email):
    """Retrieve all certificates for an institution, including verification data."""
    try:
        certificates = []
        degree_docs = db.collection('degree_certificates').where('institution_email', '==', institution_email).stream()
        add_docs = db.collection('additional_certificates').where('institution_email', '==', institution_email).stream()
        
        for doc in list(degree_docs) + list(add_docs):
            data = doc.to_dict()
            data['id'] = doc.id
            verified_doc = db.collection('verified_status').document(doc.id).get()
            verified_data = verified_doc.to_dict() if verified_doc.exists else {}
            data['verification_count'] = verified_data.get('count', 0)
            data['verifiers'] = verified_data.get('verifiers', [])
            certificates.append(data)
        return certificates
    except Exception as e:
        print(f"Error fetching certificates for institution: {e}")
        return []

def get_certificates_by_email(student_email):
    """Retrieve all certificates for a student, including verification history."""
    try:
        certificates = []
        degree_query = db.collection('degree_certificates').where('email', '==', student_email).stream()
        additional_query = db.collection('additional_certificates').where('email', '==', student_email).stream()
        
        for doc in list(degree_query) + list(additional_query):
            data = doc.to_dict()
            data['hash'] = doc.id
            verified_doc = db.collection('verified_status').document(doc.id).get()
            data['verifiers'] = verified_doc.to_dict().get('verifiers', []) if verified_doc.exists else []
            certificates.append(data)
        return certificates
    except Exception as e:
        print(f"❌ Error fetching certificates for {student_email}: {e}")
        return []

def get_students_by_institution(institution_name):
    try:
        students_query = db.collection('students').where('institution_name', '==', institution_name).stream()
        return [dict(doc.to_dict(), uid=doc.id) for doc in students_query]
    except Exception as e:
        print(f"❌ Error fetching students for {institution_name}: {e}")
        return []

def get_institution_verification_count(institution_email):
    """Calculates the total verification count for an institution's certificates."""
    try:
        issued_hashes = [cert['id'] for cert in get_institution_certificates(institution_email)]
        if not issued_hashes: return 0
            
        total_verifications = 0
        for i in range(0, len(issued_hashes), 30):
            batch_hashes = issued_hashes[i:i+30]
            if not batch_hashes: continue
            
            verified_docs = db.collection('verified_status').where('__name__', 'in', batch_hashes).stream()
            for doc in verified_docs:
                total_verifications += doc.to_dict().get('count', 0)
        return total_verifications
    except Exception as e:
        print(f"❌ Error calculating verification count for {institution_email}: {e}")
        return 0

def get_all_discrepancies():
    """
    Retrieves all data discrepancies.
    This new version is more robust and less dependent on complex indexes.
    """
    try:
        all_docs = db.collection('discrepancies').stream()
        
        unresolved = []
        resolved = []

        for doc in all_docs:
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Convert timestamp to a readable string for display
            if isinstance(data.get('timestamp'), datetime):
                data['timestamp_str'] = data['timestamp'].strftime('%b %d, %Y at %I:%M %p UTC')
            
            if data.get('status') == 'unresolved':
                unresolved.append(data)
            elif data.get('status') == 'resolved':
                resolved.append(data)
        
        # Sort each list by timestamp in Python (most recent first)
        fallback_date = datetime.min.replace(tzinfo=timezone.utc)
        unresolved.sort(key=lambda x: x.get('timestamp', fallback_date), reverse=True)
        resolved.sort(key=lambda x: x.get('timestamp', fallback_date), reverse=True)
        
        # Return unresolved issues first, then resolved ones
        print(f"✅ Found {len(unresolved) + len(resolved)} total discrepancies in Firestore.")
        return unresolved + resolved

    except Exception as e:
        print(f"❌ Error getting discrepancies: {e}")
        return []

def update_discrepancy_status(doc_id, new_status):
    """Updates the status of a discrepancy document (e.g., to 'resolved')."""
    try:
        doc_ref = db.collection('discrepancies').document(doc_id)
        doc_ref.update({'status': new_status})
        print(f"✅ Updated discrepancy {doc_id} to {new_status}")
        return True
    except Exception as e:
        print(f"❌ Error updating discrepancy status: {e}")
        return False


def get_admin_report_data():
    """Aggregates complex data for the admin reports dashboard."""
    try:
        # 1. Fetch all necessary data
        certs_ref = get_all_certificates()
        inst_ref = list(db.collection('institution_requests').stream())
        comp_ref = list(db.collection('company_requests').stream())
        stud_ref = list(db.collection('students').stream())

        # 2. Process Time Series Data
        all_docs = certs_ref + [d.to_dict() for d in inst_ref] + [d.to_dict() for d in comp_ref] + [d.to_dict() for d in stud_ref]
        
        data_with_dates = []
        for doc in all_docs:
            if doc and doc.get('timestamp') and isinstance(doc.get('timestamp'), datetime):
                # Determine the type of record
                doc_type = 'certificate'
                if 'institution_name' in doc and 'approved' in doc:
                    doc_type = 'registration'
                elif 'company_name' in doc and 'approved' in doc:
                    doc_type = 'registration'
                elif 'uid' in doc: # It's a student registration
                    doc_type = 'registration'
                
                data_with_dates.append({'date': doc['timestamp'].date(), 'type': doc_type})

        time_series_data = {"dates": [], "certificates": [], "registrations": []}
        if data_with_dates:
            df = pd.DataFrame(data_with_dates)
            df['date'] = pd.to_datetime(df['date'])
            # Group by day and type, then unstack to get columns for each type
            daily_counts = df.groupby([df['date'].dt.to_period('D'), 'type']).size().unstack(fill_value=0)
            # Resample to fill in missing days with 0
            daily_counts = daily_counts.resample('D').sum().fillna(0)
            daily_counts.index = daily_counts.index.to_timestamp()

            if 'certificate' not in daily_counts: daily_counts['certificate'] = 0
            if 'registration' not in daily_counts: daily_counts['registration'] = 0

            time_series_data = {
                "dates": daily_counts.index.strftime('%Y-%m-%d').tolist(),
                "certificates": daily_counts['certificate'].tolist(),
                "registrations": daily_counts['registration'].tolist()
            }

        # 3. Process Distribution Data
        cert_types = [c.get('cert_type', 'Unknown') for c in certs_ref]
        cert_type_dist = { "Degree": cert_types.count('Degree'), "Additional": cert_types.count('Additional') }
        
        user_type_dist = { "Institutions": len(inst_ref), "Companies": len(comp_ref), "Students": len(stud_ref) }

        # 4. Process Top 5 Data
        inst_certs_count = defaultdict(int)
        for cert in certs_ref:
            if cert.get('institution_name'):
                inst_certs_count[cert['institution_name']] += 1
        
        top_inst = sorted(inst_certs_count.items(), key=lambda item: item[1], reverse=True)[:5]
        top_institutions = [{"name": name, "count": count} for name, count in top_inst]

        comp_verifs_count = defaultdict(int)
        verifs_ref = db.collection('verified_status').stream()
        for doc in verifs_ref:
            verifiers = doc.to_dict().get('verifiers', [])
            for verifier in verifiers:
                 if verifier.get('company_name'):
                     comp_verifs_count[verifier['company_name']] += 1
        
        top_comp = sorted(comp_verifs_count.items(), key=lambda item: item[1], reverse=True)[:5]
        top_companies = [{"name": name, "count": count} for name, count in top_comp]

        return {
            "time_series": time_series_data,
            "cert_type_distribution": cert_type_dist,
            "user_type_distribution": user_type_dist,
            "top_institutions": top_institutions,
            "top_companies": top_companies,
        }
    except Exception as e:
        print(f"Error getting admin report data: {e}")
        return {}