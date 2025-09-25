#!/bin/bash

# Footer Quickstart Testing Script
# Automates the manual testing scenarios from quickstart.md

set -e

echo "🚀 Starting Footer Quickstart Testing..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function for test results
test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$1" = "PASS" ]; then
        echo -e "${GREEN}✅ $2${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo -e "${BLUE}📁 Setting up test environment...${NC}"

# Create backend footer directory structure
echo "Creating backend footer directory structure..."
mkdir -p backend/data/footer/

# Create test footer content files as per quickstart.md
echo "Creating test content files..."

# Footer configuration content
cat > backend/data/footer/footer.md << 'EOF'
# Footer Configuration

© 2025 Vagrantfile Generator. Built with ❤️ for developers.

## Navigation Links

- [Roadmap](#roadmap)
- [GitHub Repository](https://github.com/marekruzicka/vagrantfile-generator)
- [Support](#support)
EOF

# Internal pages
cat > backend/data/footer/roadmap.md << 'EOF'
# Roadmap

## Upcoming Features
- Advanced networking configuration
- Plugin system integration  
- Multi-provider support

## Timeline
- Q1 2025: Enhanced UI/UX improvements
- Q2 2025: Plugin ecosystem launch
- Q3 2025: Multi-cloud provider support
EOF

cat > backend/data/footer/support.md << 'EOF'
For technical support, please contact our team or visit the documentation.

We're here to help with any questions about Vagrant configuration.

## Contact Information
- Email: support@vagrantfile-generator.com
- Documentation: https://docs.vagrantfile-generator.com
- Community: https://community.vagrantfile-generator.com
EOF

# External link page (for GitHub)
cat > backend/data/footer/github.md << 'EOF'
# GitHub Repository

Visit our [GitHub repository](https://github.com/marekruzicka/vagrantfile-generator) for:

- Source code
- Issue tracking
- Contributing guidelines
- Release notes

This page redirects to our external GitHub repository.
EOF

# Hidden file (should be ignored by footer discovery)
echo "# Hidden Content - Should not appear in footer" > backend/data/footer/_hidden.md

echo -e "${GREEN}✅ Test environment setup complete${NC}"
echo ""

# Test footer API endpoints
echo -e "${BLUE}🔌 Testing Footer API Endpoints...${NC}"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
    
    # Test file discovery endpoint
    echo "Testing file discovery endpoint..."
    DISCOVERY_RESPONSE=$(curl -s http://localhost:8000/api/footer/files)
    if echo "$DISCOVERY_RESPONSE" | grep -q '"status":"success"'; then
        test_result "PASS" "Footer file discovery API responds successfully"
        
        # Count discovered files (should be 4: footer.md, roadmap.md, support.md, github.md)
        FILE_COUNT=$(echo "$DISCOVERY_RESPONSE" | grep -o '"filename"' | wc -l)
        if [ "$FILE_COUNT" -eq 4 ]; then
            test_result "PASS" "Correct number of files discovered ($FILE_COUNT)"
        else
            test_result "FAIL" "Expected 4 files, got $FILE_COUNT"
        fi
        
        # Test that hidden file is excluded (should be in excluded array, not files array)
        if echo "$DISCOVERY_RESPONSE" | grep -q '"excluded"' && echo "$DISCOVERY_RESPONSE" | grep -q '_hidden'; then
            test_result "PASS" "Hidden files correctly excluded"
        else
            test_result "FAIL" "Hidden files should be excluded"
        fi
        
    else
        test_result "FAIL" "Footer file discovery API failed"
    fi
    
    # Test content retrieval endpoint
    echo "Testing content retrieval endpoint..."
    CONTENT_RESPONSE=$(curl -s http://localhost:8000/api/footer/content/roadmap)
    if echo "$CONTENT_RESPONSE" | grep -q '"title":"Roadmap"'; then
        test_result "PASS" "Footer content retrieval API responds successfully"
    else
        test_result "FAIL" "Footer content retrieval API failed"
    fi
    
else
    echo -e "${YELLOW}⚠️  Backend not running, skipping API tests${NC}"
    echo -e "${YELLOW}   Start backend with: make dev-setup${NC}"
    test_result "SKIP" "Backend API tests (backend not running)"
fi

echo ""

# Test frontend integration
echo -e "${BLUE}🌐 Testing Frontend Integration...${NC}"

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
    
    # Check if footer component files exist
    if [ -f "frontend/src/components/footer.html" ]; then
        test_result "PASS" "Footer HTML template exists"
    else
        test_result "FAIL" "Footer HTML template missing"
    fi
    
    if [ -f "frontend/src/js/components/FooterComponent.js" ]; then
        test_result "PASS" "Footer Alpine.js component exists"
    else
        test_result "FAIL" "Footer Alpine.js component missing"
    fi
    
    if [ -f "frontend/src/styles/components/footer.css" ]; then
        test_result "PASS" "Footer CSS styles exist"
    else
        test_result "FAIL" "Footer CSS styles missing"
    fi
    
    # Check footer integration in main layout
    if grep -q "footer.html" frontend/src/index.html; then
        test_result "PASS" "Footer integrated in main layout"
    else
        test_result "FAIL" "Footer not integrated in main layout"
    fi
    
else
    echo -e "${YELLOW}⚠️  Frontend not running, limited integration tests${NC}"
    echo -e "${YELLOW}   Start frontend with: make dev-setup${NC}"
fi

echo ""

# Test file structure and content
echo -e "${BLUE}📂 Testing File Structure...${NC}"

# Check backend directory structure
if [ -d "backend/data/footer" ]; then
    test_result "PASS" "Backend footer directory exists"
else
    test_result "FAIL" "Backend footer directory missing"
fi

# Check API implementation
if [ -f "backend/src/api/footer.py" ]; then
    test_result "PASS" "Backend footer API implementation exists"
else
    test_result "FAIL" "Backend footer API implementation missing"
fi

# Check frontend models
for model in "FooterConfiguration.js" "StaticPage.js" "FooterNavigationLink.js"; do
    if [ -f "frontend/src/js/models/$model" ]; then
        test_result "PASS" "Frontend model $model exists"
    else
        test_result "FAIL" "Frontend model $model missing"
    fi
done

# Check frontend services  
for service in "FooterService.js" "MarkdownService.js"; do
    if [ -f "frontend/src/js/services/$service" ]; then
        test_result "PASS" "Frontend service $service exists"
    else
        test_result "FAIL" "Frontend service $service missing"
    fi
done

# Check router
if [ -f "frontend/src/js/router/StaticPageRouter.js" ]; then
    test_result "PASS" "Static page router exists"
else
    test_result "FAIL" "Static page router missing"
fi

# Check error page component
if [ -f "frontend/src/js/components/ErrorPageComponent.js" ]; then
    test_result "PASS" "Error page component exists"
else
    test_result "FAIL" "Error page component missing"
fi

echo ""

# Test CSS imports
echo -e "${BLUE}🎨 Testing CSS Integration...${NC}"

if grep -q "footer.css" frontend/src/styles/input.css; then
    test_result "PASS" "Footer CSS imported in main stylesheet"
else
    test_result "FAIL" "Footer CSS not imported in main stylesheet"
fi

if grep -q "error-page.css" frontend/src/styles/input.css; then
    test_result "PASS" "Error page CSS imported in main stylesheet"  
else
    test_result "FAIL" "Error page CSS not imported in main stylesheet"
fi

echo ""

# Performance and content validation
echo -e "${BLUE}⚡ Testing Performance & Content...${NC}"

# Check markdown content format
echo "Validating markdown content..."
for file in backend/data/footer/*.md; do
    if [ -f "$file" ] && [[ ! "$(basename "$file")" =~ ^_ ]]; then
        filename=$(basename "$file" .md)
        if [ -s "$file" ]; then
            test_result "PASS" "Content file $filename has content"
        else
            test_result "FAIL" "Content file $filename is empty"
        fi
    fi
done

# Check footer height matches header (py-4 instead of py-6)
if grep -q "py-4" frontend/src/components/footer.html; then
    test_result "PASS" "Footer height matches header (py-4)"
else
    test_result "FAIL" "Footer height should match header (py-4)"
fi

echo ""
echo "=================================="
echo -e "${BLUE}📊 Test Summary${NC}"
echo "=================================="
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Footer implementation is ready.${NC}"
    echo ""
    echo -e "${BLUE}📝 Manual Testing Guide:${NC}"
    echo "1. Open http://localhost:5173 in your browser"
    echo "2. Scroll to bottom - footer should be visible"
    echo "3. Click footer links to test navigation"
    echo "4. Test on mobile devices for responsiveness"
    echo "5. Check browser console for any JavaScript errors"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the implementation.${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Common fixes:${NC}"
    echo "- Run: make dev-setup (to start backend and frontend)"
    echo "- Check file permissions in backend/data/footer/"
    echo "- Verify CSS imports in frontend/src/styles/input.css"
    echo "- Check footer integration in frontend/src/index.html"
    echo ""
    exit 1
fi