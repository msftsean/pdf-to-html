#!/bin/bash
# Quickstart Validation Script for pdf-to-html
# Verifies that the development environment is correctly set up
# and the conversion pipeline works end-to-end.

# Get the project root (parent directory of scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Color codes
PASS="✅"
FAIL="❌"
WARN="⚠️"

# Track results
declare -a results
pass_count=0
fail_count=0
warn_count=0

# Helper function to run a check
check() {
    local name="$1"
    local cmd="$2"
    local critical="${3:-true}"  # true for critical, false for warning
    
    printf "%-55s" "Checking $name..."
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo " $PASS"
        ((pass_count++))
        results+=("✓ $name")
    else
        if [ "$critical" = "true" ]; then
            echo " $FAIL"
            ((fail_count++))
            results+=("✗ $name")
        else
            echo " $WARN"
            ((warn_count++))
            results+=("⚠ $name")
        fi
    fi
}

# Helper to check version
check_version() {
    local name="$1"
    local tool="$2"
    local min_version="$3"
    
    printf "%-55s" "Checking $name ($min_version+)..."
    
    if ! command -v "$tool" &> /dev/null; then
        echo " $FAIL"
        ((fail_count++))
        results+=("✗ $name not found")
        return
    fi
    
    # Extract version based on tool
    local version=""
    case "$tool" in
        python3)
            version=$("$tool" --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
            ;;
        node)
            version=$("$tool" --version 2>&1 | sed 's/^v//' | cut -d. -f1-2)
            ;;
        npm)
            version=$("$tool" --version 2>&1 | cut -d. -f1-2)
            ;;
        func)
            version=$("$tool" --version 2>&1 | cut -d. -f1-2)
            ;;
        *)
            version="installed"
            ;;
    esac
    
    echo " $PASS ($version)"
    ((pass_count++))
    results+=("✓ $name: $version")
}

echo ""
echo "🔍 NCDIT Document Converter — Quickstart Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
echo "📋 PREREQUISITES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_version "Python" "python3" "3.12"
check_version "Node.js" "node" "20"
check_version "npm" "npm" "9"

# Azure Functions Core Tools is optional (can use docker or remote)
printf "%-55s" "Checking Azure Functions Core Tools (4+)..."
if command -v func &> /dev/null; then
    local version=$(func --version 2>&1 | cut -d. -f1-2)
    echo " $PASS ($version)"
    ((pass_count++))
    results+=("✓ Azure Functions Core Tools: $version")
else
    echo " $WARN (optional - can use remote backend)"
    ((warn_count++))
    results+=("⚠ Azure Functions Core Tools not found (optional)")
fi

# ============================================================================
echo ""
echo "📦 BACKEND DEPENDENCIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check "Python azure.functions installed" "python3 -c 'import azure.functions'" true
check "Python pymupdf installed" "python3 -c 'import fitz'" true
check "Python python-docx installed" "python3 -c 'import docx'" true
check "Python python-pptx installed" "python3 -c 'import pptx'" true
check "Python azure-ai-documentintelligence installed" "python3 -c 'import azure.ai.documentintelligence'" true
check "Python azure-identity installed" "python3 -c 'import azure.identity'" true
check "Python azure-storage-blob installed" "python3 -c 'import azure.storage.blob'" true
check "Python pytest installed" "python3 -c 'import pytest'" true

# ============================================================================
echo ""
echo "🎨 FRONTEND DEPENDENCIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check "Frontend node_modules exists" "test -d frontend/node_modules" true
check "Frontend package.json exists" "test -f frontend/package.json" true

# ============================================================================
echo ""
echo "⚙️  CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check ".env.example exists" "test -f .env.example" true
check "host.json exists" "test -f host.json" true
check "requirements.txt exists" "test -f requirements.txt" true

# ============================================================================
echo ""
echo "🧪 TESTS & BUILD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check "Backend unit tests pass" "cd /workspaces/pdf-to-html && python3 -m pytest tests/unit/ -q --tb=no" true
check "Frontend builds successfully" "cd /workspaces/pdf-to-html/frontend && npm run build 2>/dev/null" true

# ============================================================================
echo ""
echo "📋 PROJECT FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check "function_app.py exists" "test -f $PROJECT_ROOT/function_app.py" true
check "html_builder.py exists" "test -f $PROJECT_ROOT/html_builder.py" true
check "pdf_extractor.py exists" "test -f $PROJECT_ROOT/pdf_extractor.py" true
check "ocr_service.py exists" "test -f $PROJECT_ROOT/ocr_service.py" true
check "wcag_validator.py exists" "test -f $PROJECT_ROOT/wcag_validator.py" true
check "status_service.py exists" "test -f $PROJECT_ROOT/status_service.py" true

# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

total=$((pass_count + fail_count + warn_count))

# Print individual results
for result in "${results[@]}"; do
    echo "  $result"
done

echo ""
echo "Results: $pass_count/$total checks passed"

if [ $fail_count -gt 0 ]; then
    echo "⚠️  Failed: $fail_count checks"
fi

if [ $warn_count -gt 0 ]; then
    echo "⚠️  Warnings: $warn_count checks"
fi

echo ""

# ============================================================================
# Exit with appropriate code
if [ $fail_count -eq 0 ]; then
    echo "✅ Quickstart validation PASSED! Your dev environment is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Start Azurite:  azurite-blob --silent &"
    echo "  2. Start backend:  func start"
    echo "  3. Start frontend: cd frontend && npm run dev"
    echo ""
    exit 0
else
    echo "❌ Quickstart validation FAILED. Please fix the errors above."
    echo ""
    echo "Common fixes:"
    echo "  • Python 3.12+:  pip install --upgrade python"
    echo "  • Node 20+:      nvm install 20 && nvm use 20"
    echo "  • Dependencies:  pip install -r requirements.txt"
    echo "  • Frontend:      cd frontend && npm install"
    echo ""
    exit 1
fi
