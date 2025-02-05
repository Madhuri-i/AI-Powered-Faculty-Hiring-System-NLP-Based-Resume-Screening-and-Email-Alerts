import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import csv
import os
from concurrent.futures import ThreadPoolExecutor  # ThreadPoolExecutor for parallel processing

# Email credentials and server configuration
SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server
SMTP_PORT = 587  # Port for TLS
SENDER_EMAIL = "tokallaakshaya2004@gmail.com"  # Replace with your email
SENDER_PASSWORD = "jmoy dolg alqg rqbk"  # Replace with your App Password

# Folder path where the CSV file is located
CSV_FOLDER_PATH = "C:\Users\chmad\OneDrive\Desktop\hloooooooooooooooo\Resumes"  # Path to the folder containing the CSV file

# Contact details for the email
CONTACT_EMAIL = "hr@brecw.edu.in"  # Replace with the actual contact email
CONTACT_PHONE = "123-456-7890"  # Replace with the actual contact phone number
COLLEGE_NAME = "Bhoj Reddy Engineering College for Women"  # Updated college name

def send_email(to_email: str, subject: str, body: str):
    try:
        # Set up the MIME structure for the email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the message body
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail's SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Send the email
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def find_csv_file(folder_path: str):
    """Find the first CSV file in the specified folder."""
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            return os.path.join(folder_path, filename)
    return None

def send_shortlisted_notifications():
    # Automatically find the CSV file in the specified folder
    csv_file_path = find_csv_file(CSV_FOLDER_PATH)
    
    if not csv_file_path:
        print("No CSV file found in the specified folder.")
        return
    
    # Read the shortlisted candidates from the CSV file
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row

        # Create a thread pool to send emails concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:  # Use a maximum of 10 threads
            for row in csv_reader:
                # Check if the row has the expected number of columns
                if len(row) < 7:
                    print(f"Skipping row due to insufficient data: {row}")
                    continue

                filename, name, email, position, skill_match, experience_match, degree_match = row

                # Construct the email subject and body
                subject = f"Congratulations on Being Shortlisted for Faculty Position at {COLLEGE_NAME}"
                body = f"""
                Dear {name},

                We are pleased to inform you that you have been shortlisted for the position of {position} at {COLLEGE_NAME}. 
                Congratulations on reaching this stage!

                Our management team will contact you shortly with further details about the next steps in the hiring process.

                For any questions or additional information, please feel free to reach out to us at {CONTACT_EMAIL} or {CONTACT_PHONE}.


                Best regards,
                Human Resources Department
                {COLLEGE_NAME}
                {CONTACT_EMAIL}
                {CONTACT_PHONE}
                """

                # Submit email sending task to thread pool
                executor.submit(send_email, email, subject, body)

# Run the notification sending function
send_shortlisted_notifications()
