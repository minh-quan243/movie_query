#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
echo "📥 Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Download NLTK data
echo "📥 Downloading NLTK data..."
python -c "import nltk; nltk.download('stopwords', quiet=True)"

# Install Node.js if not available and build frontend
echo "🎨 Building frontend..."
cd frontend

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
npm ci --production=false

# Build frontend
echo "🔨 Building React app..."
npm run build

# Return to root
cd ..

echo "✅ Build complete!"
