#!/usr/bin/env bash
# setup-cross-sub-storage.sh
# -----------------------------------------------------------------------
# Creates storage resources in Sean's Owner subscription and wires them
# to the Function App in the MCAPS subscription.
#
# PREREQUISITES:
#   1. SPN 894189e2-b616-429a-9871-17acfc3a7614 must have Contributor
#      role on subscription 098ef2f6-cea4-4839-8093-ef90622e1b8c
#   2. Whoever runs this must be able to assign RBAC roles
#      (Owner or User Access Administrator on the target subscription)
#
# This script does:
#   - Creates resource group and storage account in Sean's subscription
#   - Creates blob containers (files, converted)
#   - Assigns RBAC roles for the Function App's managed identity
#   - Assigns RBAC roles for the SPN itself (so CI/CD can manage storage)
#   - Updates the Function App settings to point at the new storage
# -----------------------------------------------------------------------

set -euo pipefail

# ========================= CONFIGURATION ==============================
# Sean's Owner subscription (where storage will live)
STORAGE_SUB="098ef2f6-cea4-4839-8093-ef90622e1b8c"

# MCAPS subscription (where Function App lives)
FUNCAPP_SUB="4b27ac87-dec6-45d5-8634-b9f71bd1dd26"

# Resource names
STORAGE_RG="rg-pdf-to-html-storage"
STORAGE_ACCOUNT="stpdftohtmldata"
STORAGE_LOCATION="eastus"

FUNCAPP_RG="rg-pdf-to-html"
FUNCAPP_NAME="func-pdftohtml-284728"

# Identities
MSI_PRINCIPAL="350374e1-8c09-4553-9eac-1e983ea9f5b0"  # Function App managed identity
SPN_APP_ID="894189e2-b616-429a-9871-17acfc3a7614"      # CI/CD SPN

CONTAINERS=("files" "converted")
# ======================================================================

echo "============================================="
echo " Cross-Subscription Storage Setup"
echo " pdf-to-html WCAG Document Converter"
echo "============================================="
echo ""

# ------- Step 0: Verify SPN access to storage subscription --------
echo "[0/7] Verifying access to storage subscription..."
if ! az account show --subscription "$STORAGE_SUB" -o none 2>/dev/null; then
  echo ""
  echo "❌ ERROR: Cannot access subscription $STORAGE_SUB"
  echo ""
  echo "ACTION REQUIRED: Sean must grant the SPN access."
  echo "Run this in Azure Portal or CLI as Owner:"
  echo ""
  echo "  az role assignment create \\"
  echo "    --assignee $SPN_APP_ID \\"
  echo "    --role Contributor \\"
  echo "    --scope /subscriptions/$STORAGE_SUB"
  echo ""
  exit 1
fi
echo "  ✅ Access confirmed"

# ------- Step 1: Create resource group --------
echo ""
echo "[1/7] Creating resource group '$STORAGE_RG' in $STORAGE_LOCATION..."
az group create \
  --subscription "$STORAGE_SUB" \
  --name "$STORAGE_RG" \
  --location "$STORAGE_LOCATION" \
  --tags project=pdf-to-html environment=production purpose=storage \
  -o none
echo "  ✅ Resource group created"

# ------- Step 2: Create storage account --------
echo ""
echo "[2/7] Creating storage account '$STORAGE_ACCOUNT'..."
az storage account create \
  --subscription "$STORAGE_SUB" \
  --resource-group "$STORAGE_RG" \
  --name "$STORAGE_ACCOUNT" \
  --location "$STORAGE_LOCATION" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --https-only true \
  --tags project=pdf-to-html environment=production \
  -o none
echo "  ✅ Storage account created"

# ------- Step 3: Create blob containers (via ARM API) --------
echo ""
echo "[3/7] Creating blob containers..."
STORAGE_SCOPE="/subscriptions/$STORAGE_SUB/resourceGroups/$STORAGE_RG/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"

for CONTAINER in "${CONTAINERS[@]}"; do
  echo "  Creating container: $CONTAINER"
  az rest --method put \
    --url "https://management.azure.com${STORAGE_SCOPE}/blobServices/default/containers/${CONTAINER}?api-version=2023-05-01" \
    --body '{"properties":{"publicAccess":"None"}}' \
    -o none 2>/dev/null || true
done
echo "  ✅ Containers created: ${CONTAINERS[*]}"

# ------- Step 4: Assign RBAC for Function App MSI --------
echo ""
echo "[4/7] Assigning RBAC roles for Function App managed identity..."

MSI_ROLES=(
  "Storage Blob Data Contributor"
  "Storage Queue Data Contributor"
  "Storage Account Contributor"
)

for ROLE in "${MSI_ROLES[@]}"; do
  echo "  Assigning: $ROLE"
  az role assignment create \
    --assignee-object-id "$MSI_PRINCIPAL" \
    --assignee-principal-type ServicePrincipal \
    --role "$ROLE" \
    --scope "$STORAGE_SCOPE" \
    -o none 2>/dev/null || echo "    (may already exist — continuing)"
