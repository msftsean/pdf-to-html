#!/usr/bin/env bash
# assign-storage-rbac.sh
# -----------------------------------------------------------------------
# Assigns required RBAC roles to the Function App's managed identity
# so it can access the storage account via identity-based auth.
#
# UPDATED: Now targets the cross-subscription storage account in Sean's
# Owner subscription (098ef2f6-...) instead of the MCAPS subscription.
#
# REQUIRES: Owner or User Access Administrator role on the storage account.
# The Contributor SPN cannot run this — an admin (Sean) must execute it.
#
# For the full cross-subscription setup (resource group, storage account,
# containers, RBAC, Function App settings), use:
#   scripts/setup-cross-sub-storage.sh
# -----------------------------------------------------------------------

set -euo pipefail

# Function App managed identity
MSI_PRINCIPAL="350374e1-8c09-4553-9eac-1e983ea9f5b0"

# CI/CD SPN
SPN_APP_ID="894189e2-b616-429a-9871-17acfc3a7614"

# Cross-subscription storage (Sean's Owner subscription)
STORAGE_SUB="098ef2f6-cea4-4839-8093-ef90622e1b8c"
STORAGE_RG="rg-pdf-to-html-storage"
STORAGE_ACCOUNT="stpdftohtmldata"
STORAGE_SCOPE="/subscriptions/${STORAGE_SUB}/resourceGroups/${STORAGE_RG}/providers/Microsoft.Storage/storageAccounts/${STORAGE_ACCOUNT}"

echo "============================================="
echo " RBAC Role Assignment for pdf-to-html"
echo " Cross-Subscription Storage Setup"
echo "============================================="
echo ""
echo "Storage scope: $STORAGE_SCOPE"
echo ""

# ---- MSI Roles (Function App) ----
echo "Assigning RBAC roles to Function App MSI ($MSI_PRINCIPAL)..."

# Storage Blob Data Contributor — read/write/delete blobs
az role assignment create \
  --assignee-object-id "$MSI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_SCOPE" \
  -o none 2>/dev/null || echo "  (Storage Blob Data Contributor may already exist)"

# Storage Blob Delegator — required for user-delegation SAS tokens
# (identity-based auth generates SAS via UserDelegationKey, not account key)
az role assignment create \
  --assignee-object-id "$MSI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Delegator" \
  --scope "$STORAGE_SCOPE" \
  -o none 2>/dev/null || echo "  (Storage Blob Delegator may already exist)"

# Storage Queue Data Contributor — Azure Functions uses queues internally
az role assignment create \
  --assignee-object-id "$MSI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Queue Data Contributor" \
  --scope "$STORAGE_SCOPE" \
  -o none 2>/dev/null || echo "  (Storage Queue Data Contributor may already exist)"

# Storage Account Contributor — manage storage account settings
az role assignment create \
  --assignee-object-id "$MSI_PRINCIPAL" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Account Contributor" \
  --scope "$STORAGE_SCOPE" \
  -o none 2>/dev/null || echo "  (Storage Account Contributor may already exist)"

echo "  ✅ MSI roles assigned"

# ---- SPN Roles (CI/CD) ----
echo ""
echo "Assigning RBAC roles to CI/CD SPN ($SPN_APP_ID)..."

SPN_OBJECT_ID=$(az ad sp show --id "$SPN_APP_ID" --query id -o tsv 2>/dev/null || echo "")

if [ -n "$SPN_OBJECT_ID" ]; then
  az role assignment create \
    --assignee-object-id "$SPN_OBJECT_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "Storage Blob Data Contributor" \
    --scope "$STORAGE_SCOPE" \
    -o none 2>/dev/null || echo "  (Storage Blob Data Contributor may already exist)"

  az role assignment create \
    --assignee-object-id "$SPN_OBJECT_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "Storage Account Contributor" \
    --scope "$STORAGE_SCOPE" \
    -o none 2>/dev/null || echo "  (Storage Account Contributor may already exist)"

  echo "  ✅ SPN roles assigned"
else
  echo "  ⚠️  Could not resolve SPN object ID — assign manually"
fi

echo ""
echo "Done. Restart the function app to apply:"
echo "  az functionapp restart --name func-pdftohtml-284728 --resource-group rg-pdf-to-html --subscription 4b27ac87-dec6-45d5-8634-b9f71bd1dd26"
