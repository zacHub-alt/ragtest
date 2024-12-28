import os.path
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def readEmails():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'my_cred_file.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages', [])
        email_data_list = []
        if not messages:
            print('No new messages.')
        else:
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                email_data = msg['payload']['headers']
                email_content = get_email_content(msg)
                email_subject = get_header_value(email_data, 'Subject')
                email_from = get_header_value(email_data, 'From')
                email_to = get_header_value(email_data, 'To')
                email_data_dict = {
                    'From': email_from,
                    'To': email_to,
                    'Subject': email_subject,
                    'Message': email_content
                }
                email_data_list.append(email_data_dict)
                # mark the message as read (optional)
                service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        # Export email data to a JSON file
        with open('email_data.json', 'w') as json_file:
            json.dump(email_data_list, json_file, indent=4)
        print('Email data exported to email_data.json')
    except Exception as error:
        print(f'An error occurred: {error}')

def get_email_content(msg):
    """Extracts the email content from the message."""
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            try:
                data = part['body']["data"]
                byte_code = base64.urlsafe_b64decode(data)
                text = byte_code.decode("utf-8")
                return text
            except BaseException as error:
                pass
    else:
        try:
            data = msg['payload']['body']["data"]
            byte_code = base64.urlsafe_b64decode(data)
            text = byte_code.decode("utf-8")
            return text
        except BaseException as error:
            pass
    return ""

def get_header_value(headers, name):
    """Extracts the value of a specific header from the email headers."""
    for header in headers:
        if header['name'] == name:
            return header['value']
    return ""

# Run the function
readEmails()
