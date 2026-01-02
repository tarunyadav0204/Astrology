#!/bin/bash

echo "🚀 Testing Blog System Locally"

# 1. Install dependencies
echo "📦 Installing dependencies..."
cd backend
pip install -r requirements.txt

# 2. Initialize database
echo "🗄️ Initializing blog database..."
python -c "
from blog.database import init_blog_database
init_blog_database()
print('✅ Blog database initialized')
"

# 3. Start backend server
echo "🖥️ Starting backend server..."
echo "Visit http://localhost:8001/docs to test API endpoints"
echo "Visit http://localhost:3001/blog to see blog frontend"
echo ""
echo "Test endpoints:"
echo "- GET /api/blog/posts - List posts"
echo "- POST /api/blog/posts - Create post"
echo "- POST /api/blog/upload-image - Upload image"
echo ""

python main.py