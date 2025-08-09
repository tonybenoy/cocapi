"""
Fixed tests for async functionality of unified CocApi
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
            
            # Mock test response to prevent real API calls during initialization
            test_response = Mock()
            test_response.status_code = 200
            test_response.json.return_value = {"result": "success", "message": "Api is up and running!"}
            test_response.raise_for_status.return_value = None
            mock_client_instance.get.return_value = test_response
            
            # Test basic context manager usage
            async with CocApi("test_token") as api:
                assert api is not None
                assert api.async_mode is True
                
            # Verify cleanup was called
            mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_clan_tag(self):
        """Test async clan_tag method"""
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock responses: first for test(), second for clan_tag()
            test_response = Mock()
            test_response.status_code = 200
            test_response.json.return_value = {"result": "success"}
            test_response.raise_for_status.return_value = None
            
            clan_response = Mock()
            clan_response.status_code = 200
            clan_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            clan_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [test_response, clan_response]
            
            async with CocApi("test_token") as api:
                # Mock clan_tag to return test data
                result = await api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                assert result["name"] == "Test Clan"

    @pytest.mark.asyncio
    async def test_caching_works(self):
        """Test that caching works with async API"""
        config = ApiConfig(enable_caching=True, cache_ttl=300)
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock responses
            test_response = Mock()
            test_response.status_code = 200
            test_response.json.return_value = {"result": "success"}
            test_response.raise_for_status.return_value = None
            
            clan_response = Mock()
            clan_response.status_code = 200
            clan_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            clan_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [test_response, clan_response]
            
            async with CocApi("test_token", config=config) as api:
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
        """Test retry logic for rate limiting"""
        config = ApiConfig(
            max_retries=2,
            retry_delay=0.1,  # Short delay for testing
            enable_caching=False
        )
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock test response
            test_response = Mock()
            test_response.status_code = 200
            test_response.json.return_value = {"result": "success"}
            test_response.raise_for_status.return_value = None
            
            # Mock rate limit response followed by success
            rate_limit_response = Mock()
            rate_limit_response.status_code = 429
            
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            success_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [
                test_response, 
                rate_limit_response, 
                success_response
            ]
            
            async with CocApi("test_token", config=config) as api:
                result = await api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                # Should have made 3 calls: test + rate_limit + success
                assert mock_client_instance.get.call_count == 3

    @pytest.mark.asyncio
    async def test_cache_management(self):
        """Test cache management functionality"""
        config = ApiConfig(enable_caching=True)
        
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            # Mock responses
            test_response = Mock()
            test_response.status_code = 200
            test_response.json.return_value = {"result": "success"}
            test_response.raise_for_status.return_value = None
            
            clan_response = Mock()
            clan_response.status_code = 200
            clan_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
            clan_response.raise_for_status.return_value = None
            
            mock_client_instance.get.side_effect = [test_response, clan_response]
            
            async with CocApi("test_token", config=config) as api:
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


class TestApiConfig:
    """Test ApiConfig functionality"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ApiConfig()
        assert config.base_url == "https://api.clashofclans.com/v1"
        assert config.timeout == 20
        assert config.max_retries == 3
        assert config.enable_caching is True
        assert config.use_pydantic_models is False  # New feature

    def test_custom_config(self):
        """Test custom configuration"""
        config = ApiConfig(
            timeout=60,
            max_retries=5,
            enable_caching=False,
            use_pydantic_models=True  # Test new feature
        )
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.enable_caching is False
        assert config.use_pydantic_models is True