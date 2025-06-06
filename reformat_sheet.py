import os
import random
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from datetime import datetime, timedelta
import requests

# Load environment variables
load_dotenv()

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
WORKSHEET_NAME = os.getenv('WORKSHEET_NAME')
NEW_SHEET_NAME = 'Reformatted'
API_KEY = os.getenv('HIGHLEVEL_API_KEY')
SUBACCOUNT_ID = os.getenv('HIGHLEVEL_SUBACCOUNT_ID')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None

if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

def get_invoices():
    """Get list of invoices from HighLevel API"""
    base_url = "https://services.leadconnectorhq.com"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'Version': '2021-07-28'
    }
    
    # Get invoices for the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    url = f"{base_url}/invoices/"
    params = {
        'altId': SUBACCOUNT_ID,
        'altType': 'location',
        'startAt': start_date.strftime('%Y-%m-%d'),
        'endAt': end_date.strftime('%Y-%m-%d'),
        'limit': '100',
        'offset': '0',
        'sortField': 'issueDate',
        'sortOrder': 'descend',
        'paymentMode': 'live',
        'status': 'paid'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('invoices', [])
        else:
            print(f"Failed to fetch invoices: {response.text}")
            return []
    except Exception as e:
        print(f"Error fetching invoices: {str(e)}")
        return []

# Get invoices from HighLevel API
invoices = get_invoices()

# Create a dictionary to store invoice data by date
invoice_data = {}
for invoice in invoices:
    try:
        issue_date = datetime.strptime(invoice.get('issueDate', ''), '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
        tax = invoice.get('totalSummary', {}).get('tax', 0)
        invoice_data[issue_date] = tax
    except Exception as e:
        print(f"Error processing invoice: {str(e)}")
        continue

# Read data from the original worksheet
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{WORKSHEET_NAME}!A1:C').execute()
values = result.get('values', [])

if not values or len(values) < 2:
    print('No data found or not enough rows.')
    exit(1)

header = values[0]
data = values[1:]

# Prepare new data with actual sales tax values
new_header = header + ['Sales Tax']
new_data = []
for row in data:
    # Ensure row has at least 3 columns
    while len(row) < 3:
        row.append('')
    
    # Get the date from the row (assuming it's in the second column)
    try:
        date = row[1]
        tax = invoice_data.get(date, 0)
        sales_tax = f"${tax:.2f}"
    except (IndexError, ValueError):
        sales_tax = "$0.00"
    
    new_data.append(row + [sales_tax])

# Delete the 'Reformatted' sheet if it exists
spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = None
for s in spreadsheet['sheets']:
    if s['properties']['title'] == NEW_SHEET_NAME:
        sheet_id = s['properties']['sheetId']
        break
if sheet_id is not None:
    requests = [{
        'deleteSheet': {
            'sheetId': sheet_id
        }
    }]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': requests}
    ).execute()

# Add the new sheet
requests = [{
    'addSheet': {
        'properties': {
            'title': NEW_SHEET_NAME
        }
    }
}]
service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

# Write the new data
sheet.values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'{NEW_SHEET_NAME}!A1',
    valueInputOption='RAW',
    body={'values': [new_header] + new_data}
).execute()

print(f"Sheet '{NEW_SHEET_NAME}' created and populated with actual sales tax values.") 