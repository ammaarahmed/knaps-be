import pytest
import asyncio
from src.storage import SQLStorage
from src.db_models import User


@pytest.mark.asyncio
async def test_user_operations():
    """Test basic user operations with the storage system."""
    storage = SQLStorage()
    
    # Test data
    test_keycloak_id = "test-keycloak-id-123"
    test_email = "test@example.com"
    
    # Create a test user
    user_data = User(
        keycloak_id=test_keycloak_id,
        email=test_email
    )
    
    # Test creating a user (this would require a database connection)
    # For now, we'll just test that the User model can be instantiated
    assert user_data.keycloak_id == test_keycloak_id
    assert user_data.email == test_email


@pytest.mark.asyncio
async def test_user_model_structure():
    """Test that the User model has the expected structure."""
    user = User(
        keycloak_id="test-id",
        email="test@example.com"
    )
    
    # Verify the model has the expected attributes
    assert hasattr(user, 'id')
    assert hasattr(user, 'keycloak_id')
    assert hasattr(user, 'email')
    assert hasattr(user, 'created_at')
    assert hasattr(user, 'updated_at')
    
    # Verify the values are set correctly
    assert user.keycloak_id == "test-id"
    assert user.email == "test@example.com" 