import pytest
from pydantic import ValidationError

from tdp.config import Settings


def test_local_identity_is_allowed_for_development_and_test() -> None:
    assert Settings(environment="development").auth_mode == "local"
    assert Settings(environment="test").auth_mode == "local"


def test_local_identity_is_rejected_for_shared_environments() -> None:
    with pytest.raises(ValidationError, match="restricted to development and test"):
        Settings(environment="production")

    with pytest.raises(ValidationError, match="restricted to development and test"):
        Settings(environment="staging")


def test_api_prefix_requires_a_root_relative_path() -> None:
    with pytest.raises(ValidationError, match="must begin"):
        Settings(api_prefix="api")
