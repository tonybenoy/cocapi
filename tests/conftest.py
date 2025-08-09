"""
Test configuration and shared fixtures for cocapi tests.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from cocapi import CocApi, ApiConfig


class TestHelpers:
    """Shared test helper methods"""
    
    @staticmethod
    def create_mock_response(status_code=200, json_data=None, should_raise=False):
        """Create a mock HTTP response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {"result": "success"}
        
        if should_raise:
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        else:
            mock_response.raise_for_status.return_value = None
            
        return mock_response

    @staticmethod
    def create_success_response():
        """Create a standard success test response"""
        return TestHelpers.create_mock_response(
            json_data={"result": "success", "message": "Api is up and running!"}
        )

    @staticmethod
    def create_clan_response(tag="#TEST", name="Test Clan"):
        """Create a mock clan response"""
        return TestHelpers.create_mock_response(
            json_data={"tag": tag, "name": name, "clanLevel": 10}
        )

    @staticmethod
    def create_player_response(tag="#PLAYER", name="Test Player"):
        """Create a mock player response"""
        return TestHelpers.create_mock_response(
            json_data={"tag": tag, "name": name, "townHallLevel": 12}
        )

    @staticmethod
    def create_error_response(status_code, message):
        """Create a mock error response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        return mock_response


@pytest.fixture
def test_helpers():
    """Provide test helpers"""
    return TestHelpers


@pytest.fixture
def mock_success_api_init():
    """Mock successful API initialization"""
    with patch.object(CocApi, 'test', return_value={"result": "success"}):
        yield


@pytest.fixture
def basic_api(mock_success_api_init):
    """Create a basic API instance with mocked initialization"""
    return CocApi("test_token")


@pytest.fixture
def api_with_config(mock_success_api_init):
    """Create API instance with custom config"""
    config = ApiConfig(
        enable_caching=True,
        max_retries=2,
        retry_delay=0.1,
        use_pydantic_models=False
    )
    return CocApi("test_token", config=config)


@pytest.fixture
def pydantic_api(mock_success_api_init):
    """Create API instance with Pydantic models enabled"""
    config = ApiConfig(use_pydantic_models=True)
    return CocApi("test_token", config=config)


class AsyncTestHelpers:
    """Helper methods for async tests"""
    
    @staticmethod
    def setup_async_client_mock():
        """Set up async client mock with common patterns"""
        async_client_mock = AsyncMock()
        
        # Default successful responses
        success_response = TestHelpers.create_success_response()
        async_client_mock.get.return_value = success_response
        
        return async_client_mock

    @staticmethod
    async def create_async_api_context(token="test_token", config=None):
        """Create async API context with mocked client"""
        with patch('cocapi.cocapi.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncTestHelpers.setup_async_client_mock()
            mock_client.return_value = mock_client_instance
            
            async with CocApi(token, config=config) as api:
                yield api, mock_client_instance


@pytest.fixture
def async_helpers():
    """Provide async test helpers"""
    return AsyncTestHelpers


# Common test data
@pytest.fixture
def sample_clan_data():
    """Sample clan data for testing"""
    return {
        "tag": "#TEST_CLAN",
        "name": "Test Clan",
        "clanLevel": 15,
        "members": 25,
        "clanPoints": 50000
    }


@pytest.fixture
def sample_player_data():
    """Sample player data for testing"""
    return {
        "tag": "#TEST_PLAYER", 
        "name": "Test Player",
        "townHallLevel": 12,
        "expLevel": 150,
        "trophies": 3500
    }


@pytest.fixture
def http_error_test_cases():
    """Common HTTP error test cases"""
    return [
        (400, "Bad request - check your parameters"),
        (403, "Forbidden - invalid API token or access denied"),
        (404, "Not found - check clan/player tag"),
        (429, "Rate limited - too many requests"),
        (500, "Server error - try again later"),
    ]