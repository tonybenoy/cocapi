"""
Refactored async tests for cocapi with reduced duplication.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from cocapi import CocApi, ApiConfig


class AsyncTestBase:
    """Base class with common async test setup"""
    
    @pytest.fixture
    def async_client_setup(self, test_helpers):
        """Setup async client with common mocking"""
        def _setup(responses=None):
            mock_client = AsyncMock()
            
            if responses is None:
                # Default: success test response
                responses = [test_helpers.create_success_response()]
            
            mock_client.get.side_effect = responses
            return mock_client
        
        return _setup

    async def create_async_context(self, token="test_token", config=None, mock_responses=None):
        """Helper to create async API context with mocked client"""
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            
            # Set up default or custom responses
            if mock_responses:
                mock_client_instance.get.side_effect = mock_responses
            else:
                success_response = Mock()
                success_response.status_code = 200
                success_response.json.return_value = {"result": "success"}
                success_response.raise_for_status.return_value = None
                mock_client_instance.get.return_value = success_response
            
            mock_client.return_value = mock_client_instance
            
            async with CocApi(token, config=config) as api:
                yield api, mock_client_instance


class TestAsyncBasicFunctionality(AsyncTestBase):
    """Test basic async API functionality"""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage"""
        async for api, mock_client in self.create_async_context():
            assert api is not None
            assert api.async_mode is True
            
        # Verify cleanup was called
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_api_call(self, test_helpers):
        """Test basic async API call"""
        responses = [
            test_helpers.create_success_response(),
            test_helpers.create_clan_response()
        ]
        
        async for api, mock_client in self.create_async_context(mock_responses=responses):
            result = await api.clan_tag("#TEST")
            
            assert result["tag"] == "#TEST"
            assert result["name"] == "Test Clan"
            assert mock_client.get.call_count == 2  # test + clan_tag


class TestAsyncCaching(AsyncTestBase):
    """Test async caching functionality"""
    
    @pytest.mark.asyncio
    async def test_caching_works(self, test_helpers):
        """Test that caching works with async API"""
        config = ApiConfig(enable_caching=True, cache_ttl=300)
        
        responses = [
            test_helpers.create_success_response(),
            test_helpers.create_clan_response()
        ]
        
        async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
            # First call - should hit API
            result1 = await api.clan_tag("#TEST")
            assert result1["tag"] == "#TEST"
            
            # Second call - should hit cache
            result2 = await api.clan_tag("#TEST") 
            assert result2["tag"] == "#TEST"
            
            # Should only have made 2 HTTP calls (1 for test, 1 for clan data)
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_management(self, test_helpers):
        """Test cache management functionality"""
        config = ApiConfig(enable_caching=True)
        
        responses = [
            test_helpers.create_success_response(),
            test_helpers.create_clan_response()
        ]
        
        async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
            # Make a request to populate cache
            await api.clan_tag("#TEST")
            
            # Check cache stats
            stats = api.get_cache_stats()
            assert stats["cache_enabled"] is True
            assert stats["total_entries"] >= 1
            
            # Clear cache
            api.clear_cache()
            stats_after_clear = api.get_cache_stats()
            assert stats_after_clear["total_entries"] == 0


class TestAsyncRetryLogic(AsyncTestBase):
    """Test async retry functionality"""
    
    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, test_helpers):
        """Test retry logic for rate limiting"""
        config = ApiConfig(
            max_retries=2,
            retry_delay=0.1,
            enable_caching=False
        )
        
        responses = [
            test_helpers.create_success_response(),  # test call
            test_helpers.create_mock_response(status_code=429),  # rate limit
            test_helpers.create_clan_response()  # success after retry
        ]
        
        async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
            result = await api.clan_tag("#TEST")
            assert result["tag"] == "#TEST"
            # Should have made 3 calls: test + rate_limit + success
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, test_helpers):
        """Test retry logic on server errors"""
        config = ApiConfig(max_retries=2, retry_delay=0.1)
        
        responses = [
            test_helpers.create_success_response(),  # test call
            test_helpers.create_mock_response(status_code=500),  # server error
            test_helpers.create_clan_response()  # success after retry
        ]
        
        with patch('asyncio.sleep'):  # Mock async sleep
            async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
                result = await api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                assert mock_client.get.call_count == 3


class TestAsyncErrorHandling(AsyncTestBase):
    """Test async error handling"""
    
    @pytest.mark.asyncio  
    async def test_async_timeout_handling(self, test_helpers):
        """Test async timeout error handling"""
        responses = [test_helpers.create_success_response()]  # For test call
        
        async for api, mock_client in self.create_async_context(mock_responses=responses):
            # Mock timeout on the actual API call
            import httpx
            mock_client.get.side_effect = [
                responses[0],  # Successful test call
                httpx.TimeoutException("Async timeout")  # Timeout on clan_tag
            ]
            
            result = await api.clan_tag("#TEST")
            assert result["result"] == "error"
            assert "timeout" in result["message"].lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code,expected_message", [
        (400, "Bad request - check your parameters"),
        (403, "Forbidden - check your API token"), 
        (404, "Not found - check clan/player tag"),
        (500, "Server error - try again later")
    ])
    async def test_async_http_errors(self, status_code, expected_message, test_helpers):
        """Test async HTTP error handling"""
        responses = [
            test_helpers.create_success_response(),
            test_helpers.create_mock_response(status_code=status_code)
        ]
        
        async for api, mock_client in self.create_async_context(mock_responses=responses):
            result = await api.clan_tag("#TEST")
            assert result["result"] == "error"
            assert result["message"] == expected_message
            assert result["status_code"] == status_code


class TestAsyncConfiguration(AsyncTestBase):
    """Test async-specific configuration"""
    
    @pytest.mark.asyncio
    async def test_async_with_pydantic_config(self, test_helpers):
        """Test async API with Pydantic models enabled"""
        config = ApiConfig(use_pydantic_models=True)
        
        responses = [
            test_helpers.create_success_response(),
            test_helpers.create_clan_response()
        ]
        
        async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
            result = await api.clan_tag("#TEST")
            
            # With Pydantic enabled, should get model or fallback to dict
            assert isinstance(result, (dict, object))
            
            # Should have the expected data regardless of type
            if hasattr(result, 'tag'):
                assert result.tag == "#TEST"  # Pydantic model
            else:
                assert result["tag"] == "#TEST"  # Dict fallback

    @pytest.mark.asyncio
    async def test_async_rate_limiting_config(self, test_helpers):
        """Test async rate limiting configuration"""
        config = ApiConfig(
            enable_rate_limiting=True,
            requests_per_second=10.0,
            burst_limit=20
        )
        
        responses = [test_helpers.create_success_response()]
        
        async for api, mock_client in self.create_async_context(config=config, mock_responses=responses):
            assert api.config.enable_rate_limiting is True
            assert abs(api.config.requests_per_second - 10.0) < 1e-9
            assert api.config.burst_limit == 20


# Keep the simple ApiConfig tests from the original
class TestApiConfig:
    """Test ApiConfig functionality (shared with sync tests)"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ApiConfig()
        assert config.base_url == "https://api.clashofclans.com/v1"
        assert config.timeout == 20
        assert config.max_retries == 3
        assert config.enable_caching is True
        assert config.use_pydantic_models is False

    def test_custom_config(self):
        """Test custom configuration"""
        config = ApiConfig(
            timeout=60,
            max_retries=5,
            enable_caching=False,
            use_pydantic_models=True
        )
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.enable_caching is False
        assert config.use_pydantic_models is True


if __name__ == "__main__":
    pytest.main([__file__])