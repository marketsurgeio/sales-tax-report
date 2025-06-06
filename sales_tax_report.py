import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import json
import time
import schedule
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sales_tax_report.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class SalesTaxReport:
    def __init__(self):
        self.api_key = os.getenv('HIGHLEVEL_API_KEY')
        self.subaccount_id = os.getenv('HIGHLEVEL_SUBACCOUNT_ID')
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }
        
        # Google Sheets setup
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        self.worksheet_name = os.getenv('WORKSHEET_NAME')
        self.sheets_service = self._setup_google_sheets()
        
        # Track last run time
        self.last_run_file = 'last_run.txt'
        self.last_run = self._load_last_run()

    def _load_last_run(self):
        """Load the last run timestamp from file"""
        try:
            if os.path.exists(self.last_run_file):
                with open(self.last_run_file, 'r') as f:
                    return datetime.fromisoformat(f.read().strip())
        except Exception as e:
            logging.error(f"Error loading last run time: {str(e)}")
        return datetime.now() - timedelta(days=90)  # Default to 90 days ago

    def _save_last_run(self):
        """Save the current run timestamp to file"""
        try:
            with open(self.last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logging.error(f"Error saving last run time: {str(e)}")

    def _setup_google_sheets(self):
        """Set up Google Sheets API connection using OAuth 2.0"""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = None
        
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('sheets', 'v4', credentials=creds)

    def test_api_access(self):
        """Test basic API access with different endpoints"""
        print("\nTesting API 2.0 access...")
        
        # Test endpoints
        endpoints = [
            '/locations',
            '/contacts',
            '/opportunities',
            '/invoices/list'
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            print(f"\nTrying endpoint: {url}")
            print(f"Headers: {self.headers}")
            
            try:
                response = requests.get(url, headers=self.headers)
                print(f"Status Code: {response.status_code}")
                print(f"Response Text: {response.text}")
            except Exception as e:
                print(f"Error: {str(e)}")

    def get_invoice(self, invoice_id):
        """Get a single invoice by ID"""
        url = f"{self.base_url}/invoices/{invoice_id}"
        params = {
            'altId': self.subaccount_id,
            'altType': 'location'
        }
        
        print(f"\nFetching invoice {invoice_id}...")
        print(f"URL: {url}")
        print(f"Headers: {self.headers}")
        print(f"Params: {params}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to fetch invoice: {response.text}")
                
        except Exception as e:
            print(f"Error fetching invoice: {str(e)}")
            raise

    def get_invoices(self, start_date, end_date):
        """Get list of invoices from HighLevel API"""
        logging.info("Fetching invoices from HighLevel API...")
        
        url = f"{self.base_url}/invoices/"
        params = {
            'altId': self.subaccount_id,
            'altType': 'location',
            'startAt': start_date.strftime('%Y-%m-%d'),
            'endAt': end_date.strftime('%Y-%m-%d'),
            'limit': '100',  # Get up to 100 invoices
            'offset': '0',   # Start from the beginning
            'sortField': 'issueDate',
            'sortOrder': 'descend',
            'paymentMode': 'live',  # Get live mode invoices
            'status': 'paid'  # Only get paid invoices
        }
        
        logging.info(f"Fetching paid invoices...")
        logging.debug(f"URL: {url}")
        logging.debug(f"Headers: {self.headers}")
        logging.debug(f"Params: {params}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            logging.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                invoices = data.get('invoices', [])
                total = data.get('total', 0)
                logging.info(f"Found {total} total paid invoices")
                
                # Debug: Print first invoice structure
                if invoices:
                    logging.info("First invoice structure:")
                    logging.info(json.dumps(invoices[0], indent=2))
                
                return invoices
            else:
                raise Exception(f"Failed to fetch invoices: {response.text}")
                
        except Exception as e:
            logging.error(f"Error fetching invoices: {str(e)}")
            raise

    def format_currency(self, amount):
        """Format amount as currency"""
        return f"${amount:,.2f}" if amount else "$0.00"

    def generate_chart_data(self, invoices):
        """Generate data for the sales tax chart for the last 3 months"""
        try:
            # Get data from the Reformatted tab
            range_name = 'Reformatted!A1:D'  # Include the sales tax column
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values or len(values) < 2:
                logging.warning('No data found in Reformatted sheet')
                return []
            
            # Process the data from Reformatted sheet
            monthly_data = defaultdict(float)
            
            for row in values[1:]:  # Skip header row
                if len(row) >= 4:  # Make sure we have the sales tax column
                    try:
                        # Date is in the second column (index 1)
                        date = datetime.strptime(row[1], '%Y-%m-%d')
                        month_key = date.strftime('%Y-%m')
                        
                        # Sales tax is in the fourth column (index 3)
                        tax = float(row[3].replace('$', '').replace(',', ''))
                        monthly_data[month_key] += tax
                    except (ValueError, IndexError) as e:
                        logging.warning(f'Error processing row {row}: {str(e)}')
                        continue
            
            # Sort months and get last 3 months
            sorted_months = sorted(monthly_data.keys(), reverse=True)[:3]
            
            # Prepare chart data
            chart_data = []
            for month in sorted_months:
                month_date = datetime.strptime(month, '%Y-%m')
                month_name = month_date.strftime('%B %Y')
                chart_data.append({
                    'month': month_name,
                    'tax': monthly_data[month]
                })
            
            # Save chart data to JSON file
            with open('chart_data.json', 'w') as f:
                json.dump(chart_data, f)
            
            return chart_data
            
        except Exception as e:
            logging.error(f'Error generating chart data: {str(e)}')
            return []

    def generate_widget_code(self, chart_data):
        """Generate embeddable iframe code for the chart"""
        iframe_code = f"""
            <iframe 
                src="http://localhost:8000/chart.html" 
                width="100%" 
                height="600" 
                frameborder="0"
                style="border: 1px solid #ccc;">
            </iframe>
        """
        logging.info("\nEmbeddable iframe code for CRM:")
        logging.info("-" * 80)
        logging.info(iframe_code)
        logging.info("-" * 80)
        return iframe_code

    def update_google_sheet(self, invoices):
        """Update Google Sheet with invoice data"""
        try:
            # Prepare the data
            values = [
                # Header row
                ['Invoice Number', 'Date', 'Customer', 'Subtotal', 'Sales Tax', 'Total', 'Status']
            ]
            
            # Add invoice rows
            for invoice in invoices:
                invoice_number = invoice.get('invoiceNumber', 'N/A')
                issue_date = datetime.strptime(invoice.get('issueDate', ''), '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
                customer_name = invoice.get('contactDetails', {}).get('name', 'N/A')
                subtotal = invoice.get('totalSummary', {}).get('subTotal', 0)
                tax = invoice.get('totalSummary', {}).get('tax', 0)
                total = invoice.get('total', 0)
                status = invoice.get('status', 'N/A')
                
                values.append([
                    invoice_number,
                    issue_date,
                    customer_name,
                    self.format_currency(subtotal),
                    self.format_currency(tax),
                    self.format_currency(total),
                    status
                ])
            
            # Clear existing content
            range_name = f'{self.worksheet_name}!A1:G1000'
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            # Update with new data
            body = {
                'values': values
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logging.info(f"Updated {result.get('updatedCells')} cells in Google Sheet")
            
            # Generate iframe code for the Google Sheet
            iframe_code = f'''
            <iframe 
                src="https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/preview?rm=minimal" 
                width="100%" 
                height="600" 
                frameborder="0"
                style="border: 1px solid #ccc;">
            </iframe>
            '''
            
            logging.info("\nEmbeddable iframe code for CRM:")
            logging.info("-" * 80)
            logging.info(iframe_code)
            logging.info("-" * 80)
            
        except Exception as e:
            logging.error(f"Error updating Google Sheet: {str(e)}")
            raise

    def generate_report(self):
        """Generate sales tax report"""
        try:
            # Use a longer date range (last 12 months)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Changed from 90 to 365 days
            
            # Get invoices
            invoices = self.get_invoices(start_date, end_date)
            
            if invoices:
                logging.info("\n=== Sales Tax Report ===")
                logging.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                logging.info("\nPaid Invoices:")
                logging.info("-" * 80)
                
                total_sales = 0
                total_tax = 0
                
                for invoice in invoices:
                    invoice_number = invoice.get('invoiceNumber', 'N/A')
                    issue_date = datetime.strptime(invoice.get('issueDate', ''), '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d')
                    customer_name = invoice.get('contactDetails', {}).get('name', 'N/A')
                    subtotal = invoice.get('totalSummary', {}).get('subTotal', 0)
                    tax = invoice.get('totalSummary', {}).get('tax', 0)
                    total = invoice.get('total', 0)
                    
                    logging.info(f"\nInvoice #{invoice_number}")
                    logging.info(f"Date: {issue_date}")
                    logging.info(f"Customer: {customer_name}")
                    logging.info(f"Subtotal: {self.format_currency(subtotal)}")
                    logging.info(f"Sales Tax: {self.format_currency(tax)}")
                    logging.info(f"Total: {self.format_currency(total)}")
                    logging.info("-" * 40)
                    
                    total_sales += subtotal
                    total_tax += tax
                
                logging.info("\n=== Summary ===")
                logging.info(f"Total Sales: {self.format_currency(total_sales)}")
                logging.info(f"Total Sales Tax: {self.format_currency(total_tax)}")
                logging.info(f"Total Revenue: {self.format_currency(total_sales + total_tax)}")
                
                # Generate chart data
                chart_data = self.generate_chart_data(invoices)
                
                # Save chart data to JSON file
                with open('chart_data.json', 'w') as f:
                    json.dump(chart_data, f)
                
                # Update Google Sheet
                self.update_google_sheet(invoices)
                
                # Save the current run time
                self._save_last_run()
            
            logging.info("\nReport generation completed successfully!")
            
        except Exception as e:
            logging.error(f"Error generating report: {str(e)}")
            raise

def run_report():
    """Function to run the report"""
    try:
        report = SalesTaxReport()
        report.generate_report()
        logging.info("Report generated successfully at " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        logging.error(f"Error running report: {str(e)}")

if __name__ == "__main__":
    # Check if running in scheduled mode
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--schedule':
        logging.info("Starting scheduled report generation...")
        
        # Schedule the report to run daily at 1 AM
        schedule.every().day.at("01:00").do(run_report)
        
        # Run immediately on startup
        run_report()
        
        logging.info("Scheduler started. Will run daily at 1 AM.")
        
        # Keep the script running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying on error
    else:
        # Run once
        run_report() 