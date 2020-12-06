"""
Process a document into publishable blog format.
"""
import json
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


footnote_map = {}
font_map = set()


def handle_textRun(tr: OD) -> None:
    pass


def handle_footnoteReference(fnr: OD) -> None:
    """
    Besides rendering a link to the footnote in the body of the output,
    we must also remember the footnoteId against the footnoteNumber, in
    order to be able to produce the actual footnote contents once the
    whole document body has been parsed.

    A simple implementation has been chosen initially, which ignores
    the textStyle in the reference. It uses a global footnote_map table
    to store these references.
    """
    print(
        f"""<a href=#footnote-{fnr.footnoteNumber}">[{fnr.footnoteNumber}]</a>""",
        end="",
    )
    footnote_map[fnr.footnoteNumber] = fnr.footnoteId


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

pe_handlers = {"textRun": handle_textRun, "footnoteReference": handle_footnoteReference}

# One advantage of string element types is their ability to reference forwards,
# allowing code to appear in top-down rather than bottom-up ordering.

handle_paragraphElement = AnyOf(pe_handlers)


def render_code_chunk(chunk: List[str]) -> None:
    """
    A chunk is simply a list of code lines to be
    set as a single paragraph in monospaced font.

    Note it might be wise to consider adopting
    jinja2 early to remove presentation features
    from this code. For now, there's HTML here.
    """
    sep = ""
    result = f"""\
<pre>
  <code>
{sep.join(chunk).strip()}
  </code>
</pre>
"""
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


def render_normal_text(p: OD) -> None:
    result = f"""\
<p class="normal_text">
{render_structuralElements(p)}
</p>
"""
    print(result)


def render_heading(h_type, p):
    # TODO: should insert correct class, or possibly none at all
    result = f"""\
<{h_type} class="normal_text">{render_structuralElements(p)}</{h_type}>"""
    print(result)


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
                render_code_chunk(chunk)
                chunk = []
            # Outside a code chunk ignore blank paras
            if len(elements) == 1 and elements[0].textRun.content == "\n":
                continue
            renderer[p_type](para)  # call handler selected by type
        # Handle edge case where post ends with a code sequence.
    else:
        if chunk:
            render_code_chunk(chunk)
            chunk = []


def main(args=sys.argv) -> None:
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
    render_paragraphs(paragraph_stream)
    #
    # Finally, render the footnotes in such a way that the links
    # from the body text correctly reference the anchors.
    #
    # TODO: Move the HTML into a template and generate
    #       whole section with jinja2
    #
    if footnote_map:
        print(
            """<h3>Footnotes</h3>
        <ol id="footnotes">
"""
        )
        for number, id in footnote_map.items():

            print(f"""        <li id="footnote-{number}">""")
            render_paragraphs(paragraphs_from(document.footnotes[id].content))
        print(
            """
            </ol>
"""
        )


def load(args: List[str] = sys.argv) -> None:
    """
    Divert stdout to a StringIO for generation, then store in SQLite.
    """
    save_stdout = sys.stdout
    sys.stdout = s = StringIO()
    main(args)
    result = s.getvalue()
    sys.stdout = save_stdout
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
    load()
