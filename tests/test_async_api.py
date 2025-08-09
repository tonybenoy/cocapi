"""
Tests for async functionality of unified CocApi
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from cocapi import CocApi, ApiConfig


class TestAsyncCocApi:
    """Test async API functionality with unified CocApi"""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage"""
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock test response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client_instance.get.return_value = mock_response
            
            async with CocApi("test_token") as api:
                assert api._client is not None
                assert api.token == "test_token"
                
            # Verify client was closed
            mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_clan_tag(self):
        """Test async clan tag method"""
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock test response (for initialization)
            test_response = Mock()
            test_response.status_code = 200
            
            # Mock clan data response
            clan_response = Mock()
            clan_response.status_code = 200
            clan_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            clan_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [test_response, clan_response]
            
            async with CocApi("test_token") as api:
                result = await api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                assert result["name"] == "Test Clan"

    @pytest.mark.asyncio
    async def test_caching_works(self):
        """Test that caching works correctly"""
        config = ApiConfig(enable_caching=True, cache_ttl=60)
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock responses
            test_response = Mock()
            test_response.status_code = 200
            
            clan_response = Mock()
            clan_response.status_code = 200
            clan_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            clan_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [test_response, clan_response]
            
            async with AsyncCocApi("test_token", config=config) as api:
                # First call - should hit API
                result1 = await api.clan_tag("#TEST")
                assert result1["tag"] == "#TEST"
                
                # Second call - should hit cache (no additional HTTP call)
                result2 = await api.clan_tag("#TEST")
                assert result2["tag"] == "#TEST"
                
                # Should only have made 2 HTTP calls (1 for test, 1 for clan data)
                assert mock_client_instance.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test retry logic on rate limiting"""
        config = ApiConfig(max_retries=2, retry_delay=0.1)
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock test response
            test_response = Mock()
            test_response.status_code = 200
            
            # First response: rate limited
            rate_limit_response = Mock()
            rate_limit_response.status_code = 429
            
            # Second response: success
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {"tag": "#TEST"}
            success_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [
                test_response, 
                rate_limit_response,
                success_response
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                async with AsyncCocApi("test_token", config=config) as api:
                    result = await api.clan_tag("#TEST")
                    assert result["tag"] == "#TEST"
                    
                    # Should have slept for retry
                    mock_sleep.assert_called_once()

    @pytest.mark.asyncio 
    async def test_cache_management(self):
        """Test cache management functions"""
        config = ApiConfig(enable_caching=True)
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            test_response = Mock()
            test_response.status_code = 200
            mock_client_instance.get.return_value = test_response
            
            async with AsyncCocApi("test_token", config=config) as api:
                # Test cache stats
                stats = api.get_cache_stats()
                assert stats["cache_enabled"] is True
                assert stats["total_entries"] == 0
                
                # Test cache clearing
                api.clear_cache()
                assert len(api._cache) == 0


class TestApiConfig:
    """Test ApiConfig functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ApiConfig()
        assert config.base_url == "https://api.clashofclans.com/v1"
        assert config.timeout == 20
        assert config.max_retries == 3
        assert config.enable_caching is True
        assert config.cache_ttl == 300

    def test_custom_config(self):
        """Test custom configuration values"""
        config = ApiConfig(
            timeout=30,
            max_retries=5,
            enable_caching=False,
            cache_ttl=600
        )
        assert config.timeout == 30
        assert config.max_retries == 5
        assert config.enable_caching is False
        assert config.cache_ttl == 600


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__]))