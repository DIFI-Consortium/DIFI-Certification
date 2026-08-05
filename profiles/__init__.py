"""Dispatch profile-specific validation to modules in this package."""

from functools import lru_cache
from importlib import import_module
from pathlib import Path


_VALIDATOR_NAMES = (
    "validate_profile_context",
    "validate_profile_data",
    "validate_profile_version",
    "validate_profile_command",
)


def available_profiles():
    """Return the profile names provided by Python modules in this package."""
    return sorted(
        path.stem
        for path in Path(__file__).parent.glob("*.py")
        if path.stem != "__init__" and path.stem.isidentifier()
    )


@lru_cache(maxsize=None)
def load_profile(profile):
    """Load and validate the module selected by ``--profile``."""
    if not profile:
        return None
    if (
        not isinstance(profile, str)
        or not profile.isidentifier()
        or profile == "__init__"
    ):
        raise ValueError(f"Invalid profile name: {profile!r}")

    profile_path = Path(__file__).parent / f"{profile}.py"
    if not profile_path.is_file():
        raise FileNotFoundError(
            f"Profile {profile!r} does not exist (expected {profile_path})"
        )

    module = import_module(f"{__name__}.{profile}")
    missing_validators = [
        name for name in _VALIDATOR_NAMES if not callable(getattr(module, name, None))
    ]
    if missing_validators:
        raise AttributeError(
            f"Profile {profile!r} is missing required validator(s): "
            f"{', '.join(missing_validators)}"
        )
    return module


def _validate(profile, validator_name, parsed):
    module = load_profile(profile)
    if module is None:
        return []

    errors = getattr(module, validator_name)(profile, parsed)
    if errors is None:
        return []
    if not isinstance(errors, list):
        raise TypeError(
            f"{profile}.{validator_name}() must return a list of validation errors"
        )
    return errors


def validate_profile_context(profile, parsed):
    return _validate(profile, "validate_profile_context", parsed)


def validate_profile_data(profile, parsed):
    return _validate(profile, "validate_profile_data", parsed)


def validate_profile_version(profile, parsed):
    return _validate(profile, "validate_profile_version", parsed)


def validate_profile_command(profile, parsed):
    return _validate(profile, "validate_profile_command", parsed)
