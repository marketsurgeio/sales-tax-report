# Sales Tax Report

This application generates a sales tax report and displays it in a chart format for the last three months.

## Features

- Fetches invoice data from the HighLevel API
- Calculates sales tax for each invoice
- Displays a bar chart showing monthly sales tax for the last three months
- Updates automatically via scheduled tasks
- Provides an embeddable chart widget
- Integrates with Looker Studio for enhanced visualization and reporting

## Looker Studio Integration

1. Set up Looker Studio:
   - Go to [Looker Studio](https://lookerstudio.google.com/)
   - Create a new report
   - Click "Add data" and select "Google Sheets"
   - Choose the same spreadsheet that's being updated by this application

2. Create your visualization:
   - Add charts and graphs using the data from your Google Sheet
   - Customize the design and layout to match your needs
   - Set up automatic refresh to ensure data stays current

3. Get the embeddable URL:
   - Click "Share" in the top right
   - Select "Embed report"
   - Copy the provided iframe code

4. Update your website:
   - Replace the existing chart iframe with the Looker Studio embed code
   - The Looker Studio report will automatically update when the Google Sheet is updated

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
HIGHLVL_API_KEY=your_api_key
SPREADSHEET_ID=your_spreadsheet_id
```

3. Configure Google Sheets API:
- Place your `credentials.json` in the project directory
- Run the application once to generate `token.pickle`

## Running the Application

1. Start the server:
```bash
python serve.py
```

2. View the chart:
- Open http://localhost:8000/chart.html in your browser
- The chart will display sales tax data for the last three months

3. Embed the chart:
- Use the following iframe code in your website or application:
```html
<iframe 
    src="http://localhost:8000/chart.html" 
    width="100%" 
    height="600" 
    frameborder="0"
    style="border: 1px solid #ccc;">
</iframe>
```

## Server Management

To ensure the servers stay running:

1. Using `nohup` (recommended for development):
```bash
nohup python serve.py > serve.log 2>&1 &
```

2. Using `screen` (alternative method):
```bash
screen -S sales_tax_server
python serve.py
# Press Ctrl+A then D to detach
# To reattach: screen -r sales_tax_server
```

3. Using `systemd` (recommended for production):
```bash
# Copy the service file
sudo cp com.salestax.report.plist /Library/LaunchDaemons/

# Load and start the service
sudo launchctl load /Library/LaunchDaemons/com.salestax.report.plist
```

To check server status:
```bash
# Check if server is running
ps aux | grep "python serve.py" | grep -v grep

# View server logs
tail -f serve.log
```

To restart the server:
```bash
# If using nohup
pkill -f "python serve.py"
nohup python serve.py > serve.log 2>&1 &

# If using systemd
sudo launchctl unload /Library/LaunchDaemons/com.salestax.report.plist
sudo launchctl load /Library/LaunchDaemons/com.salestax.report.plist
```

## Port Usage Warning

**Important:**
- Do not use a port that is already in use by another process. The default is port 8000.
- To check if port 8000 is in use:
  ```bash
  lsof -i :8000
  ```
- If it is, either kill the process using it:
  ```bash
  kill -9 <PID>
  ```
  or change the port used by the server.

- To change the port, edit `serve.py` and modify the line:
  ```python
  app.run(port=8000)
  # Change 8000 to another available port, e.g., 8080
  ```
- Update your iframe and browser URLs to match the new port.

## Scheduling

To run the report automatically:

1. Make the scheduler script executable:
```bash
chmod +x start_scheduler.sh
```

2. Run the scheduler:
```bash
./start_scheduler.sh
```

## Troubleshooting

- If the chart doesn't load, ensure the server is running (`python serve.py`)
- If data isn't updating, check the scheduler logs
- For API issues, verify your API key and credentials
- If the server won't start, check if port 8000 is already in use:
  ```bash
  lsof -i :8000
  # If port is in use, kill the process:
  kill -9 <PID>
  ```
- If you change the port, update all references to the server URL accordingly.

## Support

For issues or questions, please check the logs in:
- `sales_tax_report.log`
- `serve.log`
- `auth_server.log`

## Embedding the Report

You have two options for embedding the report:

1. Using Looker Studio (Recommended):
```html
<!-- Replace YOUR_REPORT_ID with your actual Looker Studio report ID -->
<iframe 
    src="https://lookerstudio.google.com/embed/reporting/YOUR_REPORT_ID/page/YOUR_PAGE_ID" 
    width="100%" 
    height="600" 
    frameborder="0"
    style="border: 1px solid #ccc;">
</iframe>
```

2. Using the local server (Alternative):
```html
<iframe 
    src="http://localhost:8000/chart.html" 
    width="100%" 
    height="600" 
    frameborder="0"
    style="border: 1px solid #ccc;">
</iframe>
``` 