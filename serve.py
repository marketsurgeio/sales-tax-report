import http.server
import socketserver
import os
import sys
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PORT = 8000
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
WORKSHEET_NAME = 'copy of reformatted'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_credentials():
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
    return creds

def get_chart_data():
    try:
        service = build('sheets', 'v4', credentials=get_credentials())
        sheet = service.spreadsheets()
        
        # Get data from the reformatted sheet
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{WORKSHEET_NAME}!A:D'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return []
            
        # Process data for the last 3 months
        today = datetime.now()
        three_months_ago = today - timedelta(days=90)
        
        monthly_totals = {}
        
        for row in values[1:]:  # Skip header
            if len(row) >= 4:  # Ensure row has enough columns
                try:
                    # Parse the date from the second column
                    date_str = row[1]
                    # Try different date formats
                    try:
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        try:
                            date = datetime.strptime(date_str, '%m/%d/%Y')
                        except ValueError:
                            try:
                                date = datetime.strptime(date_str, '%m-%d-%Y')
                            except ValueError:
                                print(f"Could not parse date: {date_str}")
                                continue
                    
                    if date >= three_months_ago:
                        month_key = date.strftime('%B %Y')  # Format as "Month Year"
                        # Extract numeric value from the sales tax string (remove $ and ,)
                        tax_str = row[3].replace('$', '').replace(',', '')
                        tax_value = float(tax_str)
                        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + tax_value
                except (ValueError, IndexError) as e:
                    print(f"Error processing row: {e}")
                    continue
        
        # Sort months chronologically
        sorted_months = sorted(
            monthly_totals.items(),
            key=lambda x: datetime.strptime(x[0], '%B %Y')
        )
        
        # Format data for chart
        chart_data = [
            {'month': month, 'total': round(total, 2)}
            for month, total in sorted_months
        ]
        
        return chart_data
    except Exception as e:
        print(f"Error getting chart data: {str(e)}")
        return []

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

    def do_GET(self):
        print(f"Received request for: {self.path}")
        
        if self.path == '/api/chart-data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            chart_data = get_chart_data()
            self.wfile.write(json.dumps(chart_data).encode())
            return
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

Handler = MyHandler
Handler.extensions_map.update({
    '.json': 'application/json',
})

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        print("Current directory:", os.getcwd())
        print("Available files:", os.listdir())
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()
except OSError as e:
    print(f"Error starting server: {e}")
    print("Make sure no other process is using port 8000")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nServer stopped by user")
    sys.exit(0) 