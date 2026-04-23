#!/bin/bash
# Tendly Chat - Development Server
# Starts on port 5002 to avoid conflict with main tendly app (port 5001)

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
echo "Starting Tendly Chat on http://localhost:5002"
echo ""

# Start the server
python app.py
