import pytest

from app.document.text_formatting import (
    convert_case,
    format_like_book,
    indent_lines,
    outdent_lines,
    trim_trailing_whitespace,
)


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("upper", "HELLO WORLD"),
        ("lower", "hello world"),
        ("title", "Hello World"),
    ],
)
def test_convert_case(style, expected):
    assert convert_case("hello world", style) == expected


def test_convert_case_rejects_unknown_style():
    with pytest.raises(ValueError, match="Unsupported case style"):
        convert_case("text", "sentence")


def test_trim_trailing_whitespace_preserves_line_endings_and_indentation():
    assert trim_trailing_whitespace("  first  \r\n\tsecond \n") == "  first\r\n\tsecond\n"


def test_trim_trailing_whitespace_supports_classic_mac_line_endings():
    assert trim_trailing_whitespace("  first  \r\tsecond \r") == "  first\r\tsecond\r"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Opening line\ncontinued line\n\nNext paragraph\n",
            "    Opening line\ncontinued line\n\n    Next paragraph\n",
        ),
        (
            "  First\r\n\r\n\tSecond\r\n",
            "    First\r\n\r\n    Second\r\n",
        ),
        ("", ""),
        ("\n\n", "\n\n"),
    ],
)
def test_format_like_book_indents_paragraphs_and_preserves_layout(text, expected):
    assert format_like_book(text) == expected


def test_indent_and_outdent_preserve_blank_lines_and_line_endings():
    original = "first\r\n\r\n\tsecond\n"
    indented = "    first\r\n\r\n    \tsecond\n"

    assert indent_lines(original) == indented
    assert outdent_lines(indented) == original
    assert outdent_lines("\tindented\n") == "indented\n"


def test_formatting_does_not_treat_unicode_separators_as_file_line_endings():
    text = "first\u2028second\nthird"
    assert indent_lines(text) == "    first\u2028second\n    third"
    assert outdent_lines("    first\u2028    second") == "first\u2028    second"
