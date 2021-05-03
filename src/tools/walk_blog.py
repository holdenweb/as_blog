"""
Process a document into publishable blog format.
"""
import json
import os
import sys
import webbrowser
from functools import partial
from io import StringIO
from typing import List

from doc_utils import element_type
from doc_utils import para_type
from doc_utils import paragraphs_from
from docs import SQLDoc
from hu import ObjectDict as OD
from snippets import snippet_ranges


MARKER = "# snippet "
EXTRACT_PATH = "/Users/sholden/Projects/Python/blogAlexSteve/src/extracted"
SNIPPET_PATH = "/Users/sholden/Projects/Python/blogAlexSteve/src/snippets"
footnote_map = {}
font_map = set()
snippets = []
snippet_names = []


def handle_paragraph(p: OD) -> None:
    """
    A paragraph is a sequence of paragraphElements.
    """
    for pe in p.elements:
        handle_paragraphElement(pe)


class AnyOf:
    """
    Proxy the appropriate instance handler for
    one of the established sub-elements.
    """

    def __init__(self, elements: dict):
        """
        Record the possible sub-elements with their handlers.
        """
        self.sub_elements = elements

    def __call__(self, element: dict) -> None:
        """
        Given an element, select its handler by type and call it.

        We currently ignore elements for which no handler is mapped.
        """
        et = element_type(element)
        if et in self.sub_elements:
            return self.sub_elements[et](element[et])


# class EachOf(AnyOf):
# """
# Process an established sequence of sub-elements.
# """

# def __call__(self, element):
# for element_name, handler in self.sub_elements.items():
# handler(element[element_name])


class SequenceOf:
    """
    Handle a list of a given element type.
    """

    def __init__(self, handler):
        """
        Remember the handler.
        """
        self.handler = handler

    def __call__(self, element: List[OD]) -> None:
        """
        Given a list of elements of a given type, handle each one.
        """
        for sub_element in element:
            self.handler(sub_element)


se_handlers = {"paragraph": handle_paragraph}
handle_structuralElement = AnyOf(se_handlers)

handle_content = SequenceOf(handle_structuralElement)

# One advantage of string element types is their ability to reference forwards,
# allowing code to appear in top-down rather than bottom-up ordering. (???)


def render_code_chunk(chunk: List[str]) -> None:
    """
    A chunk is simply a list of code lines to be
    set as a single paragraph in monospaced font.
    Confusingly we also call them snippets.

    Note it might be wise to consider adopting
    jinja2 early to remove presentation features
    from this code. For now, there's HTML here.

    TODO: save the snippets to assemble an output file.
    """
    sep = "\n"
    chunk = "".join(chunk).strip().splitlines()
    result = f"""\
<pre>
  <code>
{sep.join(chunk)}
  </code>
</pre>
"""
    #
    # Verify snippet begins with a snippet id, extract code & name
    #
    line_gen = iter(chunk)
    line = next(line_gen)
    if not line.startswith(MARKER):
        sys.exit(
            f"No chunk identifier found in snippet:\n{line+sep+sep.join(line_gen)}"
        )
    name = line[len(MARKER) :].strip()
    article, seq = name.rsplit("-", 1)
    seq = int(seq)
    snippets.append(chunk)
    snippet_names.append(article)
    pos = len(snippets)
    if seq != pos:
        sys.exit(
            f"Snippet {seq} appears in position {pos}"
        )  # print(f"{article}, {seq}", file=sys.stderr)
    print(result)


def render_structuralElements(p: OD) -> str:
    """
    Render the textRuns and footnoteReferences from a paragraph.
    """
    c_list = []
    for element in p.elements:
        e_type = element_type(element)
        if e_type == "textRun":
            style = element.textRun.textStyle
            content = element.textRun.content
            if "link" in style:
                content = f"""<a href="{style.link.url}">{content}</a>"""
            style_set = {}
            handle_bold(style, style_set)
            handle_italic(style, style_set)
            handle_font_size(style, style_set)
            handle_font_family(style, style_set)
            if style_set:
                span_style = "; ".join(f"{k}:{v}" for (k, v) in style_set.items())
                content = f"""<span style="{span_style}">{content}</span>"""
            c_list.append(content)
        elif e_type == "footnoteReference":
            fnr = element.footnoteReference
            c_list.append(
                f"""<a href="#footnote-{fnr.footnoteNumber}">[{fnr.footnoteNumber}]</a>"""
            )
            footnote_map[fnr.footnoteNumber] = fnr.footnoteId
    return "".join(c_list)


def handle_font_family(style, style_set):
    """
    TODO: This was originally intended to condition the use of fontAwesome
    fonts, but it would be better to use the native Google fonts from the
    get-go even if this means a radical change to the styles.
    """

    if "weightedFontFamily" in style and style.weightedFontFamily:
        wff = style.weightedFontFamily
        if "weight" in wff and wff.weight:
            style_set["font_weight"] = wff.weight
        if "fontFamily" in wff and wff.fontFamily:
            style_set["font-family"] = wff.fontFamily
            font_map.add(wff.fontFamily)


def handle_font_size(style, style_set):
    if "fontSize" in style:
        style_set["font-size"] = f"{style.fontSize.magnitude}pt"


