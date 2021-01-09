import json
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime

FILE_PATH = os.path.dirname(__file__)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1Wu2fL9DMmroz4PM7iNE-wf7IfqEAho4ArJ9L-zzxrxo'
RANGE_NAME = 'Error!A2:D'


def authorize_creds():

    creds = None

    if os.path.exists(os.path.join(FILE_PATH, '../token.pickle')):
        with open(os.path.join(FILE_PATH, '../token.pickle'), 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not os.path.exists(os.path.join(FILE_PATH, '../credentials.json')):
            json_str = os.environ.get('CREDENTIALS_JSON')
            print(json.dumps(json.loads(json_str), indent=4, sort_keys=True))
            with open(os.path.join(FILE_PATH, '../credentials.json'), 'w') as f:
                f.write(json_str)
                f.close()

        flow = InstalledAppFlow.from_client_secrets_file(
            os.path.join(FILE_PATH, '../credentials.json'), SCOPES)
        creds = flow.run_console()

        # Save the credentials for the next run
        with open(os.path.join(FILE_PATH, '../token.pickle'), 'wb') as token:
            pickle.dump(creds, token)

    return creds


def add_response(username, level, response):

    # Authorize requests to read/write
    creds = authorize_creds()

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    response_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    values = [[response_time, username, level, response]]
    body = {'values': values}

    # Append the data on the last row
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
        valueInputOption='RAW', body=body).execute()


if __name__ == '__main__':
    print("Testing credentials...")
    print(authorize_creds())
