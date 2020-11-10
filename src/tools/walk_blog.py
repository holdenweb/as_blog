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


def main(document_id: str):
    """
    Process a Google docs document into a blog entry.
    """

    def element_type(se):
        residuals = se.keys() - {"startIndex", "endIndex"}
        assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
            sorted(se.keys())
        )
        return residuals.pop()

    def handle_textRun(tr):
        print(tr.content)

    def handle_footnoteReference(fnr):
        print(f"[{fnr.footnoteNumber}]", end="")

    def handle_paragraph(p):
        """
        A paragraph is a sequence of paragraphElements.
        """
        for pe in p.elements:
            handle_paragraphElement(pe)

    class HandlesAnyOf:
        def __init__(self, elements):
            self.elements = elements

        def __call__(self, element):
            et = element_type(element)
            if et in self.elements:
                self.elements[et](element[et])

    pe_handlers = {
        "textRun": handle_textRun,
        "footnoteReference": handle_footnoteReference,
    }

    se_handlers = {"paragraph": handle_paragraph}

    handle_structuralElement = HandlesAnyOf(se_handlers)
    handle_paragraphElement = HandlesAnyOf(pe_handlers)

    df = DocsFile(document_id).open()
    document = json.loads(df.read())
    document = ObjectDict(document)
    # named_styles = {x.namedStyleType: x for x in document.namedStyles.styles}
    for se in document.body.content:
        handle_structuralElement(se)


if __name__ == "__main__":
    main(sys.argv[1])
