#!/bin/bash

# Walmart API Testing Setup Script

echo "🛒 Setting up Walmart API Testing Environment"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
        echo "⚠️  Please edit .env and add your Walmart Developer credentials!"
        echo "   Required: WALMART_CONSUMER_ID, WALMART_PRIVATE_KEY_VERSION, WALMART_PRIVATE_KEY_PATH (or WALMART_PRIVATE_KEY)"
        echo "   Optional: PUBLISHER_ID, CAMPAIGN_ID, AD_ID"
else
    echo "✅ .env file already exists"
fi

# Create results directory
mkdir -p results

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Walmart API credentials"
echo "2. Run: python main.py --help (to see options)"
echo "3. Run: python main.py (to start testing)"
echo ""
echo "Quick test commands:"
echo "  python main.py                    # Standard testing"
echo "  python main.py --mode limits      # Test maximum limits"
echo "  python main.py --custom-sizes 1,10,50,100  # Custom batch sizes"