#!/bin/bash
# Quick setup script for L'Aura project

set -e

echo "🚀 L'Aura Project - Quick Setup"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from project root"
    exit 1
fi

cd "$(dirname "$0")/.."

echo "📦 Installing Backend Dependencies..."
cd backend
if [ ! -f ".env" ]; then
    echo "⚠️  Creating backend/.env from .env.example"
    cp .env.example .env
fi
pip install -r requirements.txt
echo "✅ Backend dependencies installed"
echo ""

echo "📦 Installing Frontend Dependencies..."
cd ../frontend
if [ ! -f ".env" ]; then
    echo "⚠️  Creating frontend/.env from .env.example"
    cp .env.example .env
fi
yarn install
echo "✅ Frontend dependencies installed"
echo ""

echo "🌱 Seeding Database..."
cd ../backend
python seed.py
echo "✅ Database seeded"
echo ""

echo "✅ Setup Complete!"
echo ""
echo "📝 Next steps:"
echo "   Start services: make dev"
echo "   Or manually:"
echo "     Terminal 1: cd backend && uvicorn server:app --reload"
echo "     Terminal 2: cd frontend && yarn start"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8001"
echo "   Admin: http://localhost:3000/admin/login (admin/admin123)"
