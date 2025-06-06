#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start the auth server in the background
python auth_server.py > auth_server.log 2>&1 &

# Start the file server in the background
python serve.py > serve.log 2>&1 &

# Start the report scheduler
python sales_tax_report.py

# Keep the script running
wait 