<p>
    <a href="https://github.com/tonybenoy/cocapi/actions">
        <img src="https://github.com/tonybenoy/cocapi/workflows/CI/badge.svg" alt="CI Status" height="20">
    </a>
    <a href="https://pypi.org/project/cocapi/"><img src="https://img.shields.io/pypi/v/cocapi" alt="Pypi version" height="21"></a>
</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python version" height="17"></a>
    <a href="https://github.com/tonybenoy/cocapi/blob/master/LICENSE"><img src="https://img.shields.io/github/license/tonybenoy/cocapi" alt="License" height="17"></a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" height="17">
    </a>
</p>

# ClashOfClansAPI v3.0.0

A high-performance Python wrapper for SuperCell's Clash of Clans API with enterprise-grade features including async support, response caching, retry logic, middleware system, and comprehensive metrics.

**🎯 Complete API Coverage**: All 22 official endpoints implemented  
**⚡ High Performance**: Async support with intelligent caching and rate limiting  
**🔄 100% Backward Compatible**: Drop-in replacement for existing code  
**🛡️ Production Ready**: Retry logic, middleware pipeline, metrics tracking, and comprehensive error handling  
**🚀 Future-Proof**: Custom endpoint support and dynamic Pydantic models

Get Token from [https://developer.clashofclans.com/](https://developer.clashofclans.com/)

## ✨ Key Features

- **🔄 Synchronous & Asynchronous Support**: Same API works for both sync and async
- **🚀 Custom Endpoint Support**: Future-proof with any new SuperCell endpoints
- **💾 Intelligent Caching**: Response caching with configurable TTL and statistics
- **🔁 Smart Retry Logic**: Exponential backoff with configurable retry policies
- **⚡ Rate Limiting**: Built-in protection against API rate limits (async mode)
- **🛡️ Comprehensive Error Handling**: Detailed error messages and types
- **📊 Metrics & Analytics**: Request performance tracking and insights
- **🔌 Middleware System**: Pluggable request/response processing pipeline
- **🎯 Type Safety**: Complete type hints and optional Pydantic models
- **🔮 Dynamic Models**: Auto-generated Pydantic models for unknown endpoints
- **🌐 Base URL Configuration**: Support for proxies and testing environments
- **🔄 100% Backward Compatible**: Drop-in replacement for existing code
- **⚙️ Configurable**: Extensive configuration options via ApiConfig

# Install

```bash
# Standard installation (dict responses)
pip install cocapi

# With optional Pydantic models support
pip install 'cocapi[pydantic]'
```


# Usage Examples

## Basic Synchronous Usage (Backward Compatible)

```python
from cocapi import CocApi

token = 'YOUR_API_TOKEN'
timeout = 60  # requests timeout

# Basic initialization (same as before)
api = CocApi(token, timeout)

# With status codes (same as before)
api = CocApi(token, timeout, status_code=True)
```

## Advanced Configuration

```python
from cocapi import CocApi, ApiConfig

# Enterprise-grade configuration
config = ApiConfig(
    # Performance settings
    timeout=30,
    max_retries=5,
    retry_delay=1.5,  # Base delay for exponential backoff
    
    # Caching configuration  
    enable_caching=True,
    cache_ttl=600,  # Cache responses for 10 minutes
    
    # Async rate limiting (async mode only)
    enable_rate_limiting=True,
    requests_per_second=10.0,
    burst_limit=20,
    
    # Advanced features
    enable_metrics=True,
    metrics_window_size=1000,  # Track last 1000 requests
    use_pydantic_models=False  # Enable for type-safe models
)

api = CocApi('YOUR_API_TOKEN', config=config)

# Management methods
cache_stats = api.get_cache_stats()
metrics = api.get_metrics()
api.clear_cache()
api.clear_metrics()
```

## Asynchronous Usage

```python
import asyncio
from cocapi import CocApi, ApiConfig

async def main():
    # Method 1: Automatic async mode with context manager (recommended)
    async with CocApi('YOUR_API_TOKEN') as api:
        clan = await api.clan_tag('#CLAN_TAG')
        player = await api.players('#PLAYER_TAG')
    
    # Method 2: Explicit async mode
    api = CocApi('YOUR_API_TOKEN', async_mode=True)
    async with api:
        clan = await api.clan_tag('#CLAN_TAG')
    
    # Method 3: With custom configuration
    config = ApiConfig(timeout=30, enable_caching=True)
    async with CocApi('YOUR_API_TOKEN', config=config) as api:
        clan = await api.clan_tag('#CLAN_TAG')

# Run async code
asyncio.run(main())
```

## 🚀 New in v3.0.0: Enterprise Features

### 📊 Metrics & Analytics

Track API performance and usage patterns:

```python
from cocapi import CocApi, ApiConfig

# Enable metrics tracking
config = ApiConfig(enable_metrics=True, metrics_window_size=1000)
api = CocApi('YOUR_TOKEN', config=config)

# Make some API calls
clan = api.clan_tag('#CLAN_TAG')
player = api.players('#PLAYER_TAG')

# Get comprehensive metrics
metrics = api.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Average response time: {metrics['avg_response_time']:.2f}ms")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Error rate: {metrics['error_rate']:.1%}")

# Performance insights
insights = metrics['performance_insights']
for insight in insights:
    print(f"💡 {insight}")

# Endpoint-specific metrics
endpoint_stats = metrics['endpoint_metrics']
for endpoint, stats in endpoint_stats.items():
    print(f"{endpoint}: {stats['count']} calls, {stats['avg_time']:.2f}ms avg")
```

### 🔌 Middleware System

Add custom request/response processing:

```python
from cocapi import CocApi, ApiConfig
from cocapi.middleware import (
    add_user_agent_middleware,
    add_request_id_middleware, 
    add_response_timestamp_middleware
)

api = CocApi('YOUR_TOKEN')

# Add request middleware
api.add_request_middleware(add_user_agent_middleware("MyApp/1.0"))
api.add_request_middleware(add_request_id_middleware())

# Add response middleware
api.add_response_middleware(add_response_timestamp_middleware())

# Custom middleware example
def add_custom_header(url, headers, params):
    """Add custom authentication or tracking headers"""
    headers['X-Client-Version'] = '3.0.0'
    headers['X-Request-Source'] = 'production'
    return url, headers, params

def log_response_size(response):
    """Log response sizes for monitoring"""
    if isinstance(response, dict):
        size = len(str(response))
        print(f"Response size: {size} characters")
    return response

api.add_request_middleware(add_custom_header)
api.add_response_middleware(log_response_size)

# All requests now include middleware processing
clan = api.clan_tag('#CLAN_TAG')  # Includes custom headers and logging
```

### 🎯 Enhanced Caching with Statistics

Advanced caching capabilities with detailed statistics:

```python
from cocapi import CocApi, ApiConfig

config = ApiConfig(
    enable_caching=True,
    cache_ttl=900  # 15 minutes
)
api = CocApi('YOUR_TOKEN', config=config)

# Make requests (cached automatically)
clan1 = api.clan_tag('#CLAN_TAG')  # Cache miss
clan2 = api.clan_tag('#CLAN_TAG')  # Cache hit

# Detailed cache statistics
stats = api.get_cache_stats()
print(f"Cache enabled: {stats['enabled']}")
print(f"Total entries: {stats['total_entries']}")
print(f"Valid entries: {stats['valid_entries']}")
print(f"Expired entries: {stats['expired_entries']}")
print(f"Memory usage: {stats['memory_usage_mb']:.2f} MB")
print(f"Hit rate: {stats['hit_rate']:.1%}")

# Cache management
api.clear_cache()  # Returns number of cleared entries
print(f"Cleared {api.clear_cache()} entries")
```

### ⚡ Async Rate Limiting

Built-in rate limiting for async operations:

```python
from cocapi import CocApi, ApiConfig
import asyncio

async def high_throughput_example():
    config = ApiConfig(
        enable_rate_limiting=True,
        requests_per_second=10.0,  # Maximum 10 requests per second
        burst_limit=20,            # Allow bursts up to 20 requests
        enable_caching=True,
        enable_metrics=True
    )
    
    async with CocApi('YOUR_TOKEN', config=config) as api:
        # Make many concurrent requests - rate limiting automatically applied
        clan_tags = ['#CLAN1', '#CLAN2', '#CLAN3', '#CLAN4', '#CLAN5']
        
        tasks = [api.clan_tag(tag) for tag in clan_tags]
        results = await asyncio.gather(*tasks)
        
        # Check metrics to see rate limiting in action
        metrics = api.get_metrics()
        print(f"Requests completed: {metrics['total_requests']}")
        print(f"Average response time: {metrics['avg_response_time']:.2f}ms")

asyncio.run(high_throughput_example())
```

## Pydantic Models (Optional)

For enhanced type safety and structured data validation, cocapi supports optional Pydantic models:

```python
from cocapi import CocApi, ApiConfig, Clan, Player

# Enable Pydantic models
config = ApiConfig(use_pydantic_models=True)
api = CocApi('YOUR_API_TOKEN', config=config)

# Get structured clan data
clan = api.clan_tag('#2PP')  # Returns Clan model instead of dict
print(clan.name)             # Type-safe attribute access
print(clan.clan_level)       # IDE autocompletion support
print(clan.members)          # Validated data structure

# Get structured player data  
player = api.players('#PLAYER_TAG')  # Returns Player model
print(player.town_hall_level)        # Type-safe attributes
print(player.trophies)
print(player.clan.name if player.clan else "No clan")

# Works with async too
async def get_data():
    config = ApiConfig(use_pydantic_models=True)
    async with CocApi('YOUR_TOKEN', config=config) as api:
        clan = await api.clan_tag('#TAG')  # Returns Clan model
        return clan.name

# Available models: Clan, Player, ClanMember, League, Achievement, etc.
# Import them: from cocapi import Clan, Player, ClanMember
```

### Benefits of Pydantic Models

- **Type Safety**: Catch errors at development time
- **IDE Support**: Full autocompletion and type hints
- **Data Validation**: Automatic validation of API responses  
- **Clean Interface**: Object-oriented access to data
- **Documentation**: Self-documenting code with model schemas
- **Optional**: Zero impact if not used (lazy imports)

## Custom Endpoints (Future-Proofing) 🚀

When SuperCell adds new endpoints to the Clash of Clans API, you can use them immediately without waiting for library updates:

### Basic Custom Endpoint Usage

```python
from cocapi import CocApi

api = CocApi('YOUR_API_TOKEN')

# Call any new endpoint by providing the path
result = api.custom_endpoint('/new-endpoint')

# With parameters
result = api.custom_endpoint('/clans/search', {
    'name': 'my clan', 
    'limit': 10
})

# Async support
async with CocApi('YOUR_TOKEN') as api:
    result = await api.custom_endpoint('/new-endpoint')
```

### Dynamic Pydantic Models for Unknown Endpoints

Create type-safe models automatically from JSON responses:

```python
from cocapi import CocApi, ApiConfig

# Enable dynamic model creation
api = CocApi('YOUR_TOKEN')

# Get a dynamic Pydantic model from the response
result = api.custom_endpoint('/new-endpoint', use_dynamic_model=True)

# Now you get a Pydantic model with:
# - Type safety
# - IDE autocompletion
# - Attribute access: result.field_name
# - Data validation
print(result.some_field)  # Type-safe access
print(type(result))       # <class 'DynamicNewEndpointModel'>
```

### Advanced Custom Endpoint Examples

```python
from cocapi import CocApi, ApiConfig
import asyncio

async def use_new_features():
    # With full configuration
    config = ApiConfig(
        enable_caching=True,
        cache_ttl=300,
        max_retries=3
    )
    
    async with CocApi('YOUR_TOKEN', config=config) as api:
        # Future SuperCell endpoints work immediately
        new_feature = await api.custom_endpoint(
            '/hypothetical-new-feature/v2',
            {'player_tag': '#PLAYER_TAG'},
            use_dynamic_model=True
        )
        
        # All existing features work: caching, retries, error handling
        if hasattr(new_feature, 'result') and new_feature.result == 'error':
            print(f"Error: {new_feature.message}")
        else:
            # Type-safe access to new fields
            print(f"New data: {new_feature.some_new_field}")

# Real-world example: Using custom endpoint for clan search
api = CocApi('YOUR_TOKEN')

# These are equivalent:
search1 = api.clan('search', {'name': 'reddit'})  # Built-in method
search2 = api.custom_endpoint('/clans', {'name': 'reddit'})  # Custom endpoint

# But custom endpoint lets you use ANY future endpoint:
future_endpoint = api.custom_endpoint('/future-feature', use_dynamic_model=True)
```

### Benefits of Custom Endpoints

- **🔮 Future-Proof**: Use new SuperCell endpoints immediately
- **⚡ Full Feature Support**: Caching, retries, async, error handling all work
- **🛡️ Type Safety**: Dynamic Pydantic models for unknown structures  
- **🔄 Backward Compatible**: Existing code unchanged
- **📦 Zero Dependencies**: Dynamic models only if Pydantic is installed
- **🎯 Flexible**: Works with any HTTP endpoint structure

## Base URL Configuration 🌐

For testing, proxying, or adapting to API changes, you can modify the base URL:

### Changing Base URL (with Safety Warnings)

```python
from cocapi import CocApi
import warnings

api = CocApi('YOUR_TOKEN')

# For development/testing environments
api.set_base_url(
    "https://api-dev.clashofclans.com/v1", 
    force=True  # Required for safety
)
# Warning: ⚠️  WARNING: Changing base URL from official endpoint!

# For proxy usage
api.set_base_url(
    "https://my-proxy.example.com/clash-api/v1", 
    force=True
)

# Check current URL
current_url = api.get_base_url()
print(f"Using: {current_url}")

# Reset to official endpoint
api.reset_base_url()
# Warning: Base URL reset from '...' to official SuperCell endpoint
```

### Base URL via Configuration

```python
from cocapi import CocApi, ApiConfig

# Set base URL during initialization
config = ApiConfig(
    base_url="https://api-staging.clashofclans.com/v1",
    timeout=30,
    enable_caching=True
)

api = CocApi('YOUR_TOKEN', config=config)
# No warnings during initialization - warnings only for runtime changes
```

### Safety Features

- **Force Required**: Must set `force=True` for safety
- **URL Validation**: Validates URL format before applying
- **Clear Warnings**: Prominent warnings about potential risks  
- **Logging**: All URL changes are logged for audit trail
- **Easy Reset**: One-method reset to official endpoint

### Common Use Cases

```python
# Testing against staging environment
api.set_base_url("https://staging-api.example.com/v1", force=True)

# Using corporate proxy
api.set_base_url("https://proxy.corp.com/clash/v1", force=True)

# Load balancer or CDN
api.set_base_url("https://clash-api.cdn.example.com/v1", force=True)

# Local mock server for development
api.set_base_url("http://localhost:3000/api/v1", force=True)

# Always reset when done testing
api.reset_base_url()
```

## 📈 Performance & Reliability Benefits

v3.0.0 introduces significant performance and reliability improvements:

### Performance Gains
- **⚡ Intelligent Caching**: Up to 100% faster for repeated requests with TTL management
- **🚀 Async Operations**: Handle dozens of concurrent requests efficiently  
- **📊 Metrics-Driven**: Identify bottlenecks with comprehensive performance analytics
- **🔌 Middleware Pipeline**: Minimal overhead for request/response processing

### Reliability Features  
- **🔁 Smart Retry Logic**: Exponential backoff with configurable policies
- **⚡ Rate Limiting**: Built-in protection against API limits (async mode)
- **🛡️ Enhanced Error Handling**: Detailed error messages with specific error types
- **📈 Monitoring**: Track error rates, response times, and cache performance

### Real-World Impact
```python
# Before v3.0.0: Basic requests
api = CocApi('token')
clan = api.clan_tag('#TAG')  # Single request, no caching

# v3.0.0: High-performance setup  
config = ApiConfig(
    enable_caching=True,     # Automatic caching
    enable_metrics=True,     # Performance tracking  
    enable_rate_limiting=True, # Rate limiting (async)
    max_retries=3           # Auto-retry on failures
)

api = CocApi('token', config=config)
clan = api.clan_tag('#TAG')  # Cached, monitored, with retry protection

# Async mode with concurrency
async with CocApi('token', config=config) as api:
    # Process multiple clans concurrently with rate limiting
    clans = await asyncio.gather(*[
        api.clan_tag(tag) for tag in clan_tags  # 10x+ faster than sequential
    ])
```

## Migration Guide 

### 🔄 Upgrading to v3.0.0 - Zero Breaking Changes!

**IMPORTANT: cocapi 3.0.0 maintains 100% backward compatibility. Your existing code will continue to work exactly as before with zero changes required.**

```python
# All existing code continues to work identically in v3.0.0
from cocapi import CocApi

# Old initialization patterns - ALL STILL WORK
api = CocApi('YOUR_TOKEN')                           # ✅ Works
api = CocApi('YOUR_TOKEN', 60)                       # ✅ Works  
api = CocApi('YOUR_TOKEN', 60, True)                 # ✅ Works
api = CocApi('YOUR_TOKEN', timeout=30, status_code=True)  # ✅ Works

# All existing methods - ALL STILL WORK
clan = api.clan_tag('#CLAN_TAG')                     # ✅ Works
player = api.players('#PLAYER_TAG')                  # ✅ Works
locations = api.locations()                          # ✅ Works
# ... all other methods work identically

# Async usage - ALL STILL WORKS
async with CocApi('YOUR_TOKEN') as api:              # ✅ Works
    clan = await api.clan_tag('#CLAN_TAG')           # ✅ Works

# ApiConfig usage - ALL STILL WORKS  
config = ApiConfig(timeout=60, enable_caching=True)  # ✅ Works
api = CocApi('YOUR_TOKEN', config=config)            # ✅ Works
```

### What's Changed in v3.0.0?
- ✅ **Added** enterprise features (metrics, middleware, enhanced caching)
- ✅ **Added** custom endpoint support and dynamic Pydantic models  
- ✅ **Added** base URL configuration with safety warnings
- ✅ **Enhanced** async support with rate limiting and performance improvements
- ✅ **Enhanced** error handling with detailed error types and retry logic
- ✅ **Maintained** 100% backward compatibility
- ❌ **No breaking changes** - existing code works unchanged
- ❌ **No deprecated methods** - all existing methods remain

### For Existing Users

### Upgrading to New Features

To take advantage of new features:

```python
from cocapi import CocApi, ApiConfig

# 1. Add caching to existing code (no changes needed!)
config = ApiConfig(enable_caching=True, cache_ttl=300)
api = CocApi('YOUR_TOKEN', config=config)

# 2. Use async for better performance (same class!)
async with CocApi('YOUR_TOKEN') as api:
    clan = await api.clan_tag('#CLAN_TAG')

# 3. Enhanced error handling is automatic
result = api.clan_tag('#INVALID_TAG')
if result.get('result') == 'error':
    print(f"Error: {result.get('message')}")
```

---

## 🚀 What's New in v3.0.0 - Major Release

**cocapi 3.0.0** is a major release that transforms the library into an enterprise-grade API wrapper while maintaining 100% backward compatibility. This release introduces comprehensive monitoring, middleware system, enhanced performance features, and future-proofing capabilities.

### 🎯 **Major New Features**

#### 1. **Enterprise Metrics & Analytics** 📊
Comprehensive API performance monitoring and insights:
```python
# Track performance, errors, cache hits, response times
config = ApiConfig(enable_metrics=True, metrics_window_size=1000)
api = CocApi('token', config=config)

metrics = api.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Average response time: {metrics['avg_response_time']:.2f}ms")
print(f"Error rate: {metrics['error_rate']:.1%}")

# Get actionable performance insights
for insight in metrics['performance_insights']:
    print(f"💡 {insight}")
```

#### 2. **Middleware System** 🔌
Pluggable request/response processing pipeline:
```python
from cocapi.middleware import add_user_agent_middleware, add_request_id_middleware

# Add built-in middleware
api.add_request_middleware(add_user_agent_middleware("MyApp/1.0"))
api.add_request_middleware(add_request_id_middleware())

# Custom middleware for authentication, logging, monitoring
def add_custom_headers(url, headers, params):
    headers['X-API-Version'] = '3.0.0'
    return url, headers, params

api.add_request_middleware(add_custom_headers)
```

#### 3. **Advanced Async Features** ⚡
Enhanced async support with rate limiting and performance optimizations:
```python
config = ApiConfig(
    enable_rate_limiting=True,
    requests_per_second=10.0,
    burst_limit=20,
    enable_caching=True
)

async with CocApi('token', config=config) as api:
    # Concurrent requests with automatic rate limiting
    results = await asyncio.gather(*[
        api.clan_tag(tag) for tag in clan_tags
    ])
```

#### 4. **Custom Endpoint Support** 🔮
Future-proof with support for any new SuperCell endpoints:
```python
# Use ANY new endpoint immediately without library updates
result = api.custom_endpoint('/new-supercell-feature')
result = api.custom_endpoint('/hypothetical-endpoint/v2', {'param': 'value'})

# With dynamic Pydantic models for type safety
result = api.custom_endpoint('/new-endpoint', use_dynamic_model=True)
print(result.some_field)  # Type-safe attribute access
```

### 📈 **Performance & Reliability Improvements**

- **📊 Comprehensive Metrics**: Track response times, error rates, cache performance, and endpoint usage
- **🔌 Middleware Pipeline**: Extensible request/response processing with minimal overhead  
- **⚡ Enhanced Async**: Rate limiting, connection pooling, and improved concurrency handling
- **💾 Smart Caching**: Detailed statistics, TTL management, and memory usage tracking
- **🛡️ Better Error Handling**: Specific error types, retry logic, and detailed error messages
- **🎯 Type Safety**: Enhanced type hints and optional Pydantic model integration
- **📝 Audit Logging**: Comprehensive logging for configuration changes and operations

### 🛡️ **Safety & Security Features**

- **🔒 Safe URL Changes**: Mandatory `force=True` parameter prevents accidental base URL changes
- **✅ URL Validation**: Strict validation of endpoint URLs and HTTP/HTTPS scheme enforcement  
- **⚠️ Clear Warnings**: Comprehensive warnings about configuration changes and potential risks
- **📋 Request Validation**: Parameter validation and sanitization for all API calls
- **🔄 Graceful Degradation**: Fallback mechanisms when optional features are unavailable

### 🔄 **100% Backward Compatibility**

**Your existing code works unchanged:**
```python
# All existing code continues to work exactly the same
from cocapi import CocApi
api = CocApi('YOUR_TOKEN', 30, True)
clan = api.clan_tag('#CLAN_TAG')
# Zero changes needed!
```

### 🎉 **What This Means for Developers**

1. **📊 Data-Driven**: Make informed decisions with comprehensive API metrics and performance insights
2. **🔌 Extensible**: Add custom functionality through the middleware system without modifying core code  
3. **⚡ High-Performance**: Handle high-throughput scenarios with async rate limiting and intelligent caching
4. **🔮 Future-Proof**: Never wait for library updates when SuperCell adds new endpoints
5. **🛡️ Production-Ready**: Enterprise-grade reliability with monitoring, retry logic, and error handling
6. **🎯 Type-Safe**: Enhanced IDE support and validation for better development experience
7. **🌐 Testing-Ready**: Easily test against staging environments, proxies, or mock servers
8. **🔄 Zero Migration**: Existing applications need no changes to benefit from new features

### 📦 **Installation**

```bash
# Upgrade to 3.0.0 (100% backward compatible)
pip install --upgrade cocapi

# Or with Pydantic models support
pip install --upgrade 'cocapi[pydantic]'
```

---

## Previous Releases

### What's New in v2.2.x

🆕 **v2.2.0-2.2.4 Features:**
- **Optional Pydantic Models**: Type-safe, validated data structures with IDE support
- **Enhanced Type Safety**: Full Pydantic model support for `Clan`, `Player`, and all API responses
- **Flexible Configuration**: Enable/disable Pydantic models via `ApiConfig.use_pydantic_models`
- **Lazy Loading**: Zero impact when not using models (automatic imports)
- **Async + Pydantic**: Full async support with Pydantic model validation
- **Comprehensive Models**: 15+ Pydantic models covering all API response types

## What's New in v2.1.0+

✨ **Major New Features:**
- **Unified Async Support**: Same `CocApi` class works for both sync and async!
- **Intelligent Caching**: Automatic response caching with configurable TTL
- **Retry Logic**: Exponential backoff for handling temporary API failures
- **Enhanced Configuration**: Flexible settings via ApiConfig class
- **Better Error Handling**: Comprehensive error messages and types
- **Type Hints**: Complete type annotations for better IDE support
- **Rate Limiting Protection**: Built-in handling of API rate limits
- **🆕 Optional Pydantic Models**: Type-safe, validated data structures with IDE support

🔧 **Code Quality Improvements:**
- Fixed all mutable default arguments
- Added comprehensive logging
- Improved test coverage
- Enhanced documentation

📚 **Full API Reference**

The following sections document all available API methods. All methods work identically in both sync and async modes - just use `await` when in async context!

---

## Clans

### Information about a Clan
```python
api.clan_tag(tag) #example tag "#9UOVJJ9J"
```
<details>
 <summary>Click to view output</summary>

```text
{
  "warLeague": {
    "name": {},
    "id": 0
  },
  "memberList": [
    {
      "league": {
        "name": {},
        "id": 0,
        "iconUrls": {}
      },
      "tag": "string",
      "name": "string",
      "role": "string",
      "expLevel": 0,
      "clanRank": 0,
      "previousClanRank": 0,
      "donations": 0,
      "donationsReceived": 0,
      "trophies": 0,
      "versusTrophies": 0
    }
  ],
  "isWarLogPublic": true,
  "tag": "string",
  "warFrequency": "string",
  "clanLevel": 0,
  "warWinStreak": 0,
  "warWins": 0,
  "warTies": 0,
  "warLosses": 0,
  "clanPoints": 0,
  "clanVersusPoints": 0,
  "requiredTrophies": 0,
  "name": "string",
  "location": {
    "localizedName": "string",
    "id": 0,
    "name": "string",
    "isCountry": true,
    "countryCode": "string"
  },
  "type": "string",
  "members": 0,
  "labels": [
    {
      "name": {},
      "id": 0,
      "iconUrls": {}
    }
  ],
  "description": "string",
  "badgeUrls": {}
}
```
</details>

#### Members Only
```python
api.clan_members(tag)
```
returns membersList information from api.clan_tag(tag) under "items" in dict

### War Log Information
```python
api.clan_war_log(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{items:
[
  {
    "clan": {
      "destructionPercentage": {},
      "tag": "string",
      "name": "string",
      "badgeUrls": {},
      "clanLevel": 0,
      "attacks": 0,
      "stars": 0,
      "expEarned": 0,
      "members": [
        {
          "tag": "string",
          "name": "string",
          "mapPosition": 0,
          "townhallLevel": 0,
          "opponentAttacks": 0,
          "bestOpponentAttack": {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          },
          "attacks": [
            {
              "order": 0,
              "attackerTag": "string",
              "defenderTag": "string",
              "stars": 0,
              "destructionPercentage": 0
            }
          ]
        }
      ]
    },
    "teamSize": 0,
    "opponent": {
      "destructionPercentage": {},
      "tag": "string",
      "name": "string",
      "badgeUrls": {},
      "clanLevel": 0,
      "attacks": 0,
      "stars": 0,
      "expEarned": 0,
      "members": [
        {
          "tag": "string",
          "name": "string",
          "mapPosition": 0,
          "townhallLevel": 0,
          "opponentAttacks": 0,
          "bestOpponentAttack": {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          },
          "attacks": [
            {
              "order": 0,
              "attackerTag": "string",
              "defenderTag": "string",
              "stars": 0,
              "destructionPercentage": 0
            }
          ]
        }
      ]
    },
    "endTime": "string",
    "result": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Current War Information
```python
api.clan_current_war(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "clan": {
    "destructionPercentage": {},
    "tag": "string",
    "name": "string",
    "badgeUrls": {},
    "clanLevel": 0,
    "attacks": 0,
    "stars": 0,
    "expEarned": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "mapPosition": 0,
        "townhallLevel": 0,
        "opponentAttacks": 0,
        "bestOpponentAttack": {
          "order": 0,
          "attackerTag": "string",
          "defenderTag": "string",
          "stars": 0,
          "destructionPercentage": 0
        },
        "attacks": [
          {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          }
        ]
      }
    ]
  },
  "teamSize": 0,
  "opponent": {
    "destructionPercentage": {},
    "tag": "string",
    "name": "string",
    "badgeUrls": {},
    "clanLevel": 0,
    "attacks": 0,
    "stars": 0,
    "expEarned": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "mapPosition": 0,
        "townhallLevel": 0,
        "opponentAttacks": 0,
        "bestOpponentAttack": {
          "order": 0,
          "attackerTag": "string",
          "defenderTag": "string",
          "stars": 0,
          "destructionPercentage": 0
        },
        "attacks": [
          {
            "order": 0,
            "attackerTag": "string",
            "defenderTag": "string",
            "stars": 0,
            "destructionPercentage": 0
          }
        ]
      }
    ]
  },
  "startTime": "string",
  "state": "string",
  "endTime": "string",
  "preparationStartTime": "string"
}
```
</details>

### Clan League Group Information
```python
api.clan_leaguegroup(tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "tag": "string",
  "state": "string",
  "season": "string",
  "clans": [
    {
      "tag": "string",
      "clanLevel": 0,
      "name": "string",
      "members": [
        {
          "tag": "string",
          "townHallLevel": 0,
          "name": "string"
        }
      ],
      "badgeUrls": {}
    }
  ],
  "rounds": [
    {
      "warTags": [
        "string"
      ]
    }
  ]
}
```
</details>

### Clan Capital Raid Seasons
```python
api.clan_capitalraidseasons(tag)
```
Retrieve clan's capital raid seasons information
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "state": "string",
    "startTime": "string", 
    "endTime": "string",
    "capitalTotalLoot": 0,
    "raidsCompleted": 0,
    "totalAttacks": 0,
    "enemyDistrictsDestroyed": 0,
    "offensiveReward": 0,
    "defensiveReward": 0,
    "members": [
      {
        "tag": "string",
        "name": "string",
        "attacks": 0,
        "attackLimit": 0,
        "bonusAttackLimit": 0,
        "capitalResourcesLooted": 0
      }
    ]
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Warleague Information
```python
api.warleague(war_tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "tag": "string",
  "state": "string",
  "season": "string",
  "clans": [
    {
      "tag": "string",
      "clanLevel": 0,
      "name": "string",
      "members": [
        {
          "tag": "string",
          "townHallLevel": 0,
          "name": "string"
        }
      ],
      "badgeUrls": {}
    }
  ],
  "rounds": [
    {
      "warTags": [
        "string"
      ]
    }
  ]
}
```
</details>




## Player

### Player information
```python
api.players(player_tag) #for example "#900PUCPV"
```
<details>
 <summary>Click to view output</summary>

```text
{
  "clan": {
    "tag": "string",
    "clanLevel": 0,
    "name": "string",
    "badgeUrls": {}
  },
  "league": {
    "name": {},
    "id": 0,
    "iconUrls": {}
  },
  "townHallWeaponLevel": 0,
  "versusBattleWins": 0,
  "legendStatistics": {
    "previousSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "previousVersusSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "bestVersusSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "legendTrophies": 0,
    "currentSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    },
    "bestSeason": {
      "trophies": 0,
      "id": "string",
      "rank": 0
    }
  },
  "troops": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "heroes": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "spells": [
    {
      "level": 0,
      "name": {},
      "maxLevel": 0,
      "village": "string"
    }
  ],
  "role": "string",
  "attackWins": 0,
  "defenseWins": 0,
  "townHallLevel": 0,
  "labels": [
    {
      "name": {},
      "id": 0,
      "iconUrls": {}
    }
  ],
  "tag": "string",
  "name": "string",
  "expLevel": 0,
  "trophies": 0,
  "bestTrophies": 0,
  "donations": 0,
  "donationsReceived": 0,
  "builderHallLevel": 0,
  "versusTrophies": 0,
  "bestVersusTrophies": 0,
  "warStars": 0,
  "achievements": [
    {
      "stars": 0,
      "value": 0,
      "name": {},
      "target": 0,
      "info": {},
      "completionInfo": {},
      "village": "string"
    }
  ],
  "versusBattleWinCount": 0
}
```
</details>




## Locations

### All Locations Information
```python
api.location()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "localizedName": "string",
    "id": 0,
    "name": "string",
    "isCountry": true,
    "countryCode": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Information for a Single Location
