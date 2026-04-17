---
name: RAP Handler 404 Error Incident
description: Incident where RAP handler methods were not accessible via OData
type: project
scope: project:REPO_NAME
source: incident
# Trust Metadata - Incident Record
source_type: incident
approval_status: draft
confidence: 0.5
owner: developer-team
created_at: 1713558000
# Domain Tags
domain_tags:
  - RAP
  - CDS
  - OData
  - ABAP_Cloud
  - bug
---

# RAP Handler 404 Error Incident

## Problem

When calling OData service endpoints, received 404 errors for handler methods that were defined in the behavior definition.

## Root Cause

The handler methods were not properly exposed in the service binding. The `@EndUserText.label` annotation was missing on the behavior definition, causing the service binding to skip the handler registration.

## Solution

1. Add `@EndUserText.label` annotation to behavior definition
2. Re-deploy the service binding
3. Clear OData cache

```abap
@EndUserText.label: 'Travel Handler'
define behavior for ZI_TRAVEL
persistent table ztravel
// handler methods now accessible
```

## Prevention

- Always validate service binding after behavior changes
- Include OData service in integration test suite
- Document all handler methods in ADR
