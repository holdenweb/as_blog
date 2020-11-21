"""
Process a document into publishable blog format.
"""
import json
import sys

from docs import DocsFile
from hu import ObjectDict


def element_type(se):
    residuals = se.keys() - {"startIndex", "endIndex"}
    assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
        sorted(se.keys())
    )
    return residuals.pop()


def handle_textRun(tr):
    # print(tr.textStyle)
    # print(tr.content, end="")
    pass


def handle_footnoteReference(fnr):
    print(
        f"""<a href=#footnote-{fnr.footnoteNumber}">[{fnr.footnoteNumber}]</a>""",
        end="",
    )
    pass


def handle_paragraph(p):
    """
    A paragraph is a sequence of paragraphElements.
    """
    # print(p.paragraphStyle, len(p.elements))
    for pe in p.elements:
        handle_paragraphElement(pe)


class AnyOf:
    """
    Proxy the appropriate instance handler for
    one of the established sub-elements.
    """

    def __init__(self, elements):
        self.sub_elements = elements

    def __call__(self, element):
        et = element_type(element)
        if et in self.sub_elements:
            self.sub_elements[et](element[et])
        # At present we do nothing about unhandled sub-elements.


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
        self.handler = handler

    def __call__(self, element):
        for sub_element in element:
            self.handler(sub_element)


se_handlers = {"paragraph": handle_paragraph}
handle_structuralElement = AnyOf(se_handlers)

handle_content = SequenceOf(handle_structuralElement)

pe_handlers = {"textRun": handle_textRun, "footnoteReference": handle_footnoteReference}

# One advantage of string element types is their ability to reference forwards,
# allowing code to appear in top-down rather than bottom-up ordering.

handle_paragraphElement = AnyOf(pe_handlers)


def paras(document):
    for element in document.body.content:
        if element_type(element) == "paragraph":
            yield element.paragraph


def is_code(para, in_chunk):
    if len(para.elements) == 1:
        text_run = para.elements[0].textRun
        style = text_run.textStyle
        if (
            "weightedFontFamily" in style
            and style.weightedFontFamily.fontFamily == "Consolas"
        ) or (in_chunk and text_run.content == "\n"):
            return True
    return False


def para_type(para, in_chunk):
    if is_code(para, in_chunk):
        return "code", para.elements
    return para.paragraphStyle.namedStyleType, para.elements


def render_code_chunk(chunk):
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
{sep.join(chunk)}
  </code>
</pre>
"""
    print(result)


def render_textRuns(p):
    """
    Render the textRuns from a paragraph.
    """
    c_list = []
    for element in p.elements:
        if element_type(element) == "textRun":
            style = element.textRun.textStyle
            content = element.textRun.content
            if "bold" in style and style.bold:
                content = f"<b>{content}</b>"
            if "italic" in style and style.italic:
                content = f"<i>{content}</i>"
            c_list.append(content)
    return "".join(c_list)


def render_normal_text(p):
    result = f"""\
<p class="normal_text">
{render_textRuns(p)}
</p>
"""
    print(result)


def render_heading_2(p):
    result = f"""\
<h2 class="normal_text">{render_textRuns(p)}</h2>"""
    print(result)


renderer = {"NORMAL_TEXT": render_normal_text, "HEADING_2": render_heading_2}


def main(document_id: str):
    """
    Process a Google docs document into a blog entry.
    """
    df = DocsFile(document_id).open()
    document = json.loads(df.read())
    document = ObjectDict(document)
    # named_styles = {x.namedStyleType: x for x in document.namedStyles.styles}
    # print(f"{len(named_styles)} named styles: {', '.join(sorted(named_styles.keys()))}")
    handle_content(document.body.content)
    # print("Done")
    # content = document.body.content
    paragraph_stream = paras(document)
    chunk = []
    for para in paragraph_stream:
        p_type, elements = para_type(para, len(chunk) != 0)
        #
        # Special case: code paragraphs are accumulated
        # into a chunk, which becomes a single paragraph.
        #
        if p_type == "code":
            chunk.append(para.elements[0].textRun.content)
        #
        # Other paragraph types are rendered as an appropriate
        # HTML element as set in a lookup table. Rendering can
        # then be performed on the paragraphs' textRun elements.
        #
        else:
            if chunk:
                render_code_chunk(chunk)
                chunk = []
            renderer[p_type](para)  # call handler selected by type
        # Handle edge case where post ends with a code sequence.
    else:
        if chunk:
            render_code_chunk(chunk)
            chunk = []

    # for chunk in chunks(document):
    # print("=== CODE CHUNK ===")
    # for para in chunk:
    # print(para_type(para)[0])


if __name__ == "__main__":
    main(sys.argv[1])
