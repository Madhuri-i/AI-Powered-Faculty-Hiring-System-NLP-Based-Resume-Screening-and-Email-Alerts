import os
import base64
import time
from typing import List
from flask import Flask, Response, render_template
from google_apis import Create_Service  # Ensure this import is implemented
from short import analyze_resumes, save_to_csv  # Importing from short.py
from tabulate import tabulate
from json import dumps
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
# Email credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "tokallaakshaya2004@gmail.com"
SENDER_PASSWORD = "jmoy dolg alqg rqbk"
CONTACT_EMAIL = "hr@brecw.edu.in"
CONTACT_PHONE = "123-456-7890"
COLLEGE_NAME = "Bhoj Reddy Engineering College for Women"


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
    file_path = os.path.join(folder_path, file_name)
    if os.path.exists(file_path):
        print(f"File '{file_name}' already exists. Skipping download.")
        return False
    else:
        with open(file_path, 'wb') as file:
            file.write(file_content)
        print(f"File '{file_name}' downloaded successfully.")
        return True

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_shortlisted_notifications():
    csv_file_path = "shortlisted_resumes.csv"
    if not os.path.exists(csv_file_path):
        print("No shortlisted resumes CSV found.")
        return "No CSV file found for shortlisted resumes."

    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)
        with ThreadPoolExecutor(max_workers=10) as executor:
            for row in csv_reader:
                if len(row) < 7:
                    continue
                _, name, email, position, _, _, _ = row
                subject = f"Congratulations on Being Shortlisted at {COLLEGE_NAME}"
                body = f"""
                Dear {name},

                Congratulations! You have been shortlisted for the {position} position at {COLLEGE_NAME}.
                Our HR team will contact you with further details.

                Contact us at {CONTACT_EMAIL} or {CONTACT_PHONE} for any queries.

                Best regards,
                HR Department,
                {COLLEGE_NAME}
                """
                executor.submit(send_email, email, subject, body)
    return "Emails sent successfully."
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
            custom_save_location = r"C:\Users\chmad\OneDrive\Desktop\hloooooooooooooooo\Resumes"

            if not os.path.exists(custom_save_location):
                os.makedirs(custom_save_location)
                yield f"data: Created directory: {custom_save_location}\n\n"

            email_messages = search_emails(service, query_string)
            total_files = len(email_messages)
            downloaded_files = []

            if total_files == 0:
                total_existing_files = len(os.listdir(custom_save_location))
                yield f"data: No emails found matching the query.\n"
                yield f"data: Total resumes in folder: {total_existing_files}\n\n"
                yield "event: complete\ndata: Stream completed\n\n"
                return

            for email_message in email_messages:
                message_detail = get_message_detail(service, email_message['id'], msg_format='full', metadata_headers=['parts'])
                message_payload = message_detail.get('payload', {})

                if 'parts' in message_payload:
                    for msg_payload in message_payload['parts']:
                        file_name = msg_payload['filename']
                        body = msg_payload['body']

                        if 'attachmentId' in body:
                            attachment_id = body['attachmentId']
                            attachment_content = get_file_data(service, email_message['id'], attachment_id)

                            if download_resume(file_name, attachment_content, custom_save_location):
                                downloaded_files.append(file_name)
                                yield f"data: File {file_name} downloaded successfully.\n\n"
                            else:
                                yield f"data: File {file_name} already exists. Skipping.\n\n"
                time.sleep(0.1)

            total_existing_files = len(os.listdir(custom_save_location))
            yield f"data: Process completed. New Resumes Downloaded: {len(downloaded_files)}\n\n"
            yield f"data: Total resumes in folder: {total_existing_files}\n\n"
            yield "event: complete\ndata: Stream completed\n\n"
        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return Response(stream_downloads(), content_type='text/event-stream')

@app.route('/shortlist-resumes', methods=['GET'])
def shortlist_resumes():
    def stream_shortlisting():
        try:
            resume_directory = r"C:\Users\chmad\OneDrive\Desktop\hloooooooooooooooo\Resumes"
            shortlisted_resumes = analyze_resumes(resume_directory)
            total_applicants = len(shortlisted_resumes)

            if not shortlisted_resumes:
                yield f"data: No resumes met the criteria for shortlisting.\n\n"
                yield "event: complete\ndata: Stream completed\n\n"
                return

            csv_file_path = "shortlisted_resumes.csv"
            save_to_csv(shortlisted_resumes, filename=csv_file_path)

            headers = ["File", "Name", "Email", "Position", "Skill %", "Exp Match", "Deg Match"]
            table = tabulate(shortlisted_resumes, headers=headers, tablefmt="grid")

            yield f"data: {dumps({'resumes': shortlisted_resumes, 'csv_file': csv_file_path, 'total': total_applicants})}\n\n"
            yield f"data: CSV file created: {csv_file_path}\n\n"
            yield f"data: Total shortlisted applicants: {total_applicants}\n\n"
            yield "event: complete\ndata: Shortlisting process completed\n\n"
        except Exception as e:
            yield f"data: Error during shortlisting: {str(e)}\n\n"

    return Response(stream_shortlisting(), content_type='text/event-stream')

@app.route('/send-mails', methods=['GET'])
def send_mails():
    def stream_mails():
        try:
            status = send_shortlisted_notifications()
            yield f"data: {status}\n\n"
            yield "event: complete\ndata: Emails sent successfully\n\n"
        except Exception as e:
            yield f"data: Error sending emails: {str(e)}\n\n"
    return Response(stream_mails(), content_type='text/event-stream')
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)