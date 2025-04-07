import os
from flask import Flask, request, jsonify
import requests
import json
import base64
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from edit_pdf import ocr_png_bytes  # Import the OCR function
from werkzeug.utils import secure_filename
from io import BytesIO
import fitz
import threading   # Import threading
import time        # Import time for sleeping

load_dotenv(override=True)

app = Flask(__name__)

# Load the Firebase service account key from environment variable
firebase_service_account_key = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY"))
forth_api_key = json.loads(os.getenv("FORTH_API_KEY"))

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_service_account_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

def combine_pdfs(pdf_pages):
    """
    Combine multiple PDF pages into a single PDF document using PyMuPDF.
    """
    combined_pdf = fitz.open()

    for pdf_page in pdf_pages:
        pdf_document = fitz.open(stream=pdf_page, filetype="pdf")
        for page_num in range(len(pdf_document)):
            combined_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        pdf_document.close()

    output_stream = BytesIO()
    combined_pdf.save(output_stream)
    combined_pdf.close()
    return output_stream.getvalue()

common_doc_types = {
    "pdf": "application/pdf",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4"
}

# Function to authenticate and get API key
def forthCRM_authtoken():
    f = forth_api_key
    response = requests.post(
        'https://api.forthcrm.com/v1/auth/token', 
        headers={"Accept": "application/json"}, 
        json={"client_id": f["client_id"], "client_secret": f["client_secret"]}
    ).json()
    api_key = None
    if response['status']['code'] == 200:
        api_key = response['response']['api_key']
    return api_key

# Helper function to process the uploaded document after a delay
def process_uploaded_doc(contact_id, doc_id, uid):
    time.sleep(5)  # Wait for 5 seconds before checking Firestore
    user_doc = db.collection('users_test').document(uid).get()
    if not user_doc.exists:
        return  # Document not found; exit thread
    doc_info = user_doc.get('doc_info')
    if not doc_info:
        return  # No doc_info field; exit thread
    for item in doc_info:
        if item.get('docid') == str(doc_id):
            # If found, check if 'isGeneral' is False
            if not item.get('isGeneral'):
                changeDocType(contact_id, doc_id, 10)
            else:
                changeDocType(contact_id, doc_id, 1)
            return  # Exit after processing
    return  # Matching element not found; exit thread

# Modified uploadDoc function that now accepts uid and spawns a background thread
def uploadDoc(contact_id, file_name, file_content, is_general,uid=None):
    api_key = forthCRM_authtoken()
    content_type = common_doc_types[file_name.split('.')[-1]]
    doc_type_id = 1 if is_general == True else 10
    print(f"Doc type ID: {doc_type_id}")
    print(f"is_general: {is_general}")

    headers = {
        "Accept": "application/json",
        "Api-Key": api_key
    }

    json_body = [
        {
            "file_content": file_content,
            "file_name": file_name,
            "doc_type": doc_type_id,
            "content_type": content_type
        }
    ]

    response = requests.post(
        f'https://api.forthcrm.com/v1/contacts/{contact_id}/documents/upload',
        headers=headers,
        json=json_body
    ).json()

    # Extract the document ID from the response
    doc_id = response.get('response')[0].get('doc_id')

    # If a doc_id was found and uid is provided, spawn a thread to process it
    if doc_id and uid:
        threading.Thread(target=process_uploaded_doc, args=(contact_id, doc_id, uid), daemon=True).start()

    return response

# New function to get document by ID
def getDoc(contact_id, doc_id):
    api_key = forthCRM_authtoken()
    headers = {
        "Accept": "application/json",
        "Api-Key": api_key
    }
    response = requests.get(
        f'https://api.centrexsoftware.com/v1/contacts/{contact_id}/documents/{doc_id}/uploaded',
        headers=headers
    )
    return response.json()

def deleteDoc(contact_id, doc_id):
    api_key = forthCRM_authtoken()
    headers = {
        "Accept": "application/json",
        "Api-Key": api_key
    }
    response = requests.delete(
        f'https://api.centrexsoftware.com/v1/contacts/{contact_id}/documents/{doc_id}',
        headers=headers
    )
    print('in delete doc')
    print(response.json())
    return response.json()

def renameDoc(contact_id, doc_id, new_name):
    api_key = forthCRM_authtoken()
    headers = {
        "Accept": "application/json",
        "Api-Key": api_key
    }
    json_body = {
        "file_name": new_name
    }
    response = requests.put(
        f'https://api.centrexsoftware.com/v1/contacts/{contact_id}/documents/{doc_id}',
        headers=headers,
        json=json_body
    )
    return response.json()

def changeDocType(contact_id, doc_id, new_doc_type):
    api_key = forthCRM_authtoken()
    headers = {
        "Accept": "application/json",
        "Api-Key": api_key
    }
    json_body = {
        "doc_type": new_doc_type
    }
    response = requests.put(
        f'https://api.centrexsoftware.com/v1/contacts/{contact_id}/documents/{doc_id}',
        headers=headers,
        json=json_body
    )
    return response.json()

# Function to verify Firebase ID token
def verify_firebase_token(token):
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        return None

# Function to check user and contact id in Firestore
def check_user_contact(uid, contact_id):
    try:
        user_doc = db.collection('users_test').document(uid).get()
        if user_doc.exists and user_doc.get('contact_id') == contact_id:
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/rename-doc', methods=['POST'])
def rename_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_id = data.get('doc_id')
    auth_token = data.get('auth_token')
    new_name = data.get('new_name')

    if not contact_id or not file_id or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": f"Contact ID does not match user {uid} {contact_id}"}), 403

    result = renameDoc(contact_id, file_id, new_name)
    print(result)
    return jsonify(result)

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_documents():
    contact_id = request.form.get('contact_id')
    auth_token = request.form.get('auth_token')
    fileName = request.form.get('filename')
    is_general = request.form.get('isGeneral')
    is_general = True if is_general==None else is_general
    
    print(fileName)

    if not contact_id or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": "Contact ID does not match user"}), 403

    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    if not files or len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    all_pdf_pages = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_bytes = file.read()
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
                pdf_bytes = ocr_png_bytes(file_bytes)
                all_pdf_pages.append(pdf_bytes)

    combined_pdf = combine_pdfs(all_pdf_pages)
    combined_pdf_base64 = base64.b64encode(combined_pdf).decode('utf-8')
    result = uploadDoc(contact_id, fileName, combined_pdf_base64, is_general,uid)
    return jsonify(result)

@app.route('/delete-doc', methods=['POST'])
def delete_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_id = data.get('doc_id')
    auth_token = data.get('auth_token')

    if not contact_id or not file_id or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": f"Contact ID does not match user {uid} {contact_id}"}), 403

    result = deleteDoc(contact_id, file_id)
    print(result)
    return jsonify(result)

@app.route('/upload', methods=['POST'])
def upload_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_name = data.get('file_name')
    file_content = data.get('file_content')
    auth_token = data.get('auth_token')
    is_general = data.get('isGeneral')
    is_general = True if is_general==None else is_general

    if not contact_id or not file_name or not file_content or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": "Contact ID does not match user"}), 403

    result = uploadDoc(contact_id, file_name, file_content, is_general,uid)
    return jsonify(result)

@app.route('/get_doc', methods=['POST'])
def get_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_id = data.get('doc_id')
    auth_token = data.get('auth_token')

    if not contact_id or not file_id or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": f"Contact ID does not match user {uid} {contact_id}"}), 403

    result = getDoc(contact_id, file_id)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)