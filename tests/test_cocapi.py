"""
Refactored test suite for cocapi with reduced duplication.

These tests focus on backward compatibility and basic functionality.
Note: Most tests are mocked since they require valid API tokens and live data.
"""
import pytest
from unittest.mock import Mock, patch
from cocapi import CocApi, ApiConfig


class TestCocApiInitialization:
    """Test CocApi initialization and basic setup"""

    def test_init_with_valid_token(self, test_helpers):
        """Test initialization with valid parameters"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("valid_token", timeout=30, status_code=True)
            
            # Verify initialization
            assert api.token == "valid_token"
            assert api.timeout == 30
            assert api.status_code is True
            assert api.ENDPOINT == "https://api.clashofclans.com/v1"

    def test_init_with_invalid_token_raises_error(self, test_helpers):
        """Test that invalid token raises error during initialization"""
        error_response = {"result": "error", "message": "Invalid token"}
        
        with patch.object(CocApi, 'test', return_value=error_response):
            with pytest.raises(ValueError) as exc_info:
                CocApi("invalid_token")
            assert "API initialization failed" in str(exc_info.value)


class TestBasicFunctionality:
    """Test basic API functionality with reduced duplication"""

    def test_mutable_default_arguments_fixed(self, basic_api):
        """Test that mutable default arguments are properly handled"""
        with patch.object(basic_api, '_CocApi__api_response') as mock_response:
            mock_response.return_value = {"items": []}
            
            # Call methods with and without params
            basic_api.clan_war_log("CLAN_TAG")
            basic_api.clan_war_log("CLAN_TAG", {"limit": 10})
            basic_api.clan_war_log("CLAN_TAG")  # Should not be affected
            
            assert mock_response.call_count == 3

    def test_backward_compatibility_methods(self, basic_api):
        """Test that methods work without parameters (backward compatibility)"""
        with patch.object(basic_api, '_CocApi__api_response') as mock_response:
            mock_response.return_value = {"items": []}
            
            # Test methods that should work without parameters
            methods_to_test = [
                basic_api.clan,
                basic_api.league, 
                basic_api.locations,
                basic_api.labels_clans,
                basic_api.labels_players
            ]
            
            for method in methods_to_test:
                method()
            
            assert mock_response.call_count == len(methods_to_test)

    def test_methods_with_dict_params(self, basic_api):
        """Test that methods work with dictionary parameters"""
        with patch.object(basic_api, '_CocApi__api_response') as mock_response:
            mock_response.return_value = {"items": []}
            
            params = {"limit": 10, "after": "cursor"}
            methods_to_test = [
                (basic_api.clan, params),
                (basic_api.league, params),
                (basic_api.locations, params)
            ]
            
            for method, param in methods_to_test:
                method(param)
            
            assert mock_response.call_count == len(methods_to_test)


class TestErrorHandling:
    """Test error handling with consolidated patterns"""

    def test_timeout_error_handling(self, basic_api):
        """Test timeout error handling"""
        with patch('httpx.get') as mock_get:
            import httpx
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            
            result = basic_api.clan_tag("CLAN_TAG")
            
            self._assert_error_response(result, "timeout", "timeout")

    def test_http_error_status_codes(self, basic_api, http_error_test_cases):
        """Test specific HTTP error status code handling"""
        for status_code, expected_message in http_error_test_cases:
            with patch('httpx.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_get.return_value = mock_response
                
                result = basic_api.clan_tag("CLAN_TAG")
                
                assert result["result"] == "error"
                assert result["message"] == expected_message
                assert result["status_code"] == status_code

    def _assert_error_response(self, result, message_contains, error_type):
        """Helper to assert error response format"""
        assert result["result"] == "error"
        assert message_contains in result["message"].lower()
        assert result["error_type"] == error_type


class TestResponseHandling:
    """Test response handling functionality"""

    def test_status_code_inclusion(self, test_helpers):
        """Test that status_code is properly added to responses"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", status_code=True)
            
            with patch('httpx.get') as mock_get:
                mock_response = test_helpers.create_clan_response()
                mock_get.return_value = mock_response
                
                result = api.clan_tag("CLAN_TAG")
                
                assert "status_code" in result
                assert result["status_code"] == 200

    def test_url_construction_safety(self, basic_api, test_helpers):
        """Test that URL construction handles empty params safely"""
        with patch('httpx.get') as mock_get:
            mock_response = test_helpers.create_clan_response()
            mock_get.return_value = mock_response
            
            basic_api.clan_tag("CLAN_TAG")
            
            # Verify URL doesn't have empty query string
            called_url = mock_get.call_args[1]["url"]
            assert not called_url.endswith("?")


