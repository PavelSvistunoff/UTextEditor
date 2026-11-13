"""Portable character profile export, independent of live project state."""

import os
from collections.abc import Callable
from pathlib import Path
import tempfile

import yaml

from .model import Character, character_to_mapping


def export_character_profile(
    character: Character, destination: Path | str, *, replace_existing: bool = False,
) -> Path:
    """Write one captured profile without project relationships."""
    return write_character_profile(lambda: character, destination, replace_existing=replace_existing)


def write_character_profile(
    load_character: Callable[[], Character], destination: Path | str, *, replace_existing: bool = False,
) -> Path:
    """Check the destination before loading/validating the profile, as project export does."""
    target = Path(destination)
    target_exists = target.exists()
    if target_exists and not replace_existing:
        raise FileExistsError(f"Character profile destination already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        {
            "character_format_version": 1,
            "character": character_to_mapping(load_character()),
        },
        allow_unicode=True,
        sort_keys=False,
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if replace_existing:
            if target_exists:
                os.chmod(temporary, target.stat().st_mode)
            os.replace(temporary, target)
        else:
            os.link(temporary, target)
            temporary.unlink()
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return target
