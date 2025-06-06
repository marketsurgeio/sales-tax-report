import pytest
from datetime import datetime, timedelta
from sales_tax_report import get_invoices, calculate_monthly_totals

def test_get_invoices():
    # Test that get_invoices returns a list
    invoices = get_invoices()
    assert isinstance(invoices, list)

def test_calculate_monthly_totals():
    # Test data
    test_data = [
        {'date': '2024-03-01', 'tax': 100},
        {'date': '2024-03-15', 'tax': 200},
        {'date': '2024-04-01', 'tax': 300},
    ]
    
    # Convert test data to the format expected by the function
    formatted_data = [
        {
            'issueDate': f"{item['date']}T00:00:00.000Z",
            'totalSummary': {'tax': item['tax']}
        }
        for item in test_data
    ]
    
    # Calculate totals
    totals = calculate_monthly_totals(formatted_data)
    
    # Assertions
    assert 'March 2024' in totals
    assert 'April 2024' in totals
    assert totals['March 2024'] == 300  # 100 + 200
    assert totals['April 2024'] == 300  # 300 