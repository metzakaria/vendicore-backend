# Celery Task Setup for Pending Transaction Requery

This guide explains how to set up and run Celery tasks to automatically requery pending transactions from providers.

## Overview

When a transaction receives a `PENDING` response (code `80`) from a provider, the system automatically:
1. Sets the transaction status to "Processing"
2. Stores the provider account reference
3. Schedules a Celery task to requery the provider after 30 seconds
4. The task will retry up to 3 times (with 60-second delays) if the transaction is still pending

## Prerequisites

1. **Redis/RabbitMQ Broker**: Celery requires a message broker. Redis is recommended.

2. **Environment Variables**: Ensure these are set in your `.env` file:
   ```bash
   CELERY_BROKER_URL=redis://localhost:6379/0
   REDIS_URL=redis://localhost:6379/1
   ```

## Installation

If not already installed, add Celery to your requirements:

```bash
pip install celery redis
```

## Running Celery Worker

### Development

1. **Start Redis** (if using Redis):
   ```bash
   redis-server
   ```

2. **Start Celery Worker**:
   ```bash
   cd api
   celery -A config worker --loglevel=info
   ```

   Or with auto-reload for development:
   ```bash
   celery -A config worker --loglevel=info --reload
   ```

### Production

For production, use a process manager like `supervisor` or `systemd`. Example with supervisor:

```ini
[program:celery]
command=/path/to/venv/bin/celery -A config worker --loglevel=info
directory=/path/to/api
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log
```

## Running Celery Beat (Optional - for Periodic Tasks)

If you need periodic tasks (like checking for stuck transactions), run Celery Beat:

```bash
celery -A config beat --loglevel=info
```

## How It Works

### 1. Transaction Flow

When a vend request is made:
- If provider returns `PENDING` (code `80`):
  - Transaction status → "Processing"
  - Provider account is stored
  - Celery task `trigger_provider_requery_task` is scheduled after 30 seconds

### 2. Requery Task

The `trigger_provider_requery_task`:
- Waits 30 seconds (configurable via `countdown`)
- Calls `ProviderServiceManager.requery()` with the transaction's provider account
- Updates transaction based on response:
  - **SUCCESS (00)**: Updates status to "Success"
  - **PENDING (80)**: Retries up to 3 times with 60-second delays
  - **FAILED/OTHER**: Updates status to "Failed" and refunds merchant

### 3. Retry Logic

- **Max Retries**: 3 attempts
- **Retry Delay**: 60 seconds between retries
- **After Max Retries**: Transaction remains in "Processing" status with updated description

## Testing

### Manual Task Trigger

You can manually trigger a requery task from Django shell:

```python
from apps.product.task import trigger_provider_requery_task
from apps.product.models import Transaction

# Get a pending transaction
txn = Transaction.objects.filter(status="Processing").first()

# Trigger requery immediately
trigger_provider_requery_task.delay(txn.id)

# Or trigger after delay
trigger_provider_requery_task.apply_async(args=[txn.id], countdown=30)
```

### Check Task Status

Monitor Celery logs to see task execution:

```bash
tail -f /var/log/celery/worker.log
```

## Monitoring

### Check Pending Transactions

```python
from apps.product.models import Transaction
from django.utils import timezone
from datetime import timedelta

# Find transactions stuck in Processing for more than 5 minutes
stuck = Transaction.objects.filter(
    status="Processing",
    created_at__lte=timezone.now() - timedelta(minutes=5)
)
print(f"Found {stuck.count()} stuck transactions")
```

### View Celery Tasks

Use Flower (optional) for web-based monitoring:

```bash
pip install flower
celery -A config flower
```

Then visit: `http://localhost:5555`

## Troubleshooting

### Task Not Running

1. **Check Celery Worker is Running**:
   ```bash
   ps aux | grep celery
   ```

2. **Check Broker Connection**:
   ```bash
   redis-cli ping  # Should return PONG
   ```

3. **Check Logs**:
   ```bash
   tail -f /var/log/celery/worker.log
   ```

### Tasks Stuck in Queue

1. **Purge Queue** (use with caution):
   ```bash
   celery -A config purge
   ```

2. **Restart Worker**:
   ```bash
   pkill -f "celery.*worker"
   celery -A config worker --loglevel=info
   ```

## Configuration

Task settings can be adjusted in `api/apps/product/task.py`:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_provider_requery_task(self, transaction_id):
    # max_retries: Maximum number of retry attempts
    # default_retry_delay: Default delay in seconds between retries
```

In `views.py`, the initial delay can be changed:

```python
trigger_provider_requery_task.apply_async(args=[txn.id], countdown=30)  # 30 seconds
```

## Best Practices

1. **Monitor Pending Transactions**: Set up alerts for transactions stuck in Processing for extended periods
2. **Logging**: Ensure proper logging is configured for debugging
3. **Error Handling**: The task includes comprehensive error handling and logging
4. **Database Locks**: Uses `select_for_update()` to prevent race conditions
5. **Idempotency**: Task checks transaction status before processing to avoid duplicate updates

