# Progress Tracking

## 🎯 Overview

Tasks now update their `result_data` column in real-time with progress updates as they execute. This allows you to track what stage a task is currently at, not just wait for it to complete.

## 📊 How It Works

As a task progresses through different stages, the worker adds timestamped progress updates to the `result_data.progress` array. You can see these updates by checking the task status.

## 🔍 Checking Progress

### API Endpoint

```bash
curl "http://localhost:8000/tasks/{task_id}"
```

### Response Format

```json
{
  "task_id": "abc-123",
  "type": "shopify_order",
  "current_status": "processing",
  "result_data": {
    "progress": [
      {
        "message": "Task started by worker-1",
        "timestamp": "2025-11-23T10:00:00.123456"
      },
      {
        "message": "Opening product page",
        "timestamp": "2025-11-23T10:00:01.234567"
      },
      {
        "message": "Selecting size: Medium",
        "timestamp": "2025-11-23T10:00:02.345678"
      },
      {
        "message": "Adding product to cart",
        "timestamp": "2025-11-23T10:00:05.456789"
      },
      {
        "message": "Navigating to checkout",
        "timestamp": "2025-11-23T10:00:10.567890"
      },
      {
        "message": "Filling shipping information",
        "timestamp": "2025-11-23T10:00:15.678901"
      },
      {
        "message": "Processing payment",
        "timestamp": "2025-11-23T10:00:20.789012"
      },
      {
        "message": "Order placed successfully",
        "timestamp": "2025-11-23T10:00:25.890123"
      }
    ]
  },
  "created_at": "2025-11-23T10:00:00Z",
  "started_at": "2025-11-23T10:00:00Z",
  "completed_at": "2025-11-23T10:00:25Z"
}
```

## 📝 Progress Updates by Task Type

### Uber Ride Tasks

Progress updates for Uber rides:

1. ✅ **"Task started by worker-{id}"**
2. 🚗 **"Generating Uber ride URL"**
3. 📱 **"Opening Uber app"**
4. 🔐 **"Authenticating with Uber"**
5. ✓ **"Confirming ride details"**
6. 🚕 **"Booking ride"**
7. ✅ **"Ride booked successfully"** (on success)
   OR
   ❌ **"Payment declined or booking failed"** (on failure)

### Shopify Order Tasks

Progress updates for Shopify orders:

1. ✅ **"Task started by worker-{id}"**
2. 🌐 **"Opening product page"**
3. 📏 **"Selecting size: {size}"**
4. 🛒 **"Adding product to cart"**
5. 💳 **"Navigating to checkout"**
6. 📦 **"Filling shipping information"**
7. 💰 **"Processing payment"**
8. ✅ **"Order placed successfully"** (on success)
   OR
   ❌ **"Checkout failed: {error}"** (on failure)

## 💻 Usage Examples

### Python: Real-time Progress Monitoring

```python
import requests
import time

# Create a task
response = requests.post(
    "http://localhost:8000/shopify/order",
    json={
        "product_url": "https://kith.com/products/hp-p020-051-1",
        "size": "Medium"
    }
)
task_id = response.json()["task_id"]

# Poll for progress updates
while True:
    status = requests.get(f"http://localhost:8000/tasks/{task_id}").json()
    
    # Show current status
    print(f"Status: {status['current_status']}")
    
    # Show all progress updates
    progress = status.get("result_data", {}).get("progress", [])
    for update in progress:
        print(f"  [{update['timestamp']}] {update['message']}")
    
    if status["current_status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)  # Check every 2 seconds
```

### JavaScript: Progress Display

```javascript
async function monitorTask(taskId) {
  while (true) {
    const response = await fetch(`http://localhost:8000/tasks/${taskId}`);
    const task = await response.json();
    
    // Display progress
    const progress = task.result_data?.progress || [];
    console.clear();
    console.log(`Task: ${taskId}`);
    console.log(`Status: ${task.current_status}\n`);
    
    progress.forEach(update => {
      console.log(`✓ ${update.message}`);
    });
    
    if (['completed', 'failed'].includes(task.current_status)) {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```

### cURL: Check Latest Progress

```bash
# Get task status with progress
curl "http://localhost:8000/tasks/abc-123" | jq '.result_data.progress'
```

Output:
```json
[
  {
    "message": "Task started by worker-1",
    "timestamp": "2025-11-23T10:00:00.123456"
  },
  {
    "message": "Opening product page",
    "timestamp": "2025-11-23T10:00:01.234567"
  },
  {
    "message": "Adding product to cart",
    "timestamp": "2025-11-23T10:00:05.456789"
  }
]
```

## 🔧 View in Supabase

In your Supabase dashboard:

1. Go to **Table Editor** → `tasks`
2. Click on a task row
3. Look at the `result_data` column (JSONB)
4. Expand the `progress` array to see all updates

Example `result_data`:
```json
{
  "progress": [
    {
      "message": "Task started by worker-1",
      "timestamp": "2025-11-23T10:00:00.123456"
    },
    {
      "message": "Opening product page",
      "timestamp": "2025-11-23T10:00:01.234567"
    }
  ]
}
```

## 📊 Query Progress in SQL

### Get Latest Progress for a Task

```sql
SELECT 
    id,
    type,
    current_status,
    result_data->'progress'->-1->>'message' as latest_progress,
    result_data->'progress'->-1->>'timestamp' as latest_timestamp
FROM tasks
WHERE id = 'your-task-id';
```

### Get All Progress Updates

```sql
SELECT 
    id,
    type,
    jsonb_array_elements(result_data->'progress') as progress_update
FROM tasks
WHERE id = 'your-task-id';
```

### Count Progress Steps by Task

```sql
SELECT 
    id,
    type,
    current_status,
    jsonb_array_length(result_data->'progress') as progress_steps
FROM tasks
WHERE result_data->'progress' IS NOT NULL
ORDER BY created_at DESC;
```

## 🎯 Benefits

✅ **Real-time visibility** - See exactly what stage a task is at  
✅ **Better debugging** - Know where tasks fail  
✅ **User experience** - Show progress to end users  
✅ **Historical tracking** - See how long each step took  
✅ **Timestamped** - Precise timing for each update  

## 🔍 Troubleshooting

### Progress Updates Not Showing

1. **Check task status**:
   ```bash
   curl "http://localhost:8000/tasks/{task_id}"
   ```

2. **Verify worker is running**:
   ```bash
   ps aux | grep worker.py
   ```

3. **Check result_data in Supabase**:
   - Go to Supabase → Table Editor → tasks
   - Find your task
   - Check the `result_data` column

### Progress Stopped Updating

This usually means:
- Task encountered an error
- Worker crashed
- Task is stuck (will be reset after 10 minutes)

Check the `error_message` field in the task.

## 📝 Adding Custom Progress Updates

If you want to add more detailed progress updates, edit the worker functions in `api/worker.py`:

```python
# In process_shopify_order or process_uber_ride
TaskDatabase.add_progress_update(task_id, "Your custom message here")
```

## 🎨 UI Integration Example

For a web interface, you could display progress like this:

```
Task: abc-123 (Processing)

Progress:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 60%

✓ Task started by worker-1          10:00:00
✓ Opening product page              10:00:01
✓ Selecting size: Medium            10:00:02
✓ Adding product to cart            10:00:05
⏳ Navigating to checkout           10:00:10
□ Filling shipping information
□ Processing payment
□ Order placed successfully
```

---

**Progress tracking is now live!** 🎉

Check your task status to see real-time updates as tasks execute.

