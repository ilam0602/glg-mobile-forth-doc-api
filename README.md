
# Flask Document Upload and Retrieval API

This is a Flask application for uploading and retrieving documents using Firebase for authentication and Firestore for user data storage. It also integrates with the Forth CRM API for document management.

## Prerequisites

- Python 3.x
- Firebase project with Firestore and Authentication set up
- Forth CRM account and API credentials

## Setup

### 1. Clone the Repository

```sh
git clone <repository-url>
cd <repository-directory>
```

### 2. Create and Activate a Virtual Environment

```sh
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Environment Variables



```
Fill in .env.Sample and rename to .env
```

## Running the Application

```

flask run

The application will be available at `http://127.0.0.1:5000/`.

```

## API Endpoints

### 1. Upload Document

**Endpoint:** `/upload`

**Method:** `POST`

**Description:** Uploads a document for a specific contact.

**Request Body:**

```json
{
    "contact_id": "contact_id",
    "file_name": "file_name",
    "file_content": "base64_encoded_content",
    "auth_token": "firebase_auth_token"
}
```

**Response:**

See documentation: 
https://debtpaypro.stoplight.io/docs/dpp-api/4121bcce11e74-upload-document-to-contact-dashboard


### 2. Get Document

**Endpoint:** `/get_doc`

**Method:** `POST`

**Description:** Retrieves a document for a specific contact.

**Request Body:**

```json
{
    "contact_id": "contact_id",
    "doc_id": "document_id",
    "auth_token": "firebase_auth_token"
}
```

**Response:**

See Documentation:
https://debtpaypro.stoplight.io/docs/dpp-api/9ab6480764e77-get-document-by-id


## File Structure

```
.
├── forth_api.py
├── requirements.txt
├── .env
└── README.md
```

## Functions

### `convert_to_base64(file_path)`

Converts the content of a file to a base64 encoded string.

### `forthCRM_authtoken()`

Authenticates and retrieves an API key from Forth CRM.

### `uploadDoc(contact_id, file_name, file_content)`

Uploads a document to Forth CRM for a given contact.

### `getDoc(contact_id, doc_id)`

Retrieves a document from Forth CRM for a given contact.

### `verify_firebase_token(token)`

Verifies the provided Firebase authentication token.

### `check_user_contact(uid, contact_id)`

Checks if the provided contact ID matches the user in Firestore.

## Notes

- Ensure the Firebase and Forth API keys are correctly set in the `.env` file.
- Make sure to replace the hardcoded contact ID in the `uploadDoc` and `getDoc` functions with dynamic data.

## License

This project is licensed under the MIT License.

## Contact

If you have any questions, feel free to contact the project maintainer.
