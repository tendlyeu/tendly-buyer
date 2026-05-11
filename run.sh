#!/bin/bash
# Tendly Buyer - Development Server
# Starts on port 5004 (avoids conflict with tendly:5001, tendly-agent-chat:5002, tendly-taas:5003)

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

echo ""
echo "Starting Tendly Buyer on http://localhost:5004"
echo ""

# Start the server
python app.py
