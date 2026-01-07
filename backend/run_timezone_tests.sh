#!/bin/bash
# Run timezone tests

echo "🧪 Installing test dependencies..."
pip install -q -r requirements-test.txt

echo ""
echo "🚀 Running timezone tests..."
echo "================================"
pytest tests/test_timezone_critical.py -v

echo ""
echo "✅ Test run complete!"
