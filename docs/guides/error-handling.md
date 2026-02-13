# Error Handling

All endpoints return dicts. Errors never raise exceptions from API calls.

## Error Response Format

```python
result = api.clan_tag("#INVALID")
if result.get("result") == "error":
    print(result["message"])         # Human-readable message
    print(result["error_type"])      # Error category
    print(result.get("http_status")) # HTTP status code (when applicable)
```

## Error Types

| Error Type | Cause |
|---|---|
| `timeout` | Request timed out after configured seconds |
| `connection` | Network error (DNS failure, connection refused, etc.) |
| `http` | Non-2xx HTTP response from the API |
| `json` | Invalid JSON in the API response |
| `retry_exhausted` | All retry attempts failed |
| `deprecated` | Endpoint has been removed by SuperCell (404/410) |
| `unknown` | Unexpected error |

## Retry Behavior

cocapi retries failed requests automatically:

- **Max retries**: Configured via `ApiConfig(max_retries=3)` (default: 3)
- **Backoff**: Exponential — `retry_delay * 2^attempt` seconds between retries
- **Retryable errors**: Server errors (5xx) and rate limiting (429)
- **Non-retryable**: Client errors (400, 403, 404) fail immediately

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    max_retries=5,
    retry_delay=2.0,  # 2s, 4s, 8s, 16s between retries
)
api = CocApi("token", config=config)
```

## Auto Key Refresh

When using credential-based auth, if the API returns `403 accessDenied.invalidIp` (your IP changed), cocapi automatically:

1. Re-logs into the developer portal
2. Detects your new IP
3. Revokes stale keys and creates new ones
4. Retries the original request

This happens once per request. If the retry also fails, the error is returned normally.

## Common HTTP Errors

| Status | Message | Typical Cause |
|---|---|---|
| 400 | Bad request | Invalid parameters |
| 403 | Forbidden | Invalid token or IP mismatch |
| 404 | Not found | Invalid clan/player tag |
| 429 | Rate limited | Too many requests |
| 503 | Service unavailable | API maintenance |

## Best Practices

```python
result = api.clan_tag(tag)

if result.get("result") == "error":
    error_type = result["error_type"]

    if error_type == "http" and result.get("http_status") == 404:
        print("Clan not found")
    elif error_type == "timeout":
        print("Request timed out, try again later")
    elif error_type == "deprecated":
        print("This endpoint is no longer available")
    else:
        print(f"Error: {result['message']}")
else:
    # Success
    print(result["name"])
```
