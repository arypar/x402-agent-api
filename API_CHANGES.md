# API Endpoint Consolidation

## 🔄 What Changed

The Uber and Shopify task endpoints have been **unified** into a single `/tasks/create` endpoint.

### Before (Old API)

```bash
# Two separate endpoints
POST /uber/book-ride
POST /shopify/order
```

### After (New API)

```bash
# One unified endpoint
POST /tasks/create
```

---

## 📡 New Unified Endpoint

### POST /tasks/create

**Base URL**: `https://undecorously-uncongestive-cindy.ngrok-free.dev`

**Request Format**:
```json
{
  "task_type": "uber_ride" | "shopify_order",
  "input_data": {
    // Task-specific fields
  }
}
```

---

## 🚗 Uber Ride Example

**Old Way** (deprecated):
```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/uber/book-ride" \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "123 Main St, SF",
    "to_address": "456 Market St, SF"
  }'
```

**New Way** ✅:
```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/create" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "uber_ride",
    "input_data": {
      "from_address": "123 Main St, SF",
      "to_address": "456 Market St, SF"
    }
  }'
```

---

## 🛍️ Shopify Order Example

**Old Way** (deprecated):
```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/shopify/order" \
  -H "Content-Type: application/json" \
  -d '{
    "product_url": "https://kith.com/products/hp-p020-051-1",
    "size": "Medium"
  }'
```

**New Way** ✅:
```bash
curl -X POST "https://undecorously-uncongestive-cindy.ngrok-free.dev/tasks/create" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "shopify_order",
    "input_data": {
      "product_url": "https://kith.com/products/hp-p020-051-1",
      "size": "Medium"
    }
  }'
```

---

## 📋 Task Types & Required Fields

### `uber_ride`

**Required fields in `input_data`**:
- `from_address` (string) - Starting location
- `to_address` (string) - Destination location

**Example**:
```json
{
  "task_type": "uber_ride",
  "input_data": {
    "from_address": "1 Apple Park Way, Cupertino, CA",
    "to_address": "1600 Amphitheatre Parkway, Mountain View, CA"
  }
}
```

### `shopify_order`

**Required fields in `input_data`**:
- `product_url` (string) - Full URL to Shopify product
- `size` (string) - Size to order (e.g., "M", "Medium", "7")

**Example**:
```json
{
  "task_type": "shopify_order",
  "input_data": {
    "product_url": "https://kith.com/products/hp-p020-051-1",
    "size": "Medium"
  }
}
```

---

## ✅ Response Format

Same response format for all task types:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "type": "uber_ride",
  "message": "Uber ride booking task created. Use the task_id to check status."
}
```

---

## ⚠️ Error Handling

### Invalid task_type

```json
{
  "detail": "Invalid task_type. Must be one of: uber_ride, shopify_order"
}
```

### Missing required fields

```json
{
  "detail": "Missing required fields for uber_ride: from_address"
}
```

---

## 🔄 Migration Guide

### Python

**Old**:
```python
# Uber ride
response = requests.post(
    f"{BASE_URL}/uber/book-ride",
    json={"from_address": "A", "to_address": "B"}
)

# Shopify order
response = requests.post(
    f"{BASE_URL}/shopify/order",
    json={"product_url": "url", "size": "M"}
)
```

**New**:
```python
# Uber ride
response = requests.post(
    f"{BASE_URL}/tasks/create",
    json={
        "task_type": "uber_ride",
        "input_data": {"from_address": "A", "to_address": "B"}
    }
)

# Shopify order
response = requests.post(
    f"{BASE_URL}/tasks/create",
    json={
        "task_type": "shopify_order",
        "input_data": {"product_url": "url", "size": "M"}
    }
)
```

### JavaScript

**Old**:
```javascript
// Uber ride
await fetch(`${BASE_URL}/uber/book-ride`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    from_address: "A",
    to_address: "B"
  })
});
```

**New**:
```javascript
// Uber ride
await fetch(`${BASE_URL}/tasks/create`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    task_type: "uber_ride",
    input_data: {
      from_address: "A",
      to_address: "B"
    }
  })
});
```

---

## 🎯 Benefits

✅ **Simpler API** - One endpoint instead of multiple  
✅ **Consistent interface** - Same structure for all task types  
✅ **Easier to extend** - Add new task types without new endpoints  
✅ **Better validation** - Centralized input validation  
✅ **Cleaner code** - Single endpoint handler  

---

## 📚 Updated Documentation

See `API_DOCUMENTATION.md` for complete updated documentation with:
- Full request/response examples
- All task types documented
- Error handling guide
- Implementation examples in Python, JavaScript, and cURL

---

## 🔗 Quick Reference

**New Endpoint**: `POST /tasks/create`

**Supported Task Types**:
- `uber_ride`
- `shopify_order`

**Structure**:
```json
{
  "task_type": "string",
  "input_data": { /* task-specific fields */ }
}
```

---

**Base URL**: https://undecorously-uncongestive-cindy.ngrok-free.dev  
**Documentation**: API_DOCUMENTATION.md  
**Version**: 2.0.0

