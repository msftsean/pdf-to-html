#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# run_evals.sh — End-to-end evaluation pipeline wrapper
#
# Starts Azurite (if needed), creates blob containers,
# runs the eval suite, and renders the Markdown report.
#
# Usage:
#   ./scripts/run_evals.sh            # full pipeline
#   ./scripts/run_evals.sh --stdout   # print report to stdout
#
# Idempotent: safe to run multiple times.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVAL_RESULTS_DIR="$PROJECT_ROOT/tests/eval/results"
EVAL_JSON="$EVAL_RESULTS_DIR/eval-report.json"
EVAL_MD="$EVAL_RESULTS_DIR/eval-report.md"

AZURITE_BLOB_PORT=10000
AZURITE_QUEUE_PORT=10001
AZURITE_TABLE_PORT=10002
AZURITE_PID=""

BLOB_CONN_STR="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:${AZURITE_BLOB_PORT}/devstoreaccount1;"

# ── Colours ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}ℹ ${NC}$*"; }
ok()    { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️ ${NC}$*"; }
err()   { echo -e "${RED}❌${NC} $*" >&2; }

# ── 1. Azurite ───────────────────────────────────────────────
start_azurite() {
    if nc -z 127.0.0.1 "$AZURITE_BLOB_PORT" 2>/dev/null; then
        ok "Azurite already running on port $AZURITE_BLOB_PORT"
        return 0
    fi

    info "Starting Azurite blob storage emulator..."
    if ! command -v azurite &>/dev/null; then
        info "Installing azurite via npm..."
        npm install -g azurite 2>/dev/null || {
            err "Failed to install azurite. Install manually: npm install -g azurite"
            return 1
        }
    fi

    local azurite_data="$PROJECT_ROOT/.azurite"
    mkdir -p "$azurite_data"

    azurite --silent \
        --blobPort "$AZURITE_BLOB_PORT" \
        --queuePort "$AZURITE_QUEUE_PORT" \
        --tablePort "$AZURITE_TABLE_PORT" \
        --location "$azurite_data" &
    AZURITE_PID=$!

    # Wait for Azurite to be ready (up to 10 seconds)
    local attempts=0
    while ! nc -z 127.0.0.1 "$AZURITE_BLOB_PORT" 2>/dev/null; do
        sleep 1
        attempts=$((attempts + 1))
        if [ $attempts -ge 10 ]; then
            err "Azurite failed to start within 10 seconds"
            return 1
        fi
    done

    ok "Azurite started (PID=$AZURITE_PID)"
}

# ── 2. Create blob containers ────────────────────────────────
create_containers() {
    info "Ensuring blob containers exist..."

    local containers=("uploads" "results")
    for container in "${containers[@]}"; do
        # Use python + azure-storage-blob (already in requirements.txt)
        python3 -c "
from azure.storage.blob import BlobServiceClient
try:
    client = BlobServiceClient.from_connection_string('$BLOB_CONN_STR')
    client.create_container('$container')
    print('  Created container: $container')
except Exception as e:
    if 'ContainerAlreadyExists' in str(e):
        print('  Container exists: $container')
    else:
        print(f'  Container $container: {e}')
" 2>/dev/null || true
    done

    ok "Blob containers ready"
}

# ── 3. Run eval suite ───────────────────────────────────────
run_evals() {
    info "Running evaluation suite..."
    mkdir -p "$EVAL_RESULTS_DIR"

    export AZURE_STORAGE_CONNECTION_STRING="$BLOB_CONN_STR"

    python3 "$SCRIPT_DIR/run_evals.py" \
        --output "$EVAL_JSON" \
        || true  # Don't exit on FAIL — we want to render the report

    if [ ! -f "$EVAL_JSON" ]; then
        err "Eval JSON not generated at $EVAL_JSON"
        return 1
    fi

    ok "Eval JSON saved to $EVAL_JSON"
}

# ── 4. Render report ────────────────────────────────────────
render_report() {
    info "Rendering Markdown report..."

    # Ensure jinja2 is installed
    python3 -c "import jinja2" 2>/dev/null || {
        info "Installing jinja2..."
        pip install jinja2 --quiet
    }

    local render_args=("--input" "$EVAL_JSON" "--output" "$EVAL_MD")

    # Pass --stdout if requested
    if [[ "${1:-}" == "--stdout" ]]; then
        render_args=("--input" "$EVAL_JSON" "--stdout")
    fi

    python3 "$SCRIPT_DIR/render_report.py" "${render_args[@]}"
    local exit_code=$?

    if [[ "${1:-}" != "--stdout" ]] && [ -f "$EVAL_MD" ]; then
        ok "Report rendered to $EVAL_MD"
    fi

    return $exit_code
}

# ── Cleanup ──────────────────────────────────────────────────
cleanup() {
    if [ -n "$AZURITE_PID" ] && kill -0 "$AZURITE_PID" 2>/dev/null; then
        info "Stopping Azurite (PID=$AZURITE_PID)..."
        kill "$AZURITE_PID" 2>/dev/null || true
        wait "$AZURITE_PID" 2>/dev/null || true
    fi
}

# ── Main ─────────────────────────────────────────────────────
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  WCAG Evaluation Pipeline"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    trap cleanup EXIT

    start_azurite
    create_containers
    run_evals
    render_report "${1:-}"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Pipeline complete"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

main "$@"
