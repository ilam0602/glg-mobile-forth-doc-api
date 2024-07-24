import requests
import base64
import json

def forthCRM_authtoken():
    f = None
    with open('forthCRM_credentials.json', 'r') as file: f = json.loads(file.read())
    response = requests.post('https://api.forthcrm.com/v1/auth/token', headers = {"Accept":"application/json"}, json = {"client_id": f"{f['client_id']}","client_secret": f"{f['client_secret']}"}).json()
    api_key = None
    if response['status']['code'] == 200: api_key = response['response']['api_key']
    return api_key

def convert_to_base64(file_path):
    encoded_content = None
    with open(file_path, 'rb') as f: encoded_content = base64.b64encode(f.read()).decode()
    return encoded_content

#https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
common_doc_types = {
    "text": "text/plain",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpeg": "image/jpeg",#also jpg
    "mp3": "audio/mpeg",
    "mp4": "video/mp4"
}

api_key = forthCRM_authtoken()
content_type = common_doc_types['pdf']

contact_id = 938394902
file_name = 'test_doc_07_03_01.pdf'
file_content = convert_to_base64(f'{file_name}')#path to file. left as file_name since script is in the same directory as file.
print(f'file content:{file_content}')

def uploadDoc(contact_id,file_name,file_content):
	doc_type_id = 1

	headers = {
	    "Accept":"application/json", 
	    "Api-Key": f"{api_key}"
	    }

	json_body = [
		{
		"file_content": f"{file_content}",
		"file_name": f"{file_name}",
		"doc_type": f"{doc_type_id}",
		"content_type": f"{content_type}"
	    }
	]

	return requests.post(f'https://api.forthcrm.com/v1/contacts/{contact_id}/documents/upload', headers = headers, json = json_body).json()

print(uploadDoc(contact_id,file_name,file_content))

