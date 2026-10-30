import base64

import pytest
from PySide6.QtGui import QImage

from app.project import Project, ProjectFormatError
from app.project.portrait import MAX_PORTRAIT_BYTES, decode_portrait
from app.ui.portrait import load_portrait


def test_portrait_round_trips_through_project_and_character_export(tmp_path):
    image = QImage(10, 10, QImage.Format.Format_RGB32)
    image.fill(0xff55aa22)
    source = tmp_path / "portrait.png"
    assert image.save(str(source))
    portrait, preview = load_portrait(path=str(source))
    assert not preview.isNull()
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    character.portrait = portrait
    project.update_character(character.id, character)
    assert Project.open(project.root).get_character(character.id).portrait == portrait
    exported = tmp_path / "character.yaml"
    project.export_character(character.id, exported)
    other = Project.create(tmp_path / "other", "Other")
    imported = other.import_character(exported)
    assert imported.id != character.id
    assert imported.portrait == portrait
    assert load_portrait(encoded=imported.portrait)[1].size() == image.size()


@pytest.mark.parametrize("value", ["not base64", base64.b64encode(b"not an image").decode(), base64.b64encode(b"x" * (MAX_PORTRAIT_BYTES + 1)).decode()])
def test_invalid_portrait_is_rejected(value):
    with pytest.raises(ValueError):
        decode_portrait(value)


def test_invalid_portrait_cannot_be_saved(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    character.portrait = "invalid"
    with pytest.raises(ProjectFormatError):
        project.update_character(character.id, character)
    assert not Project.open(project.root).get_character(character.id).portrait


def test_corrupt_image_and_oversized_dimensions_are_rejected(tmp_path):
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"\x89PNG\r\n\x1a\ninvalid")
    with pytest.raises(ValueError):
        load_portrait(path=str(corrupt))
    large = QImage(2049, 1, QImage.Format.Format_RGB32)
    large.fill(0)
    source = tmp_path / "large.png"
    assert large.save(str(source))
    with pytest.raises(ValueError, match="dimensions"):
        load_portrait(path=str(source))
