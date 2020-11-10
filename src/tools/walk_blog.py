"""
Process a document into publishable blog format.
"""
import json
import sys

from docs import DocsFile
from hu import ObjectDict
from styles import StyleStack

DEBUG_FEATURE_FLAGS = {"se"}


def debug(debug_class, *arg, **kw):
    if any(flag in DEBUG_FEATURE_FLAGS for flag in (debug_class, "all")):
        print(*arg, **kw)


class DocParser:
    """
    This is a general framework to handle Google documents, allowing their
    processing into blog entries in a relatively automated way.
    """

    def __init__(self):
        self.content = []
        self.p_styles = StyleStack("paragraph")
        self.t_styles = StyleStack("text")


def element_type(se):
    residuals = se.keys() - {"startIndex", "endIndex"}
    assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
        sorted(se.keys())
    )
    return residuals.pop()


def handle_textRun(tr):
    print(tr.content, end="")


def handle_footnoteReference(fnr):
    print(f"[{fnr.footnoteNumber}]", end="")


def handle_paragraph(p):
    """
    A paragraph is a sequence of paragraphElements.
    """
    for pe in p.elements:
        handle_paragraphElement(pe)


class HandleAnyOf:
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


class HandleEachOf(HandleAnyOf):
    """
    Process an established sequence of sub-elements.
    """

    def __call__(self, element):
        for element_name, handler in self.sub_elements.items():
            handler(element[element_name])


class HandleSequenceOf:
    """
    Handle a list of a given element type.
    """

    def __init__(self, handler):
        self.handler = handler

    def __call__(self, element):
        for sub_element in element:
            self.handler(sub_element)


se_handlers = {"paragraph": handle_paragraph}
handle_structuralElement = HandleAnyOf(se_handlers)

handle_content = HandleSequenceOf(handle_structuralElement)

body_handlers = {"content": handle_content}
handle_body = HandleEachOf(body_handlers)

pe_handlers = {"textRun": handle_textRun, "footnoteReference": handle_footnoteReference}

doc_handlers = {
    # "documentStyle",
    # "lists",
    # "namedStyles",
    # "namedRanges",
    # "inlineObjects",
    # "headers",
    # "footers",
    # "footnotes,"
    "body": handle_body
}

handle_document = HandleEachOf(doc_handlers)
handle_paragraphElement = HandleAnyOf(pe_handlers)


def main(document_id: str):
    """
    Process a Google docs document into a blog entry.
    """
    df = DocsFile(document_id).open()
    document = json.loads(df.read())
    document = ObjectDict(document)
    # named_styles = {x.namedStyleType: x for x in document.namedStyles.styles}
    # for se in document.body.content:
    # handle_structuralElement(se)
    handle_document(document)


if __name__ == "__main__":
    main(sys.argv[1])
