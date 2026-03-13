#!/bin/bash

# SpeakFlow Backend Setup Script
# This script sets up the SpeakFlow backend for development and production

set -e

echo "🚀 Setting up SpeakFlow Backend..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📦 Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p ssl
mkdir -p data

# Initialize database
echo "🗄️  Initializing database..."
python -c "
try:
    from database import init_database
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

# Create a default API key for development
echo "🔑 Creating default API key..."
python -c "
try:
    from auth import AuthManager
    auth = AuthManager()
    key = auth.create_api_key('Default Development Key', 'system', None)
    print(f'✅ Default API key created: {key}')
    print('💡 Use this key for testing: Authorization: Bearer {key}')
except Exception as e:
    print(f'❌ Failed to create API key: {e}')
"

# Run tests
echo "🧪 Running tests..."
if pytest test_main.py -v; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed - check the output above"
fi

echo ""
echo "🎉 SpeakFlow Backend setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run the server: python main.py"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo "4. Use the default API key for testing (shown above)"
echo ""
echo "🐳 For Docker deployment:"
echo "1. docker-compose up -d"
echo "2. Check logs: docker-compose logs -f"
echo ""
echo "📚 For more information, see README.md"
