from app.document.merge import merge_text


def test_merge_disjoint_edits_preserves_both_versions():
    result = merge_text("one\ntwo\nthree\nfour\n", "ONE\ntwo\nthree\nfour\n", "one\ntwo\nthree\nFOUR\n")
    assert result.text == "ONE\ntwo\nthree\nFOUR\n"
    assert result.conflicts == 0


def test_overlapping_edits_are_explicit_and_include_both_alternatives():
    result = merge_text("first\noriginal\nlast\n", "first\nmine\nlast\n", "first\ntheirs\nlast\n")
    assert result.conflicts == 1
    assert result.text == "first\n<<<<<<< OPEN BUFFER\nmine\n=======\ntheirs\n>>>>>>> DISK\nlast\n"


def test_same_insertion_is_not_a_conflict_but_different_insertions_are():
    assert merge_text("a\n", "added\na\n", "added\na\n").text == "added\na\n"
    result = merge_text("a\n", "mine\na\n", "theirs\na\n")
    assert result.conflicts == 1 and "mine\n" in result.text and "theirs\n" in result.text


def test_unchanged_side_and_missing_final_newline_are_preserved():
    assert merge_text("a", "a", "b").text == "b"
    assert merge_text("a", "b", "a").text == "b"
    result = merge_text("a", "mine", "theirs")
    assert result.text == "<<<<<<< OPEN BUFFER\nmine\n=======\ntheirs\n>>>>>>> DISK\n"


def test_large_input_is_conservatively_flagged():
    base = "a\n" * 2001
    result = merge_text(base, "mine\n" + base, base + "theirs\n")
    assert result.conflicts == 1
    assert "mine\n" in result.text and "theirs\n" in result.text


def test_delete_and_boundary_insertion_are_flagged_instead_of_lost():
    result = merge_text("a\nb\nc\n", "a\nc\n", "a\nnew\nb\nc\n")
    assert result.conflicts == 1
    assert "new\nb\n" in result.text
    assert result.text.endswith("c\n")
