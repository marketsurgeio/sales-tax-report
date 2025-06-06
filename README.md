# Sales Tax Report

This project automates the process of tracking and reporting sales tax data, with integration to Looker Studio for visualization and GoHighLevel for embedding.

## Features

- Automated sales tax data collection from HighLevel API
- Data processing and formatting in Google Sheets
- Interactive visualization in Looker Studio
- Embeddable charts in GoHighLevel
- Automated scheduling and reporting

## Prerequisites

- Python 3.9+
- Google Cloud Platform account with Sheets API enabled
- HighLevel API access
- GoHighLevel account
- Looker Studio access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/marketsurgeio/sales-tax-report.git
cd sales-tax-report
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
SPREADSHEET_ID=your_spreadsheet_id
WORKSHEET_NAME=your_worksheet_name
HIGHLEVEL_API_KEY=your_api_key
HIGHLEVEL_SUBACCOUNT_ID=your_subaccount_id
```

## Usage

### Manual Run
```bash
python sales_tax_report.py
```

### Automated Scheduling
The project includes a scheduler script that can be run as a service:

```bash
./start_scheduler.sh
```

### Looker Studio Integration
1. Connect to the Google Sheet containing the sales tax data
2. Create a new report
3. Use the following formula for monthly grouping:
```
CASE 
  WHEN MONTH(Date) = 1 THEN CONCAT("January ", YEAR(Date))
  WHEN MONTH(Date) = 2 THEN CONCAT("February ", YEAR(Date))
  WHEN MONTH(Date) = 3 THEN CONCAT("March ", YEAR(Date))
  WHEN MONTH(Date) = 4 THEN CONCAT("April ", YEAR(Date))
  WHEN MONTH(Date) = 5 THEN CONCAT("May ", YEAR(Date))
  WHEN MONTH(Date) = 6 THEN CONCAT("June ", YEAR(Date))
  WHEN MONTH(Date) = 7 THEN CONCAT("July ", YEAR(Date))
  WHEN MONTH(Date) = 8 THEN CONCAT("August ", YEAR(Date))
  WHEN MONTH(Date) = 9 THEN CONCAT("September ", YEAR(Date))
  WHEN MONTH(Date) = 10 THEN CONCAT("October ", YEAR(Date))
  WHEN MONTH(Date) = 11 THEN CONCAT("November ", YEAR(Date))
  WHEN MONTH(Date) = 12 THEN CONCAT("December ", YEAR(Date))
END
```

### GoHighLevel Integration
1. Get the embed code from Looker Studio
2. Add an HTML widget in GoHighLevel
3. Paste the iframe code

## Development

### Project Structure
```
sales-tax-report/
├── sales_tax_report.py    # Main script
├── reformat_sheet.py      # Google Sheets formatting
├── serve.py              # Local server for development
├── auth_server.py        # Authentication handling
├── requirements.txt      # Python dependencies
└── start_scheduler.sh    # Scheduling script
```

### Running Tests
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Security

- Never commit sensitive files (token.pickle, credentials.json, .env)
- Keep API keys secure
- Use environment variables for sensitive data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository. 