def handle_italic(style, style_set):
    if "italic" in style and style.italic:
        style_set["font-style"] = "italic"


def handle_bold(style, style_set):
    if "bold" in style and style.bold:
        style_set["font-weight"] = "bold"


def render_normal_text(p: OD) -> str:
    result = f"""\
<p class="normal_text">
{render_structuralElements(p)}
</p>
"""
    return result


def render_heading(h_type, p) -> str:
    # TODO: should insert correct class, or possibly none at all
    result = f"""\
<{h_type} class="normal_text">{render_structuralElements(p)}</{h_type}>"""
    return result


render_heading_1 = partial(render_heading, "h1")
render_heading_2 = partial(render_heading, "h2")
render_heading_3 = partial(render_heading, "h3")

renderer = {
    "NORMAL_TEXT": render_normal_text,
    "HEADING_1": render_heading_1,
    "HEADING_2": render_heading_2,
    "HEADING_3": render_heading_3,
}


def render_paragraphs(paragraph_stream):
    chunk = []
    fragments = []
    for para in paragraph_stream:
        p_type, elements = para_type(para, len(chunk) != 0)
        #
        # Special case: code paragraphs are accumulated
        # into a chunk, which becomes a single paragraph
        # rendered as <pre><code>.
        #
        if p_type == "code":
            chunk.append(elements[0].textRun.content)
        #
        # Other paragraph types are rendered as an appropriate
        # HTML element as set in a lookup table. Rendering can
        # then be performed on the paragraphs' textRun elements.
        #
        else:
            if chunk:  # Emit any accumulated chunk
                fragments.append(render_code_chunk(chunk))
                chunk = []
            # Outside a code chunk ignore blank paras
            if len(elements) == 1 and elements[0].textRun.content == "\n":
                continue
            fragments.append(renderer[p_type](para))  # call handler selected by type
        # Handle edge case where post ends with a code sequence.
    else:
        if chunk:
            fragments.append(render_code_chunk(chunk))
            chunk = []
    return "".join(fragments)


def main(args=sys.argv) -> str:
    """
    Process a Google docs document into a blog entry.
    """
    document_id: str = args[1]
    df = SQLDoc(document_id)
    record = df.load()
    document = OD(json.loads(record.json))
    document = OD(document)
    #
    # Render the document body.
    #
    paragraph_stream = paragraphs_from(document.body.content)
    fragments = [render_paragraphs(paragraph_stream)]
    #
    # Verify that all snippets are tagged for the same article.
    # TODO: skip this whole section if there are no snippets!
    #
    if snippet_names:
        all_names = set(snippet_names)
        if len(all_names) != 1:
            sys.exit(f"Multiple snippet series: {', '.join(all_names)}")
        #
        # Otherwise we have a snippet "series name" for this series of
        # snippets, and in the extracted directory a bunch of files named
        # snippet_series-1.py, snippet_series-2.py and so on.
        # We use the content of each file to replace the corresponding
        # snippet in the src/snippets/snippet_series.py file, producing
        # a src/snippets/snippet_series.py_new file containing the
        # extracted snippets. If this differs from the source file then
        # editing has taken place.
        #
        series_name = snippet_names[0]
        snippet_file_path = os.path.join(
            SNIPPET_PATH, f"{series_name.replace('-', '_')}.py"
        )
        with open(snippet_file_path) as in_file, open(
            snippet_file_path + "_new", "w"
        ) as out_file:
            in_lines = in_file.readlines()
            ranges = snippet_ranges(in_lines)
            pos = 0
            for rng, ((start, end), chunk) in enumerate(zip(ranges, snippets), start=1):
                # Copy the source lines preceding the snippet
                for i in range(pos, start):
                    out_file.write(in_lines[i])
                pos = end
                # Copy out the snippet
                for line in chunk:
                    fragments.append(line)
            for line in in_lines[pos:-1]:
                out_file.write(line)
    #
    # Finally, render the footnotes in such a way that the links
    # from the body text correctly reference the anchors.
    #
    # TODO: Move the HTML into a template and generate
    #       whole section with jinja2
    #
    if footnote_map:
        fragments.append(
            """<h3>Footnotes</h3>
        <ol id="footnotes">
"""
        )
        for number, id in footnote_map.items():

            fragments.append(f"""        <li id="footnote-{number}">""")
            fragments.append(
                render_paragraphs(paragraphs_from(document.footnotes[id].content))
            )
        fragments.append(
            """
            </ol>
"""
        )
    #
    # Let's just try and print it for now!
    #
    return "".join(fragments)


def load(args: List[str] = sys.argv) -> None:
    """
    Divert stdout to a StringIO for generation, then store in SQLite.
    """
    result = main(args)
    document_id: str = args[1]
    df = SQLDoc(document_id)
    doc = OD(df.load())
    df.set_html(result, doc.title)


def browse(args: List[str] = sys.argv) -> None:
    """
    Serve up an already-loaded page in a new browser window.
    """
    document_id: str = args[1]
    webbrowser.open(f"http://localhost:5000/blog/{document_id}")


def showjson(args: List[str] = sys.argv) -> None:
    """
    Output the raw JSON from the document store.
    """
    document_id: str = args[1]
    df = SQLDoc(document_id)
    record = df.load()
    print(record.json)


if __name__ == "__main__":
    print(load())