```python
api.location_id(location_tag) #for example "32000047"
```

returns the above information for a single location

### Top Clans in a Location
```python
api.location_id_clan_rank(location_tag)
```
Top 200 clans in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clanLevel": 0,
    "clanPoints": 0,
    "location": {
      "localizedName": "string",
      "id": 0,
      "name": "string",
      "isCountry": true,
      "countryCode": "string"
    },
    "members": 0,
    "tag": "string",
    "name": "string",
    "rank": 0,
    "previousRank": 0,
    "badgeUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Top Players in a Location
```python
api.clan_leaguegroup(location_tag)
```
Top 200 players in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "league": {
      "name": {},
      "id": 0,
      "iconUrls": {}
    },
    "attackWins": 0,
    "defenseWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "trophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>


### Top Versus Clans in a Location
```python
api.location_clan_versus(location_tag)
```
Top 200 versus clans in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clanPoints": 0,
    "clanVersusPoints": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>


### Top Versus Players in a Location
```python
api.location_player_versus(location_tag)
```
Top 200 versus players in a given location
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "versusBattleWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "versusTrophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>




## Leagues

### List leagues
```python
api.league()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


### League Information
```python
api.league_id(league_tag)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>


### List Season Leagues
```python
api.league_season(league_tag)
```
Information is available only for Legend League
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "id": "string"
  }
],
"paging": {'cursors': {}}
}
```
</details>


### League Season Ranking
```python
api.league_season_id(league_tag, season_tag)
```
Information is available only for Legend League
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "clan": {
      "tag": "string",
      "name": "string",
      "badgeUrls": {}
    },
    "league": {
      "name": {},
      "id": 0,
      "iconUrls": {}
    },
    "attackWins": 0,
    "defenseWins": 0,
    "tag": "string",
    "name": "string",
    "expLevel": 0,
    "rank": 0,
    "previousRank": 0,
    "trophies": 0
  }
],
"paging": {'cursors': {}}
}
```
</details>

### List Capital Leagues
```python
api.capitalleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Capital League Information
```python
api.capitalleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>

### List Builder Base Leagues
```python
api.builderbaseleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### Builder Base League Information
```python
api.builderbaseleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>

### List War Leagues
```python
api.warleagues()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>

### War League Information
```python
api.warleagues_id(league_id)
```
<details>
 <summary>Click to view output</summary>

```text
{
  "name": {},
  "id": 0,
  "iconUrls": {}
}
```
</details>




## Gold Pass

### Current Gold Pass Season
```python
api.goldpass_seasons_current()
```
Get information about the current gold pass season
<details>
 <summary>Click to view output</summary>

```text
{
  "startTime": "string",
  "endTime": "string" 
}
```
</details>


## Labels

### List Clan Labels
```python
api.labels_clans()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


### List Player Labels
```python
api.labels_players()
```
<details>
 <summary>Click to view output</summary>

```text
{"items":
[
  {
    "name": {},
    "id": 0,
    "iconUrls": {}
  }
],
"paging": {'cursors': {}}
}
```
</details>


## Credits
- [All Contributors](../../contributors)

*Note versions below 2.0.0 are not supported anymore*

*DISCLAIMER: cocapi is not affiliated with SuperCell©.
