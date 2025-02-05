import os
import base64
import time
from typing import List
from flask import Flask, Response, render_template
from google_apis import Create_Service  # Ensure this import is valid

app = Flask(__name__)

class GmailException(Exception):
    """Gmail base exception class"""

class NoEmailFound(GmailException):
    """No email found"""

def search_emails(service, query_string: str, label_ids: List = None):
    try:
        message_list_response = service.users().messages().list(
            userId='me',
            labelIds=label_ids,
            q=query_string
        ).execute()

        message_items = message_list_response.get('messages', [])
        next_page_token = message_list_response.get('nextPageToken', None)

        while next_page_token:
            message_list_response = service.users().messages().list(
                userId='me',
                labelIds=label_ids,
                q=query_string,
                pageToken=next_page_token
            ).execute()

            message_items.extend(message_list_response.get('messages', []))
            next_page_token = message_list_response.get('nextPageToken', None)
        return message_items
    except Exception as e:
        raise NoEmailFound('No emails returned')

def get_file_data(service, message_id, attachment_id):
    response = service.users().messages().attachments().get(
        userId='me',
        messageId=message_id,
        id=attachment_id
    ).execute()

    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
    return file_data

def get_message_detail(service, message_id, msg_format='metadata', metadata_headers: List = None):
    message_detail = service.users().messages().get(
        userId='me',
        id=message_id,
        format=msg_format,
        metadataHeaders=metadata_headers
    ).execute()
    return message_detail

def download_resume(file_name, file_content, folder_path):
    """
    Downloads a file only if it doesn't already exist in the folder.
    :param file_name: Name of the file to download
    :param file_content: The content of the file (e.g., binary data)
    :param folder_path: Target folder to save the file
    """
    file_path = os.path.join(folder_path, file_name)
    
    # Check if file already exists
    if os.path.exists(file_path):
        print(f"File '{file_name}' already exists. Skipping download.")
        return False  # Indicate that the file was skipped
    else:
        # Save the file if it doesn't exist
        with open(file_path, 'wb') as file:
            file.write(file_content)
        print(f"File '{file_name}' downloaded successfully.")
        return True  # Indicate that the file was downloaded

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-script', methods=['GET'])
def run_script():
    def stream_downloads():
        try:
            CLIENT_FILE = 'client-secret.json'
            API_NAME = 'gmail'
            API_VERSION = 'v1'
            SCOPES = ['https://mail.google.com/']
            service = Create_Service(CLIENT_FILE, API_NAME, API_VERSION, SCOPES)

            query_string = 'subject:resume has:attachment'
            custom_save_location = r"C:\Users\chmad\OneDrive\Desktop\hloooooooooooooooo\Resumes"  # Replace with your desired directory

            # Create the directory if it does not exist
            if not os.path.exists(custom_save_location):
                os.makedirs(custom_save_location)
                yield f"data: Created directory: {custom_save_location}\n\n"

            email_messages = search_emails(service, query_string)
            total_files = len(email_messages)
            downloaded_files = []

            if total_files == 0:
                # Count existing files in the folder
                total_existing_files = len(os.listdir(custom_save_location))
                yield f"data: No emails found matching the query.\n"
                yield f"data: Total resumes in folder: {total_existing_files}\n\n"
                yield "event: complete\ndata: Stream completed\n\n"
                return

            for i, email_message in enumerate(email_messages, start=1):
                message_detail = get_message_detail(service, email_message['id'], msg_format='full', metadata_headers=['parts'])
                message_payload = message_detail.get('payload', {})

                if 'parts' in message_payload:
                    for msg_payload in message_payload['parts']:
                        file_name = msg_payload['filename']
                        body = msg_payload['body']

                        if 'attachmentId' in body:
                            attachment_id = body['attachmentId']
                            attachment_content = get_file_data(service, email_message['id'], attachment_id)

                            # Use the updated download_resume function
                            if download_resume(file_name, attachment_content, custom_save_location):
                                downloaded_files.append(file_name)
                                yield f"data: File {file_name} downloaded successfully.\n\n"
                            else:
                                yield f"data: File {file_name} already exists. Skipping.\n\n"
                time.sleep(0.1)

            # Count existing files in the folder after the process
            total_existing_files = len(os.listdir(custom_save_location))

            # Send a final message with the total number of files downloaded and total existing files
            yield f"data: Process completed. New Resumes Downloaded: {len(downloaded_files)}\n\n"
            yield f"data: Total resumes in folder: {total_existing_files}\n\n"
            yield "event: complete\ndata: Stream completed\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return Response(stream_downloads(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
