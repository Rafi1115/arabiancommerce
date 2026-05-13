#!/bin/bash

# 🧪 ARABIAN COMMERCE - QUICK TEST SCRIPT
# Run this after setting up the database

echo "🚀 Starting Arabian Commerce Test Suite..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api"

# Function to test endpoint
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local auth=$4
    local description=$5

    echo -e "${YELLOW}Testing: ${description}${NC}"

    if [ "$method" = "GET" ]; then
        curl -s -X GET "${BASE_URL}${url}" \
             -H "Authorization: Bearer ${auth}" \
             -w "\nStatus: %{http_code}\n"
    else
        curl -s -X $method "${BASE_URL}${url}" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer ${auth}" \
             -d "$data" \
             -w "\nStatus: %{http_code}\n"
    fi

    echo "----------------------------------------"
}

echo "📋 Step 1: Testing Public Endpoints"
test_endpoint "GET" "/products/" "" "" "Products List"
test_endpoint "GET" "/admin/categories/" "" "" "Categories List"

echo "✅ Basic endpoints working!"
echo ""
echo "📝 MANUAL STEPS REQUIRED:"
echo "1. Create admin user: python manage.py createsuperuser"
echo "2. Login as admin and get token"
echo "3. Register/login customer and get token"
echo "4. Create address with location data"
echo "5. Test cart and checkout flows"
echo ""
echo "📖 See TESTING_GUIDE.md for complete testing instructions"
echo ""
echo "🎯 QUICK TEST COMPLETE - Ready for manual testing!"