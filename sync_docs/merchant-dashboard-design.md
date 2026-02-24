---
title: "Merchant Dashboard — Technical Design Document"
space: "Payments Platform"
author: "Priya Sharma"
created: "2025-10-01"
last_updated: "2025-12-18"
labels: ["frontend", "merchant-dashboard", "design-doc", "react"]
version: 2
---

# Merchant Dashboard — Technical Design Document

## Overview

The Merchant Dashboard is the primary interface through which merchants view their transaction history, manage subscriptions, and access billing analytics. This document covers the planned redesign from the legacy jQuery-based dashboard to a modern React application.

## Goals

- Replace the legacy jQuery UI with a React + TypeScript single-page application
- Improve page load performance by 60%
- Add real-time transaction status visibility
- Provide CSV and PDF export of billing statements

## Technical Architecture

### Frontend Stack

- React 18 with TypeScript
- Tailwind CSS for styling
- React Query for server state management
- Recharts for analytics visualizations

### Data Fetching Strategy

The dashboard will use **REST API polling** to fetch transaction updates. The polling interval will be set to 30 seconds for the transaction list view and 60 seconds for the analytics dashboard.

We evaluated WebSocket-based real-time updates but determined that REST polling is sufficient for our current merchant volume (~2,000 active merchants) and significantly simpler to implement and maintain. WebSocket support can be revisited if merchant volume exceeds 10,000.

### API Endpoints

The dashboard consumes the following REST endpoints:

- `GET /api/v1/merchants/{id}/transactions` — Paginated transaction list
- `GET /api/v1/merchants/{id}/subscriptions` — Active subscriptions
- `GET /api/v1/merchants/{id}/analytics` — Aggregated billing analytics
- `POST /api/v1/merchants/{id}/exports` — Trigger CSV/PDF export

### Component Structure

```
src/
├── components/
│   ├── TransactionList.tsx
│   ├── TransactionDetail.tsx
│   ├── SubscriptionManager.tsx
│   ├── AnalyticsDashboard.tsx
│   ├── ExportDialog.tsx
│   └── common/
│       ├── DataTable.tsx
│       ├── StatusBadge.tsx
│       └── LoadingSpinner.tsx
├── hooks/
│   ├── useTransactions.ts
│   ├── useSubscriptions.ts
│   └── useAnalytics.ts
├── services/
│   └── api.ts
└── types/
    └── merchant.ts
```

## Rollout Plan

- Phase 1: Transaction list view (current sprint)
- Phase 2: Analytics dashboard
- Phase 3: Subscription management
- Phase 4: Export functionality

## Ownership

Priya Sharma is the technical lead for this redesign. For frontend architecture questions, contact Priya.
