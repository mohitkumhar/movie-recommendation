import pytest
from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.testing = True    # enable flask test mode (turn off error catching)
    return app.test_client()    # Return test client that can make HTTP requests to your app


# Test 1: Check if login page loads correctly
def test_login_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200


# Test 2:  Simulate login with invalid user
def test_invalid_user_login(client):

    with patch('app.users_collection.find_one', return_value=None):
        response = client.post("/", data={'username': "wronguser"}, follow_redirects=True)

        assert response.status_code == 200
        assert b'invalid username not found' in response.data.lower()






