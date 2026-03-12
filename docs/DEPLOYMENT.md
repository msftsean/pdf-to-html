# Azure Deployment Guide

## Production Environment: Cloudforce Sponsorship

**Status:** ✅ DEPLOYED AND OPERATIONAL  
**Deployment Date:** 2026-03-12  
**Subscription:** Cloudforce Sponsorship (`098ef2f6-cea4-4839-8093-ef90622e1b8c`)

## Resource Overview

| Resource | Name | Details |
|----------|------|---------|
| **Resource Group** | `rg-pdf-to-html` | Location: `eastus` |
| **Storage Account** | `stpdftohtml331ef3` | Standard_LRS, shared key enabled |
| **Containers** | `files`, `converted` | For uploads and converted outputs |
| **App Service Plan** | `plan-pdftohtml` | B1 Linux |
| **Function App** | `func-pdftohtml-331ef3` | Python 3.12, Functions v4 |
| **Function URL** | `https://func-pdftohtml-331ef3.azurewebsites.net` | Public endpoint |
| **Application Insights** | `func-pdftohtml-331ef3` | Monitoring enabled |

## Authentication

The Function App uses:
- **Storage**: Connection string (shared key access)
- **Identity**: System-assigned managed identity with RBAC roles:
  - Storage Blob Data Contributor
  - Storage Queue Data Contributor
  - Storage Account Contributor

## Deployment Commands

### View Resources
```bash
# List all resources in the resource group
az resource list --resource-group rg-pdf-to-html --output table

# Check function app status
az functionapp show --name func-pdftohtml-331ef3 --resource-group rg-pdf-to-html

# View app settings
az functionapp config appsettings list --name func-pdftohtml-331ef3 --resource-group rg-pdf-to-html
```

### Deploy Code
```bash
# Deploy function app code (from repo root)
func azure functionapp publish func-pdftohtml-331ef3 --python
```

### View Logs
```bash
# Stream live logs
az functionapp log tail --name func-pdftohtml-331ef3 --resource-group rg-pdf-to-html

# View Application Insights logs in portal
az portal show --resource /subscriptions/098ef2f6-cea4-4839-8093-ef90622e1b8c/resourceGroups/rg-pdf-to-html/providers/microsoft.insights/components/func-pdftohtml-331ef3
```

## Next Steps

1. **Configure OCR Service**: Set up Azure Document Intelligence endpoint
2. **Deploy Frontend**: Azure Static Web Apps or App Service
3. **CI/CD Pipeline**: GitHub Actions workflow for automated deployments
4. **Custom Domain**: Configure custom domain and SSL certificate
5. **Monitoring**: Set up alerts for errors, performance, and usage

## Support

For deployment issues, contact Cyborg (DevOps).  
For application issues, contact Wonder-Woman (Backend) or Flash (Frontend).

## Reference Files

- `.env.cloudforce` - Environment variables (NOT committed to git)
- `.squad/agents/cyborg/history.md` - Deployment history and learnings
- `.squad/decisions/inbox/cyborg-cloudforce-deploy.md` - Deployment decision record
