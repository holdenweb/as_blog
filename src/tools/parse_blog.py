import json
import sys

from docs import DocsFile
from hu import ObjectDict
from styles import StyleStack

#
# Next steps: add paragraphStyle handler to action formatting
# changes, and paragraphElement.footnoteReference handler to
# ensure that the footnotes are included.
#


DEBUG_FEATURE_FLAGS = {"parse", "upn"}


def debug(debug_class, *arg, **kw):
    if any(flag in DEBUG_FEATURE_FLAGS for flag in (debug_class, "all")):
        print(*arg, **kw)


class MyDoc:
    """
    This is a general framework to handle Google documents, allowing their
    processing into blog entries in a relatively automated way.
    """

    def __init__(self):
        self.content = []
        self.p_styles = StyleStack("paragraph")
        self.t_styles = StyleStack("text")

    def parse(self, element, element_name, item_names, ancestors):
        """
        Parses the given document element by recursively parsing
        the content of each item.
        """
        debug("parse", f"Parsing {'.'.join(ancestors + [element_name])}")
        for item_name in item_names:
            if item_name in element:
                method = getattr(
                    self, f"parse_{item_name}", self.parse_unrecognised_part_name
                )
                item = element[item_name]
                debug(
                    "parse", "Handling", ".".join(ancestors + [element_name, item_name])
                )
                method(
                    element=item,
                    element_name=item_name,
                    ancestors=ancestors + [element_name],
                )
        debug("parse", f"Parse of {'.'.join(ancestors + [element_name])} complete")

    def parse_body(self, element, element_name, ancestors):
        item_names = ("content",)
        return self.parse(
            element, element_name="content", item_names=item_names, ancestors=ancestors
        )

    def parse_content(self, element, element_name, ancestors):
        """
        elements is a sequence of structuralElement objects, some of which should
        be parsed to access publishable content.
        """
        debug("content", "Content elements count:", len(element))
        for item in element:
            self.parse_structuralElement(item, "structuralElement", ancestors=ancestors)

    def parse_document(self, element, ancestors=[]):
        item_names = (
            "title",
            "body",
            "footnotes",
            "documentStyle",
            "namedStyles",
            "revisionId",
            "suggestionsViewMode",
            "documentId",
        )
        return self.parse(
            element=element,
            element_name="document",
            item_names=item_names,
            ancestors=ancestors,
        )

    def parse_documentId(self, element, element_name, ancestors):
        self.documentId = element

    def parse_documentStyle(self, element, element_name, ancestors):
        item_names = (
            "background",
            "defaultHeaderId",
            "defaultFooterId",
            "evenPageHeaderId",
            "evenPageFooterId",
            "firstPageHeaderId",
            "firstPageFooterId",
            "useFirstPageHeaderFooter",
            "useEvenPageHeaderFooter",
            "pageNumberStart",
            "marginTop",
            "marginBottom",
            "marginRight",
            "marginLeft",
            "pageSize",
            "marginHeader",
            "marginFooter",
            "useCustomHeaderFooterMargins",
        )
        self.parse(element, element_name, item_names, ancestors)

    def parse_elements(self, element, element_name, ancestors):
        for item in element:
            self.parse_element(item, "paragraphElement", ancestors)

    def parse_element(self, element, element_name, ancestors):
        item_names = (
            "textRun",
            "autoText",
            "pageBreak",
            "columnBreak",
            "footnoteReference",
            "horizontalRule",
            "equation",
            "inlineOPbnjectElement",
        )
        debug("element", f"Range: {element['startIndex']}-{element['endIndex']}")
        self.parse(element, element_name, item_names, ancestors)

    def parse_paragraph(self, element, element_name, ancestors):
        item_names = ("paragraphStyle", "bullet", "elements")
        return self.parse(element, element_name, item_names, ancestors)

    def parse_paragraphStyle(self, element, element_name, ancestors):
        """
        Attempts to establish a paragraph style.

        Unfortunately the style's lifetime should be the
        lifetime of its containing paragraph, so a simple
        push and pop are inappropriate.

        Since the style is always processed before the content,
        it's appropriate to set the style here, but it cannot
        be popped until the end of the paragraph.

        Of course if the paragraphStyle element is optional,
        there will also need to be some mechanism that guards
        the style pop option so it only occurs when the push
        has been performed. Through a glass darkly I can see
        the shape of an abstract syntax tree.
        """
        self.p_styles.push(element)
        debug("ps", f"Pushed {element_name} {element!r}")
        debug("ps", "pStyle now:")
        for key, value in sorted(self.p_styles.to_dict().items()):
            if value:
                debug("ps", f":::{key!r}: {value!r}")
        assert self.p_styles.pop() == element

    def parse_sectionBreak(self, element, element_name, ancestors):
        debug("sb", "sectionBreak:", element)

    def parse_structuralElement(self, element, element_name, ancestors):
        part_names = ("sectionBreak", "tableOfContents", "table", "paragraph")
        return self.parse(
            element,
            element_name="structuralElement",
            item_names=part_names,
            ancestors=ancestors,
        )

    def parse_textRun(self, element, element_name, ancestors):
        style = element.get("textStyle", "")
        self.content.append((style, element["content"]))
        debug("tr", "tStyle:", style if style else "UNSTYLED CONTENT")
        debug("tr", "<|", element["content"], end="|>")

    def parse_textStyle(self, element, element_name, ancestors):
        self.t_styles.push(element)
        debug("ts", f"Pushed {element_name} {element!r}")
        debug("ts", "tStyle now:")
        for key, value in sorted(self.p_styles.to_dict().items()):
            if value:
                debug("ts", f"...{key!r}: {value!r}")
        assert self.t_styles.pop() == element

    def parse_title(self, element, element_name, ancestors):
        self.title = element
        debug("t", ".".join(ancestors + [element_name]), "is", element)

    def parse_unrecognised_part_name(self, element, element_name, ancestors):
        debug("upn", "Didn't handle", ".".join(ancestors + [element_name]))


def main(document_id: str):
    """

    """
    df = DocsFile(document_id).open()
    document = json.loads(df.read())
    document = ObjectDict(document)
    parser = MyDoc()
    parser.parse_document(element=document, ancestors=[])

    debug("main", f'The title of the document is: {document.get("title")!r}')
    debug("main", f"  The parser says: {parser.title}")
    debug("main", f"                   {parser.documentId}")

    current_style = None
    ci = iter(parser.content)
    for style, para in ci:
        if style != current_style:
            current_style = style
            debug("final", f"\n:::::::: Style: {style} ::::::::")
        debug("final", para, sep="", end="")


if __name__ == "__main__":
    main(sys.argv[1])
