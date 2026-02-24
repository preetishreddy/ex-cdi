---
title: "Production Deployment Guide"
space: "Payments Platform"
author: "Sarah Chen"
created: "2025-03-12"
last_updated: "2025-11-15"
labels: ["deployment", "ci-cd", "production", "jenkins"]
version: 3
---

# Production Deployment Guide

## Overview

All production deployments for the Payments Platform are managed through our Jenkins CI/CD pipeline. This document covers the standard deployment process, rollback procedures, and environment configuration.

## Prerequisites

Before deploying to production, ensure:

- Your branch has been reviewed and approved via GitHub PR
- All unit tests pass in the Jenkins staging pipeline
- You have received sign-off from the on-call engineer
- The deployment window is within business hours (9 AM – 5 PM EST) unless an emergency hotfix is approved by the Engineering Manager

## Deployment Steps

### Step 1: Trigger the Jenkins Pipeline

Navigate to the Jenkins dashboard at `https://jenkins.internal.meridiantech.com/payments-platform`. Select the `deploy-production` job. Enter your branch name and click "Build with Parameters."

### Step 2: Monitor the Build

The Jenkins pipeline runs the following stages in order:

1. Checkout and dependency installation
2. Unit tests
3. Integration tests against staging database
4. Docker image build and push to ECR
5. Rolling deployment to ECS production cluster
6. Post-deployment health checks

The full pipeline typically takes 12–18 minutes. Monitor the console output for any failures.

### Step 3: Verify Deployment

After Jenkins reports a successful deployment:

- Check the `/health` endpoint on production
- Verify key transactions in the payment flow using the staging merchant test account
- Monitor Datadog dashboards for error rate spikes in the first 15 minutes

### Rollback Procedure

If issues are detected post-deployment:

1. Navigate to the Jenkins `deploy-production` job
2. Click "Rollback" and select the previous stable build number
3. Jenkins will redeploy the previous Docker image from ECR
4. Notify the #payments-platform Slack channel that a rollback has been performed

## Environment Variables

Production environment variables are managed in AWS Parameter Store under the `/payments/production/` namespace. Never hardcode secrets in the repository. Contact Marcus Thompson for access to Parameter Store.

## Notes

- Deployments to staging follow the same process but use the `deploy-staging` Jenkins job
- Hotfixes outside business hours require approval from James O'Brien or Sarah Chen
- The deployment pipeline was last audited in October 2025
