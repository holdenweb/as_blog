from snippets import Snippet
from snippets import snippet_ranges
from snippets import snippets


def test_empty_snippets():
    lines = """\
Line 1 is not part of a snippet
# snippet prefix-1
# snippet prefix-2
# end snippet
""".splitlines()
    r = snippet_ranges(lines)
    assert r == [(1, 2), (2, 4)]
    sn = snippets(lines)
    assert all(s.lines == [] for s in sn)
