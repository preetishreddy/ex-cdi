---
title: "API Gateway Runbook"
space: "Payments Platform"
author: "Marcus Thompson"
created: "2025-05-10"
last_updated: "2026-01-06"
labels: ["api-gateway", "runbook", "operations", "troubleshooting"]
version: 7
---

# API Gateway Runbook

## Overview

The Payments Platform API Gateway is the single entry point for all external API traffic. It handles authentication, request routing, logging, and basic request validation. The gateway runs on AWS API Gateway backed by a Lambda authorizer for API key validation.

## Architecture

- **API Gateway**: AWS API Gateway (REST API type)
- **Authorizer**: Lambda function that validates merchant API keys against DynamoDB
- **Rate Limiting**: Currently handled at the AWS API Gateway level with a default of 1,000 requests per minute per API key
- **Logging**: All requests are logged to CloudWatch Logs with a 30-day retention policy

## Common Issues and Troubleshooting

### 1. 429 Too Many Requests

**Symptom**: Merchants report receiving 429 errors.

**Resolution**: Check the merchant's current rate limit in API Gateway. If the merchant has a legitimate need for higher throughput, update their usage plan in API Gateway console. Requires approval from James O'Brien for limits above 5,000 req/min.

### 2. 502 Bad Gateway

**Symptom**: Intermittent 502 errors on specific endpoints.

**Resolution**: Usually indicates a timeout in the downstream service. Check ECS task health for the target service. If the billing service is the target, check the database connection pool (see Dave Rossi for billing-specific issues). Increase the integration timeout if the downstream operation is legitimately slow.

### 3. 401 Unauthorized

**Symptom**: Merchants report authentication failures with valid API keys.

**Resolution**: Check the Lambda authorizer logs in CloudWatch. Common cause is a DynamoDB read throttle during high-traffic periods. If DynamoDB is throttled, increase the provisioned read capacity or switch to on-demand mode.

### 4. High Latency (>2s p99)

**Symptom**: API response times exceed SLA thresholds.

**Resolution**: Check CloudWatch metrics for the specific endpoint. If latency is concentrated on billing endpoints, check PostgreSQL query performance via RDS Performance Insights. For dashboard endpoints, check the frontend API service ECS task metrics.

## On-Call Procedures

The API Gateway is monitored 24/7 via Datadog. Alerts fire to the #payments-alerts Slack channel. The on-call rotation is managed in PagerDuty.

### Escalation Path

1. On-call engineer investigates and attempts resolution
2. If unresolved within 30 minutes, escalate to the service owner (see ownership matrix below)
3. If customer-facing impact exceeds 1 hour, escalate to James O'Brien

### Service Ownership Matrix

| Service | Primary Owner | Backup |
|---------|--------------|--------|
| API Gateway / Lambda Authorizer | Marcus Thompson | Sarah Chen |
| Billing Service | Dave Rossi | Lisa Park |
| Merchant Dashboard API | Priya Sharma | Lisa Park |
| Infrastructure / ECS / RDS | Marcus Thompson | Sarah Chen |

## Maintenance Windows

Planned maintenance is performed on Sundays between 2 AM – 6 AM EST. All maintenance must be announced 48 hours in advance in #payments-platform.

## Contact

For API Gateway issues, contact Marcus Thompson. For billing-specific API issues, contact Dave Rossi.
