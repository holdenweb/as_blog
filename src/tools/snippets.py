from typing import List
from typing import Optional
from typing import Tuple

from dataclasses import dataclass


SN_PREFIX = "# snippet "
SN_CLOSE = "# end snippet"


@dataclass
class Snippet:
    title: str
    lines: List[str]


def process_line(
    l_no: int, line: str, snippet: Optional[int], ranges: List[Tuple[int, int]]
) -> Optional[int]:
    start = line.startswith(SN_PREFIX)
    end = line.startswith(SN_CLOSE)
    if start:  # A new snippet starts here
        if snippet is not None:  # If we are currently in a snippet
            ranges.append((snippet, l_no))  # ... then add it to the ranges
        snippet = l_no
    elif end:
        if snippet is None:
            raise ValueError(f"Snippet ends without start on line {l_no+1}")
        ranges.append((snippet, l_no + 1))
        snippet = None
    return snippet


def snippet_ranges(lines: List[str]):
    ranges: List[str] = []
    snippet = None
    for l_no, line in enumerate(lines):
        snippet = process_line(l_no, line, snippet, ranges)
    if snippet:
        ranges.append((snippet, -1))
    return ranges


def snippets(lines: List[str]):
    result = []
    for (start, end) in snippet_ranges(lines):
        s_lines = lines[start + 1 : end]
        title = lines[start][len(SN_PREFIX) :]
        if s_lines and s_lines[-1] == SN_CLOSE:  # currently optional
            del s_lines[-1]
        result.append(Snippet(title, s_lines))
    return result
