# Middleware

Add custom processing to requests and responses.

## Built-in Middleware

```python
from cocapi import CocApi
from cocapi.middleware import (
    add_user_agent_middleware,
    add_request_id_middleware,
    add_debug_logging_middleware,
    add_response_timestamp_middleware,
    add_response_size_middleware,
)

api = CocApi("token")

# Add a custom User-Agent header
api.add_request_middleware(add_user_agent_middleware("MyApp/1.0"))

# Add a unique X-Request-ID to each request
api.add_request_middleware(add_request_id_middleware())

# Log request URLs and response sizes
api.add_request_middleware(add_debug_logging_middleware())

# Add a timestamp to each response
api.add_response_middleware(add_response_timestamp_middleware())

# Add response byte size to each response
api.add_response_middleware(add_response_size_middleware())
```

## Custom Request Middleware

A request middleware receives `(url, headers, params)` and returns a modified `(url, headers, params)` tuple:

```python
def add_custom_header(url, headers, params):
    headers["X-My-Header"] = "value"
    return url, headers, params

api.add_request_middleware(add_custom_header)
```

### Signature

```python
def request_middleware(
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
) -> tuple[str, dict[str, str], dict[str, Any]]:
    ...
```

## Custom Response Middleware

A response middleware receives the JSON response dict and returns a modified dict:

```python
def log_response(response):
    print(f"Got response with {len(response)} keys")
    return response

api.add_response_middleware(log_response)
```

### Signature

```python
def response_middleware(
    response: dict[str, Any],
) -> dict[str, Any]:
    ...
```

## Execution Order

- Request middleware runs in the order added, before the HTTP request is sent
- Response middleware runs in the order added, after the response is received
- Middleware applies to all API calls (GET and POST)
