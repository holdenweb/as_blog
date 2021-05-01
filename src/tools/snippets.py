import sys
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
    l_no: int, line: str, snippet: Optional[List[str]], start_end: List[Tuple[int, int]]
):
    start = line.startswith(SN_PREFIX)
    end = line.startswith(SN_CLOSE)
    if start:
        if snippet is not None:
            start_end.append((snippet, l_no))
        snippet = l_no
    elif end:
        if snippet is None:
            raise ValueError(f"Snippet ends without start on line {l_no+1}")
        start_end.append((snippet, l_no + 1))
        snippet = None
    return snippet


def snippet_ranges(lines: str):
    start_end = []
    snippet = None
    for l_no, line in enumerate(lines):
        snippet = process_line(l_no, line, snippet, start_end)
    if snippet:
        start_end.append((snippet, -1))
    return start_end


def snippets(lines):
    result = []
    for (start, end) in snippet_ranges(lines):
        s_lines = lines[start + 1 : end]
        title = lines[start][len(SN_PREFIX) :]
        if s_lines and s_lines[-1] == SN_CLOSE:  # currently optional
            del s_lines[-1]
        result.append(Snippet(title, s_lines))
    return result
