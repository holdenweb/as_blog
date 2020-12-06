"""
doc_utils.py: Useful utilities for working with Google Docs.
"""
from typing import Generator
from typing import List
from typing import Tuple

from hu import ObjectDict as OD


def para_type(para: OD, in_chunk: bool) -> Tuple[str, List[OD]]:
    if is_code(para, in_chunk):
        return "code", para.elements
    return para.paragraphStyle.namedStyleType, para.elements


def is_code(para: OD, in_chunk: bool) -> bool:
    if len(para.elements) == 1:
        text_run = para.elements[0].textRun
        style = text_run.textStyle
        if (
            "weightedFontFamily" in style
            and style.weightedFontFamily.fontFamily == "Consolas"
        ) or (in_chunk and text_run.content == "\n"):
            return True
    return False


def paragraphs_from(content: List[OD]) -> Generator[OD, None, None]:
    for element in content:
        if element_type(element) == "paragraph":
            yield element.paragraph


def element_type(se: OD) -> str:
    residuals = se.keys() - {"startIndex", "endIndex"}
    assert len(residuals) == 1, "Unexpected key in structuralElement :{!r}".format(
        sorted(se.keys())
    )
    return residuals.pop()
