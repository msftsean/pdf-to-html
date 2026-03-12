// ──────────────────────────────────────────────────────────────
// container-registry.bicep — Azure Container Registry (Basic SKU)
//
// Admin access disabled — apps pull via managed identity (AcrPull).
// ──────────────────────────────────────────────────────────────

@description('Name of the container registry')
param name string

@description('Azure region')
param location string = resourceGroup().location

// ── Container Registry ────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    policies: {
      retentionPolicy: {
        status: 'disabled'     // Basic SKU doesn't support retention policies
      }
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────

output id string = acr.id
output name string = acr.name
output loginServer string = acr.properties.loginServer
