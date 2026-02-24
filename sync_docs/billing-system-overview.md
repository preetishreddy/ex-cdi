---
title: "Legacy Billing System Overview"
space: "Payments Platform"
author: "Dave Rossi"
created: "2025-01-20"
last_updated: "2025-08-05"
labels: ["billing", "architecture", "legacy", "stripe"]
version: 5
---

# Legacy Billing System Overview

## Purpose

The legacy billing system (`legacy_billing`) handles all recurring subscription billing, one-time charges, and refund processing for the Meridian Technologies platform. It is the oldest and most critical module in the Payments Platform.

## Architecture

The billing system is a Python-based service running on ECS. It integrates directly with Stripe for payment processing and maintains its own PostgreSQL database for billing state, invoice records, and audit logs.

### Core Components

- **Invoice Generator** (`invoice_generator.py`): Creates monthly invoices for all active subscriptions. Runs as a scheduled job via CloudWatch Events on the 1st of each month.
- **Payment Processor** (`payment_processor.py`): Handles charge creation via the Stripe API. Manages the lifecycle of a payment from initiation through confirmation.
- **Retry Handler** (`retry_handler.py`): Manages failed payment retries. Currently uses a configurable retry schedule.
- **Webhook Receiver** (`stripe_webhook.py`): Receives and processes Stripe webhook events for payment confirmations, failures, and disputes.
- **Data Models** (`models.py`): SQLAlchemy models for invoices, payments, subscriptions, and audit records.

## Database Schema

The billing database contains the following primary tables:

- `invoices` — One record per invoice, linked to a subscription
- `payments` — One record per payment attempt, linked to an invoice
- `subscriptions` — Active and cancelled subscription records
- `audit_log` — Immutable log of all billing events for compliance

## Stripe Integration

We use Stripe API version `2023-10-16`. All Stripe API calls are made via the `stripe` Python SDK. Webhook events are verified using the signing secret stored in AWS Parameter Store.

### Supported Webhook Events

- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.dispute.created`
- `customer.subscription.deleted`

## Known Limitations

- The retry handler uses a fixed retry schedule that has not been optimized for varying failure modes
- Webhook processing is synchronous and can become a bottleneck during high-volume periods
- There is no dead letter queue for failed webhook events
- The system lacks comprehensive monitoring dashboards

## Ownership

Dave Rossi is the primary maintainer of this module. For questions about billing logic, payment flows, or Stripe integration, contact Dave.

## Related Documents

- [Production Deployment Guide](./deployment-guide.md)
- Stripe API Documentation (external)
