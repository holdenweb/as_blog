"""
Process a document into publishable blog format.
"""
import json
import re
import sys
import unicodedata
from io import StringIO

from docs import SQLDoc
from hu import ObjectDict as OD

footnote_map = {}

_slugify_strip_re = re.compile(r"[^\w\s-]")
_slugify_hyphenate_re = re.compile(r"[-\s]+")


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    if not isinstance(value, str):
        value = str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = str(_slugify_strip_re.sub("", value).strip().lower())
    return _slugify_hyphenate_re.sub("-", value)


def _slugify(string):
    if not string:
        return ""
    return slugify(string)


def element_type(se):
    residuals = se.keys() - {"startIndex", "endIndex"}
    assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
        sorted(se.keys())
    )
    return residuals.pop()


def handle_textRun(tr):
    pass


def handle_footnoteReference(fnr):
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


def paragraphs_from(content):
    for element in content:
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
{sep.join(chunk).strip()}
  </code>
</pre>
"""
    print(result)


def render_structuralElements(p):
    """
    Render the textRuns and footnoteReferences from a paragraph.
    """
    c_list = []
    for element in p.elements:
        e_type = element_type(element)
        if e_type == "textRun":
            style = element.textRun.textStyle
            content = element.textRun.content
            if "bold" in style and style.bold:
                content = f"<b>{content}</b>"
            if "italic" in style and style.italic:
                content = f"<i>{content}</i>"
            if "link" in style:
                content = f"""<a href="{style.link.url}">{content}</a>"""
            c_list.append(content)
        elif e_type == "footnoteReference":
            fnr = element.footnoteReference
            c_list.append(
                f"""<a href="#footnote-{fnr.footnoteNumber}">[{fnr.footnoteNumber}]</a>"""
            )
            footnote_map[fnr.footnoteNumber] = fnr.footnoteId
    return "".join(c_list)


def render_normal_text(p):
    result = f"""\
<p class="normal_text">
{render_structuralElements(p)}
</p>
"""
    print(result)


def render_heading_2(p):
    result = f"""\
<h2 class="normal_text">{render_structuralElements(p)}</h2>"""
    print(result)


renderer = {"NORMAL_TEXT": render_normal_text, "HEADING_2": render_heading_2}


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


def main(args=sys.argv):
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


def load(args=sys.argv):
    save_stdout = sys.stdout
    sys.stdout = StringIO()
    main(args)
    result = sys.stdout.getvalue()
    sys.stdout = save_stdout
    document_id: str = args[1]
    df = SQLDoc(document_id)
    df.set_html(result)


if __name__ == "__main__":
    main()
