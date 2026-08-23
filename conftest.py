import pytest
from django.contrib.auth.models import User
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before each test to prevent cross-test contamination."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db):
    """A regular authenticated user."""
    return User.objects.create_user(username="testuser", password="pass1234")


@pytest.fixture
def other_user(db):
    """A second user for testing data isolation."""
    return User.objects.create_user(username="otheruser", password="pass5678")


@pytest.fixture
def auth_client(client, user):
    """A test client authenticated as `user`."""
    client.force_login(user)
    return client
