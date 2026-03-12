// ──────────────────────────────────────────────────────────────
// prod.bicepparam — Production environment parameters
// ──────────────────────────────────────────────────────────────
using '../main.bicep'

param environmentName = 'prod'
param location = 'eastus'
param storageAccountName = 'stpdftohtml331ef3'
param storageAccountResourceGroup = 'rg-pdftohtml'
param documentIntelligenceEndpoint = ''
param imageTag = 'latest'
