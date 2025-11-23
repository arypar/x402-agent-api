# API Server

FastAPI server that provides endpoints for Uber ride booking and Shopify operations.

## Running the Server

```bash
# From the project root
python api/server.py
```

Or using uvicorn directly:

```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## Endpoints

### 1. Uber Ride Booking

**POST** `/uber/book-ride`

Request:
```json
{
  "from_address": "123 Main St, San Francisco, CA",
  "to_address": "456 Market St, San Francisco, CA"
}
```

Response:
```json
{
  "success": true,
  "message": "Ride booked successfully",
  "uber_url": "https://m.uber.com/looking?..."
}
```

### 2. Shopify Product Search

**POST** `/shopify/search`

Request:
```json
{
  "query": "black tshirt",
  "num_results": 5
}
```

Response:
```json
{
  "success": true,
  "results": [
    "https://store1.com/products/black-tshirt",
    "https://store2.com/products/tshirt-black",
    ...
  ],
  "count": 5
}
```

### 3. Shopify Order Placement

**POST** `/shopify/order`

Request:
```json
{
  "product_url": "https://thursdayboots.com/products/mens-premier-low-top-sneaker-black-matte",
  "size": "7"
}
```

Response:
```json
{
  "success": true,
  "message": "Order placed successfully",
  "order_details": {
    "product_url": "...",
    "size": "7",
    ...
  }
}
```

### 4. Health Check

**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "endpoints": {
    "uber": "/uber/book-ride",
    "shopify_search": "/shopify/search",
    "shopify_order": "/shopify/order"
  }
}
```

## Interactive API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage with curl

### Uber Ride
```bash
curl -X POST "http://localhost:8000/uber/book-ride" \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "123 Main St, San Francisco, CA",
    "to_address": "456 Market St, San Francisco, CA"
  }'
```

### Shopify Search
```bash
curl -X POST "http://localhost:8000/shopify/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black tshirt",
    "num_results": 5
  }'
```

### Shopify Order
```bash
curl -X POST "http://localhost:8000/shopify/order" \
  -H "Content-Type: application/json" \
  -d '{
    "product_url": "https://thursdayboots.com/products/mens-premier-low-top-sneaker-black-matte",
    "size": "7"
  }'
```

## Python Example

```python
import requests

# Uber ride
response = requests.post(
    "http://localhost:8000/uber/book-ride",
    json={
        "from_address": "123 Main St, San Francisco, CA",
        "to_address": "456 Market St, San Francisco, CA"
    }
)
print(response.json())

# Shopify search
response = requests.post(
    "http://localhost:8000/shopify/search",
    json={
        "query": "black tshirt",
        "num_results": 5
    }
)
print(response.json())

# Shopify order
response = requests.post(
    "http://localhost:8000/shopify/order",
    json={
        "product_url": "https://thursdayboots.com/products/mens-premier-low-top-sneaker-black-matte",
        "size": "7"
    }
)
print(response.json())
```

