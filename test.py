""" 
Testing for the Flask Application
It test login, logout and also simulates the database interaction
"""

from unittest.mock import patch
import pytest
from app import app

@pytest.fixture(name='client')
def client_fixture():
    """
    Enabling Flask Testing Mode by Turning of error catching 
    and returning test client that can make HTTP requests to the app
    """
    app.testing = True    # enable flask test mode (turn off error catching)
    return app.test_client()    # Return test client that can make HTTP requests to your app


# Test 1: Check if login page loads correctly
def test_login_page_loads(client):
    """
    Test if the login page loads correctly
    """
    response = client.get('/login')
    assert response.status_code == 200

# Test 2:  Simulate login with invalid user
def test_invalid_user_login(client):
    """
    Test by log in with invalid username
    """

    with patch('app.users_collection.find_one', return_value=None):
        response = client.post("/login", data={'username': "wronguser"}, follow_redirects=True)

        assert response.status_code == 200
        assert b'invalid username not found' in response.data.lower()

# Test 3
def test_logout(client):
    """
    Test the Logout API
    """
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302

    # follows the redirect from logout to index page

    login_page = client.get("/logout", follow_redirects=True)
    assert login_page.status_code == 200
    assert b'Enter Your Username' in login_page.data
