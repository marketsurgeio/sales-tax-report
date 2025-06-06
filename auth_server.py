from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth_server.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/auth-config')
def get_auth_config():
    try:
        # Read the client ID from credentials.json
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)
            client_id = credentials['installed']['client_id']
        
        logging.info("Successfully retrieved client ID")
        return jsonify({
            'client_id': client_id
        })
    except Exception as e:
        logging.error(f"Error reading credentials: {str(e)}")
        return jsonify({'error': 'Failed to read credentials'}), 500

if __name__ == '__main__':
    logging.info("Starting auth server on port 5001...")
    app.run(host='0.0.0.0', port=5001) 