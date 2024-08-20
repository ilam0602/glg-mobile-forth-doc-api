import os
from flask import Flask, request, jsonify
import requests
import json
import base64
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore

load_dotenv()

app = Flask(__name__)

# Load the Firebase service account key from environment variable
firebase_service_account_key = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY"))
forth_api_key = json.loads(os.getenv("FORTH_API_KEY"))

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_service_account_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to convert file content to base64
def convert_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

# Function to authenticate and get API key
def forthCRM_authtoken():
    f = forth_api_key
    response = requests.post(
        'https://api.forthcrm.com/v1/auth/token', 
        headers={"Accept": "application/json"}, 
        json={"client_id": f"{f['client_id']}", "client_secret": f"{f['client_secret']}"}
    ).json()
    api_key = None
    if response['status']['code'] == 200:
        api_key = response['response']['api_key']
    return api_key

common_doc_types = {
    "pdf": "application/pdf",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4"
}

# Main upload function
def uploadDoc(contact_id, file_name, file_content):
    api_key = forthCRM_authtoken()
    content_type = common_doc_types[file_name.split('.')[-1]]
    doc_type_id = 1

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
    )
    return response.json()

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

# Function to verify Firebase ID token
def verify_firebase_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        return None

# Function to check user and contact id in Firestore
def check_user_contact(uid, contact_id):
    try:
        users_ref = db.collection('users')
        query = users_ref.where('uid', '==', uid).stream()
        for user in query:
            user_data = user.to_dict()
            if user_data.get('contact_id') == contact_id:
                return True
        return False
    except Exception as e:
        return False

# Flask route to handle POST request for document upload
@app.route('/upload', methods=['POST'])
def upload_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_name = data.get('file_name')
    file_content = data.get('file_content')  # Expecting the file content to be in base64 format
    auth_token = data.get('auth_token')

    if not contact_id or not file_name or not file_content or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    decoded_token = verify_firebase_token(auth_token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired Firebase token"}), 401

    uid = decoded_token.get('uid')
    if not check_user_contact(uid, contact_id):
        return jsonify({"error": f"Contact ID does not match user"}), 403

    #TODO REMOVE HARD CODE
    # result = uploadDoc(contact_id, file_name, file_content)
    result = uploadDoc("938394902", file_name, file_content)
    return jsonify(result)

# Flask route to handle POST request for document retrieval
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

    #TODO REMOVE HARD CODE
    # result = getDoc(contact_id, file_id)
    result = getDoc("938394902", file_id)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=8080)