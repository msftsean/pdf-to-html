// ──────────────────────────────────────────────────────────────
// event-grid.bicep — Event Grid System Topic + Subscription
//
// Watches for BlobCreated events on the "files" container and
// routes them to the "conversion-jobs" Storage Queue.
// ──────────────────────────────────────────────────────────────

@description('Azure region')
param location string = resourceGroup().location

@description('Existing storage account name')
param storageAccountName string

@description('Resource group of the existing storage account')
param storageAccountResourceGroup string

// ── Variables ─────────────────────────────────────────────────

var topicName = 'evgt-pdftohtml-blobcreated'
var subscriptionName = 'evgs-files-to-queue'
var queueName = 'conversion-jobs'

// ── Existing Storage Account ──────────────────────────────────

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
  scope: resourceGroup(storageAccountResourceGroup)
}

// ── Storage Queue (ensure it exists) ──────────────────────────

resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-05-01' existing = {
  name: 'default'
  parent: storageAccount
}

resource conversionQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: queueName
  parent: queueService
}

// ── Event Grid System Topic ───────────────────────────────────

resource systemTopic 'Microsoft.EventGrid/systemTopics@2024-06-01-preview' = {
  name: topicName
  location: location
  properties: {
    source: storageAccount.id
    topicType: 'Microsoft.Storage.StorageAccounts'
  }
}

// ── Event Grid Subscription ──────────────────────────────────

resource subscription 'Microsoft.EventGrid/systemTopics/eventSubscriptions@2024-06-01-preview' = {
  name: subscriptionName
  parent: systemTopic
  properties: {
    destination: {
      endpointType: 'StorageQueue'
      properties: {
        resourceId: storageAccount.id
        queueName: queueName
        queueMessageTimeToLiveInSeconds: 604800  // 7 days
      }
    }
    filter: {
      includedEventTypes: [
        'Microsoft.Storage.BlobCreated'
      ]
      subjectBeginsWith: '/blobServices/default/containers/files/'
      advancedFilters: [
        {
          operatorType: 'NumberGreaterThan'
          key: 'data.contentLength'
          value: 0
        }
      ]
    }
    eventDeliverySchema: 'EventGridSchema'
    retryPolicy: {
      maxDeliveryAttempts: 5
      eventTimeToLiveInMinutes: 1440  // 24 hours
    }
  }
  dependsOn: [conversionQueue]
}

// ── Outputs ───────────────────────────────────────────────────

output systemTopicId string = systemTopic.id
output subscriptionId string = subscription.id
