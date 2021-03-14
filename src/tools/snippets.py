def snippet_ranges(lines):
    start_end = []
    snippet = None
    for l_no, line in enumerate(lines):
        start = line.startswith("# snippet ")
        end = line.startswith("# end snippet")
        if start:
            if snippet is not None:
                start_end.append((snippet, l_no))
            snippet = l_no
        elif end:
            if snippet is None:
                raise ValueError(f"Snippet ends without start on line {l_no+1}")
            start_end.append((snippet, l_no + 1))
            snippet = None
    if snippet:
        start_end.append((snippet, -1))
    return start_end