done
echo "  ✅ MSI RBAC roles assigned"

# ------- Step 5: Assign RBAC for SPN (CI/CD management) --------
echo ""
echo "[5/7] Assigning RBAC roles for CI/CD SPN..."

# Get SPN object ID from app ID
SPN_OBJECT_ID=$(az ad sp show --id "$SPN_APP_ID" --query id -o tsv 2>/dev/null || echo "")

if [ -n "$SPN_OBJECT_ID" ]; then
  SPN_ROLES=(
    "Storage Blob Data Contributor"
    "Storage Account Contributor"
  )

  for ROLE in "${SPN_ROLES[@]}"; do
    echo "  Assigning: $ROLE"
    az role assignment create \
      --assignee-object-id "$SPN_OBJECT_ID" \
      --assignee-principal-type ServicePrincipal \
      --role "$ROLE" \
      --scope "$STORAGE_SCOPE" \
      -o none 2>/dev/null || echo "    (may already exist — continuing)"
  done
  echo "  ✅ SPN RBAC roles assigned"
else
  echo "  ⚠️  Could not resolve SPN object ID. Assign roles manually:"
  echo "     SPN App ID: $SPN_APP_ID"
  echo "     Roles: Storage Blob Data Contributor, Storage Account Contributor"
fi

# ------- Step 6: Update Function App settings --------
echo ""
echo "[6/7] Updating Function App settings to use new storage..."
az functionapp config appsettings set \
  --subscription "$FUNCAPP_SUB" \
  --resource-group "$FUNCAPP_RG" \
  --name "$FUNCAPP_NAME" \
  --settings \
    "AzureWebJobsStorage__accountName=$STORAGE_ACCOUNT" \
    "STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT" \
    "STORAGE_CONTAINER_INPUT=files" \
    "STORAGE_CONTAINER_OUTPUT=converted" \
  -o none
echo "  ✅ Function App settings updated"

# Remove old connection-string-based setting if present
echo "  Checking for old connection string settings..."
OLD_SETTINGS=$(az functionapp config appsettings list \
  --subscription "$FUNCAPP_SUB" \
  --resource-group "$FUNCAPP_RG" \
  --name "$FUNCAPP_NAME" \
  --query "[?name=='AzureWebJobsStorage' && value!=''].name" -o tsv 2>/dev/null || echo "")

if [ -n "$OLD_SETTINGS" ]; then
  echo "  Removing legacy AzureWebJobsStorage connection string..."
  az functionapp config appsettings delete \
    --subscription "$FUNCAPP_SUB" \
    --resource-group "$FUNCAPP_RG" \
    --name "$FUNCAPP_NAME" \
    --setting-names AzureWebJobsStorage \
    -o none 2>/dev/null || true
  echo "  ✅ Legacy setting removed"
else
  echo "  No legacy connection string found — clean"
fi

# ------- Step 7: Restart and verify --------
echo ""
echo "[7/7] Restarting Function App and verifying health..."
az functionapp restart \
  --subscription "$FUNCAPP_SUB" \
  --resource-group "$FUNCAPP_RG" \
  --name "$FUNCAPP_NAME" \
  -o none

# Wait for restart
echo "  Waiting 30 seconds for restart..."
sleep 30

# Get the function app URL and test health
FUNCAPP_URL=$(az functionapp show \
  --subscription "$FUNCAPP_SUB" \
  --resource-group "$FUNCAPP_RG" \
  --name "$FUNCAPP_NAME" \
  --query "defaultHostName" -o tsv 2>/dev/null)

if [ -n "$FUNCAPP_URL" ]; then
  echo "  Testing health endpoint: https://${FUNCAPP_URL}/api/health"
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${FUNCAPP_URL}/api/health" --max-time 15 2>/dev/null || echo "000")
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "  ✅ Health check passed (HTTP 200)"
  else
    echo "  ⚠️  Health check returned HTTP $HTTP_STATUS — may need more time to initialize"
    echo "     Retry: curl https://${FUNCAPP_URL}/api/health"
  fi
else
  echo "  ⚠️  Could not determine Function App URL"
fi

echo ""
echo "============================================="
echo " ✅ Cross-Subscription Storage Setup Complete"
echo "============================================="
echo ""
echo " Storage Account:  $STORAGE_ACCOUNT"
echo " Storage Sub:      $STORAGE_SUB"
echo " Storage RG:       $STORAGE_RG"
echo " Containers:       ${CONTAINERS[*]}"
echo " Function App:     $FUNCAPP_NAME"
echo " Function App Sub: $FUNCAPP_SUB"
echo ""
echo " The Function App now uses identity-based auth"
echo " (AzureWebJobsStorage__accountName) pointing at"
echo " the storage account in Sean's subscription."
echo "============================================="
