# Authentication

cocapi supports two authentication methods.

## 1. API Token

Get a token from [developer.clashofclans.com](https://developer.clashofclans.com/) and pass it directly:

```python
from cocapi import CocApi

api = CocApi("your_token")
```

You manage key creation and IP binding yourself at the developer portal.

## 2. Developer Portal Credentials

Provide your email and password. cocapi handles everything automatically:

```python
from cocapi import CocApi

api = CocApi.from_credentials("email@example.com", "password")
```

What happens automatically:

- Logs into the developer portal and detects your public IP
- Creates API keys bound to that IP (or reuses existing ones)
- If your IP changes mid-session and the API returns 403, revokes the old key and creates a new one
- Respects the 10-key-per-account SuperCell limit

### Configuration Options

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    key_count=2,               # Number of keys to maintain (default: 1)
    key_name="my-bot",         # Key name on the portal (default: "cocapi_auto")
    auto_refresh_keys=True,    # Auto-rotate on IP change (default: True)
)
api = CocApi.from_credentials("email", "password", config=config)
```

### Persisting Keys Locally

Enable `persist_keys` to cache the token on disk. On the next run, if your IP hasn't changed, the cached token is reused without contacting the developer portal:

```python
config = ApiConfig(persist_keys=True)
api = CocApi.from_credentials("email", "password", config=config)
# First run:  logs in, creates key, saves to ~/.cocapi/keys.json
# Next runs:  detects IP, matches cache, skips login entirely
```

Disabled by default. The storage path is customizable via `key_storage_path`.

### Standalone Key Manager

Use `SyncKeyManager` or `AsyncKeyManager` directly if you need tokens outside of `CocApi`:

```python
from cocapi import SyncKeyManager

with SyncKeyManager("email", "password", key_count=3) as km:
    tokens = km.manage_keys()
    print(f"Got {len(tokens)} token(s)")
```

Async version:

```python
from cocapi import AsyncKeyManager

async with AsyncKeyManager("email", "password") as km:
    tokens = await km.manage_keys()
```

!!! warning "Security"
    Never commit `.cocapi/` (key cache) or `.env` files to version control.
