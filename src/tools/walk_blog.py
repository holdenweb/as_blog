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
        residuals = set(se.keys()) - {"startIndex", "endIndex"}
        assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
            sorted(se.keys())
        )
        return list(residuals)[0]

    def handle_textRun(tr):
        print(tr.content)

    def handle_footnoteReference(fnr):
        print(f"[{fnr.footnoteNumber}]", end="")

    pe_handlers = {
        "textRun": handle_textRun,
        "footnoteReference": handle_footnoteReference,
    }

    def handle_paragraph(p):
        """
        A paragraph is a sequence of paragraphElements.
        """
        for pe in p.elements:
            handle_paragraphElement(pe)

    se_handlers = {"paragraph": handle_paragraph}

    def handle_structuralElement(e):
        et = element_type(e)
        handler = se_handlers.get(et)
        if handler:
            handler(e[et])

    def handles(handlers):
        def decorator(f):
            def handle_element(element):
                et = element_type(element)
                handler = handlers.get(et)
                if handler:
                    handler(element[et])

            return handle_element

        return decorator

    @handles(pe_handlers)
    def handle_paragraphElement(element):
        pass

    df = DocsFile(document_id).open()
    document = json.loads(df.read())
    document = ObjectDict(document)
    named_styles = {x.namedStyleType: x for x in document.namedStyles.styles}
    for se in document.body.content:
        handle_structuralElement(se)


if __name__ == "__main__":
    main(sys.argv[1])
