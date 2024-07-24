from flask import Flask, request, jsonify
import base64
import requests
import json 

app = Flask(__name__)

# Function to convert file content to base64
def convert_to_base64(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

# Function to authenticate and get API key
def forthCRM_authtoken():
    f = None
    with open('forthCRM_credentials.json', 'r') as file: f = json.loads(file.read())
    response = requests.post('https://api.forthcrm.com/v1/auth/token', headers = {"Accept":"application/json"}, json = {"client_id": f"{f['client_id']}","client_secret": f"{f['client_secret']}"}).json()
    api_key = None
    if response['status']['code'] == 200: api_key = response['response']['api_key']
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

# Flask route to handle POST request
@app.route('/upload', methods=['POST'])
def upload_document():
    data = request.get_json()
    contact_id = data.get('contact_id')
    file_name = data.get('file_name')
    file_content = data.get('file_content')  # Expecting the file content to be in base64 format
    auth_token = data.get('auth_token')

    if not contact_id or not file_name or not file_content or not auth_token:
        return jsonify({"error": "Missing required parameters"}), 400

    result = uploadDoc(contact_id, file_name, file_content)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

