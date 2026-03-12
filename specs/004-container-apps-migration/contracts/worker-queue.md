# API Contract: Queue Worker Protocol

**New for Container Apps** — replaces Azure Functions blob trigger
**Contract status**: New

## Overview

The worker process consumes messages from the `conversion-jobs` Azure
Storage Queue. Each message represents a file uploaded to the `files/`
container that needs conversion.

## Queue Message Format

Messages are placed on the queue by an Event Grid subscription that
transforms `BlobCreated` events. The worker parses the Event Grid event
envelope to extract the blob reference.

### Event Grid Event Envelope (as stored in queue)

```json
{
  "id": "unique-event-id",
  "eventType": "Microsoft.Storage.BlobCreated",
  "subject": "/blobServices/default/containers/files/blobs/abc123.pdf",
  "data": {
    "api": "PutBlob",
    "contentType": "application/pdf",
    "contentLength": 2048576,
    "blobType": "BlockBlob",
    "url": "https://stpdftohtml331ef3.blob.core.windows.net/files/abc123.pdf"
  },
  "eventTime": "2026-06-15T10:00:00Z"
}
```

### Parsed Fields Used by Worker

| Field | Source | Description |
|-------|--------|-------------|
| blob_name | `subject` (parsed) | e.g., `abc123.pdf` |
| container | `subject` (parsed) | Always `files` |
| content_type | `data.contentType` | MIME type |
| size_bytes | `data.contentLength` | File size |
| blob_url | `data.url` | Full blob URL |
| timestamp | `eventTime` | Event time |

## Worker Processing Flow

```
1. Dequeue message (visibility timeout = 5 min)
2. Parse Event Grid event → extract blob_name
3. Extract document_id from blob_name (strip extension)
4. Read blob data from files/{blob_name}
5. Read blob metadata → get document_id, format, etc.
6. Set status = "processing"
7. Run conversion pipeline:
   a. Detect file type → route to extractor
   b. Extract content → PageResult[]
   c. Detect scanned pages → OCR if needed
   d. Build HTML → html_builder.build_html()
   e. Validate WCAG → wcag_validator.validate_html()
   f. Upload output to converted/{doc_id}/
   g. Set status = "completed" with metadata
8. Delete queue message (success)
9. On error:
   a. Set status = "failed" with error_message
   b. Do NOT delete message → will retry after visibility timeout
   c. After 3 retries → message moves to poison queue
```

## Queue Configuration

| Property | Value |
|----------|-------|
| Queue name | `conversion-jobs` |
| Visibility timeout | 300 seconds (5 minutes) |
| Message TTL | 604,800 seconds (7 days) |
| Max dequeue count | 3 |
| Poison queue | `conversion-jobs-poison` (auto-created) |

## KEDA Scale Rule

```yaml
scale:
  minReplicas: 0
  maxReplicas: 10
  rules:
    - name: queue-based-scaling
      custom:
        type: azure-queue
        metadata:
          queueName: conversion-jobs
          queueLength: "1"
          connectionFromEnv: AZURE_STORAGE_CONNECTION_STRING
```

## Local Development

In local development (docker-compose), the worker runs a simple polling
loop against the Azurite queue:

```python
while True:
    messages = queue_client.receive_messages(max_messages=1, visibility_timeout=300)
    for msg in messages:
        process_message(msg)
        queue_client.delete_message(msg)
    time.sleep(2)  # Poll interval
```

KEDA is not needed locally — the polling loop provides the same behavior.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Blob not found | Log warning, delete message (stale event) |
| Unsupported format | Set status = failed, delete message |
| Extraction error | Set status = failed, leave message for retry |
| OCR service unavailable | Set status = failed, leave message for retry |
| Upload output fails | Set status = failed, leave message for retry |
| Poison queue (3 retries) | Message in `conversion-jobs-poison`, alerting |
