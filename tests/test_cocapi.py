"""
Basic test suite for cocapi

These tests focus on backward compatibility and basic functionality.
Note: Most tests are mocked since they require valid API tokens and live data.
"""
import pytest
from unittest.mock import Mock, patch
from cocapi import CocApi


class TestCocApi:
    """Test class for CocApi functionality"""

    def test_init_with_valid_token(self):
        """Test initialization with valid parameters"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("valid_token", timeout=30, status_code=True)
            assert api.token == "valid_token"
            assert api.timeout == 30
            assert api.status_code is True
            assert api.ENDPOINT == "https://api.clashofclans.com/v1"

    def test_init_with_invalid_token_raises_error(self):
        """Test that invalid token raises error during initialization"""
        with patch.object(CocApi, 'test', return_value={"result": "error", "message": "Invalid token"}):
            with pytest.raises(ValueError) as exc_info:
                CocApi("invalid_token")
            assert "API initialization failed" in str(exc_info.value)

    def test_mutable_default_arguments_fixed(self):
        """Test that mutable default arguments are properly handled"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            # Mock the API response
            with patch.object(api, '_CocApi__api_response') as mock_response:
                mock_response.return_value = {"items": []}
                
                # Call methods with and without params
                result1 = api.clan_war_log("CLAN_TAG")
                result2 = api.clan_war_log("CLAN_TAG", {"limit": 10})
                result3 = api.clan_war_log("CLAN_TAG")  # Should not be affected by previous call
                
                # Verify all calls were made correctly
                assert mock_response.call_count == 3

    def test_backward_compatibility_no_params(self):
        """Test that methods work without parameters (backward compatibility)"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            with patch.object(api, '_CocApi__api_response') as mock_response:
                mock_response.return_value = {"items": []}
                
                # These should all work without parameters
                api.clan()
                api.league()
                api.locations()
                api.labels_clans()
                api.labels_players()

    def test_backward_compatibility_with_dict_params(self):
        """Test that methods work with dictionary parameters (backward compatibility)"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            with patch.object(api, '_CocApi__api_response') as mock_response:
                mock_response.return_value = {"items": []}
                
                # These should work with dictionary parameters
                params = {"limit": 10, "after": "cursor"}
                api.clan(params)
                api.league(params)
                api.locations(params)

    def test_error_handling_improvements(self):
        """Test improved error handling"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            # Test timeout error
            with patch('httpx.get') as mock_get:
                import httpx
                mock_get.side_effect = httpx.TimeoutException("Timeout")
                result = api.clan_tag("CLAN_TAG")
                
                assert result["result"] == "error"
                assert "timeout" in result["message"].lower()
                assert result["error_type"] == "timeout"

    def test_status_code_handling_fixed(self):
        """Test that status_code is properly added to responses"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", status_code=True)
            
            with patch('httpx.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"tag": "CLAN_TAG"}
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                result = api.clan_tag("CLAN_TAG")
                
                assert "status_code" in result
                assert result["status_code"] == 200

    def test_url_construction_safety(self):
        """Test that URL construction handles empty params safely"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            with patch('httpx.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"tag": "CLAN_TAG"}
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # Call without params
                api.clan_tag("CLAN_TAG")
                
                # Verify URL doesn't have empty query string
                called_url = mock_get.call_args[1]["url"]
                assert not called_url.endswith("?")

    def test_http_error_status_codes(self):
        """Test specific HTTP error status code handling"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            test_cases = [
                (400, "Bad request - check your parameters"),
                (403, "Forbidden - check your API token"),
                (404, "Not found - check clan/player tag"),
                (429, "Rate limited - too many requests"),
                (500, "Server error - try again later"),
            ]
            
            for status_code, expected_message in test_cases:
                with patch('httpx.get') as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = status_code
                    mock_get.return_value = mock_response
                    
                    result = api.clan_tag("CLAN_TAG")
                    
                    assert result["result"] == "error"
                    assert result["message"] == expected_message
                    assert result["status_code"] == status_code


# Backward compatibility tests
class TestBackwardCompatibility:
    """Ensure all existing usage patterns still work"""

    def test_old_usage_patterns_work(self):
        """Test that old code patterns still work exactly as before"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            # This should work exactly as before
            api = CocApi("token")
            
            with patch.object(api, '_CocApi__api_response') as mock_response:
                mock_response.return_value = {"items": []}
                
                # Old patterns that should still work
                result = api.clan_tag("#CLAN_TAG")
                result = api.players("#PLAYER_TAG")
                result = api.clan({"name": "test"})
                result = api.clan_members("#CLAN_TAG", {"limit": 20})
                
                # All should return the mocked response
                assert all(r == {"items": []} for r in [result])


class TestEnhancedFeatures:
    """Test enhanced features in sync API"""
    
    def test_caching_configuration(self):
        """Test caching can be configured"""
        from cocapi.config import ApiConfig
        config = ApiConfig(enable_caching=False)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            assert api.config.enable_caching is False

    def test_cache_management(self):
        """Test cache management methods"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            # Test cache stats
            stats = api.get_cache_stats()
            assert "total_entries" in stats
            assert "cache_enabled" in stats
            
            # Test cache clearing
            api.clear_cache()
            assert len(api._cache) == 0

    def test_retry_configuration(self):
        """Test retry behavior can be configured"""
        from cocapi.config import ApiConfig
        config = ApiConfig(max_retries=5, retry_delay=0.5)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            assert api.config.max_retries == 5
            assert api.config.retry_delay == 0.5

    def test_backward_compatibility_with_config(self):
        """Test that new config parameter doesn't break existing code"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            # Old way still works
            api1 = CocApi("token", timeout=30, status_code=True)
            assert api1.timeout == 30
            assert api1.status_code is True
            
            # New way with config
            from cocapi.config import ApiConfig
            config = ApiConfig(timeout=45)
            api2 = CocApi("token", config=config)
            assert api2.config.timeout == 45

    def test_caching_behavior(self):
        """Test that caching works correctly in sync API"""
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token")
            
            with patch('httpx.get') as mock_get:
                # Mock successful response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"tag": "#TEST", "name": "Test Clan"}
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # First call - should hit API
                result1 = api.clan_tag("#TEST")
                assert result1["tag"] == "#TEST"
                assert mock_get.call_count == 1
                
                # Second call - should hit cache (no additional HTTP call)
                result2 = api.clan_tag("#TEST")
                assert result2["tag"] == "#TEST"
                assert mock_get.call_count == 1  # Still only 1 call

    def test_retry_on_server_error(self):
        """Test retry logic on server errors"""
        from cocapi.config import ApiConfig
        config = ApiConfig(max_retries=2, retry_delay=0.1)
        
        with patch.object(CocApi, 'test', return_value={"result": "success"}):
            api = CocApi("token", config=config)
            
            with patch('httpx.get') as mock_get, patch('time.sleep') as mock_sleep:
                # First call: server error
                error_response = Mock()
                error_response.status_code = 500
                
                # Second call: success
                success_response = Mock()
                success_response.status_code = 200
                success_response.json.return_value = {"tag": "#TEST"}
                success_response.raise_for_status.return_value = None
                
                mock_get.side_effect = [error_response, success_response]
                
                result = api.clan_tag("#TEST")
                assert result["tag"] == "#TEST"
                
                # Should have retried once
                assert mock_get.call_count == 2
                mock_sleep.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])