class TestBackwardCompatibility:
    """Consolidated backward compatibility tests"""

    def test_old_usage_patterns(self, basic_api):
        """Test that old code patterns still work exactly as before"""
        with patch.object(basic_api, '_CocApi__api_response') as mock_response:
            mock_response.return_value = {"items": []}
            
            # Test various old patterns
            test_calls = [
                lambda: basic_api.clan_tag("#CLAN_TAG"),
                lambda: basic_api.players("#PLAYER_TAG"), 
                lambda: basic_api.clan({"name": "test"}),
                lambda: basic_api.clan_members("#CLAN_TAG", {"limit": 20})
            ]
            
            results = [call() for call in test_calls]
            
            # All should return the mocked response
            assert all(r == {"items": []} for r in results)
            assert mock_response.call_count == len(test_calls)


class TestEnhancedFeatures:
    """Test enhanced features with consolidated setup"""

    def test_caching_configuration(self):
        """Test caching can be configured"""
        config = ApiConfig(enable_caching=False)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            assert api.config.enable_caching is False

    def test_cache_management_methods(self, basic_api):
        """Test cache management methods"""
        # Test cache stats
        stats = basic_api.get_cache_stats()
        required_keys = ["total_entries", "cache_enabled", "active_entries"]
        
        for key in required_keys:
            assert key in stats
        
        # Test cache clearing
        basic_api.clear_cache()
        assert len(basic_api._cache) == 0

    def test_retry_configuration(self):
        """Test retry behavior can be configured"""
        config = ApiConfig(max_retries=5, retry_delay=0.5)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            assert api.config.max_retries == 5
            assert api.config.retry_delay == 0.5

    def test_caching_behavior(self, basic_api, test_helpers):
        """Test that caching works correctly"""
        with patch('httpx.get') as mock_get:
            mock_response = test_helpers.create_clan_response()
            mock_get.return_value = mock_response
            
            # First call - should hit API
            result1 = basic_api.clan_tag("#TEST")
            assert result1["tag"] == "#TEST"
            assert mock_get.call_count == 1
            
            # Second call - should hit cache
            result2 = basic_api.clan_tag("#TEST")
            assert result2["tag"] == "#TEST" 
            assert mock_get.call_count == 1  # Still only 1 call

    def test_retry_on_server_error(self, test_helpers):
        """Test retry logic on server errors"""
        config = ApiConfig(max_retries=2, retry_delay=0.1)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            
            with patch('httpx.get') as mock_get, patch('time.sleep'):
                # Setup responses: error then success
                error_response = test_helpers.create_mock_response(status_code=500)
                success_response = test_helpers.create_clan_response()
                mock_get.side_effect = [error_response, success_response]
                
                result = api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                assert mock_get.call_count == 2


class TestApiConfig:
    """Test ApiConfig functionality"""
    
    @pytest.mark.parametrize("use_pydantic", [True, False])
    def test_pydantic_configuration(self, use_pydantic):
        """Test Pydantic model configuration"""
        config = ApiConfig(use_pydantic_models=use_pydantic)
        assert config.use_pydantic_models is use_pydantic

    def test_config_defaults(self):
        """Test default configuration values"""
        config = ApiConfig()
        expected_defaults = {
            'base_url': "https://api.clashofclans.com/v1",
            'timeout': 20,
            'max_retries': 3,
            'enable_caching': True,
            'use_pydantic_models': False
        }
        
        for key, expected_value in expected_defaults.items():
            assert getattr(config, key) == expected_value

    def test_custom_config_values(self):
        """Test custom configuration"""
        custom_values = {
            'timeout': 60,
            'max_retries': 5,
            'enable_caching': False,
            'use_pydantic_models': True
        }
        
        config = ApiConfig(**custom_values)
        
        for key, expected_value in custom_values.items():
            assert getattr(config, key) == expected_value


if __name__ == "__main__":
    pytest.main([__file__])