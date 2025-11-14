from __future__ import annotations

from typing import List, Optional

from xml.etree import ElementTree as ET

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

LATEX_ESCAPES = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


class OmmlConversionError(ValueError):
    """Raised when we cannot derive MathML/LaTeX from the provided OMML."""


def convert_omml_to_latex(omml_xml: str) -> str:
    """
    Convert an OMML (Office Math Markup Language) snippet into LaTeX.
    """
    omml_xml = (omml_xml or "").strip()
    if not omml_xml:
        raise OmmlConversionError("Empty OMML input.")

    elements = _extract_math_elements(omml_xml)
    if not elements:
        raise OmmlConversionError("No OMML math elements were found in the payload.")

    latex_chunks: List[str] = []
    for element in elements:
        latex_chunks.append(_convert_node(element))

    formula = " ".join(chunk for chunk in latex_chunks if chunk).strip()
    if not formula:
        raise OmmlConversionError("Unable to derive LaTeX from the provided OMML.")

    return f"$$ {formula} $$"


def _extract_math_elements(omml_xml: str) -> List[ET.Element]:
    """
    Parse OMML into an XML tree and return the math-bearing elements (oMath/oMathPara).
    We accept fragments by wrapping them in a dummy root if needed.
    """
    parse_attempts = [omml_xml]
    wrapped = f"<m:wrapper xmlns:m='{MATH_NS}'>{omml_xml}</m:wrapper>"
    parse_attempts.append(wrapped)

    last_error: Optional[Exception] = None
    for xml in parse_attempts:
        try:
            root = ET.fromstring(xml)
            return _gather_math_nodes(root)
        except ET.ParseError as exc:
            last_error = exc

    raise OmmlConversionError(f"Unable to parse OMML XML: {last_error}")  # pragma: no cover


def _gather_math_nodes(root: ET.Element) -> List[ET.Element]:
    name = _local_name(root)
    if name in {"oMath", "oMathPara"}:
        return [root]

    math_nodes: List[ET.Element] = []
    for child in root:
        if _local_name(child) in {"oMath", "oMathPara"}:
            math_nodes.append(child)
        else:
            math_nodes.extend(_gather_math_nodes(child))
    return math_nodes


def _convert_node(node: ET.Element) -> str:
    name = _local_name(node)

    if name == "oMathPara":
        lines = [_convert_node(child) for child in node if _is_math_content(child)]
        return r" \\ ".join(filter(None, lines))
    if name == "oMath":
        return "".join(_convert_node(child) for child in node if _is_math_content(child))
    if name == "r":
        return "".join(_convert_node(child) for child in node)
    if name == "t":
        return _escape_text(node.text or "")
    if name == "f":
        num = _convert_first(node, "num")
        den = _convert_first(node, "den")
        return rf"\frac{{{num}}}{{{den}}}"
    if name in {"sSup", "sSub", "sSubSup"}:
        base = _convert_first(node, "e")
        sup = _convert_first(node, "sup")
        sub = _convert_first(node, "sub")
        if name == "sSup":
            return rf"{base}^{{{sup}}}"
        if name == "sSub":
            return rf"{base}_{{{sub}}}"
        return rf"{base}_{{{sub}}}^{{{sup}}}"
    if name == "rad":
        degree = _convert_first(node, "deg")
        radicand = _convert_first(node, "e")
        if degree:
            return rf"\sqrt[{degree}]{{{radicand}}}"
        return rf"\sqrt{{{radicand}}}"
    if name == "acc":
        chr_node = _convert_first(node, "chr") or r"\hat{}"
        base = _convert_first(node, "e")
        return rf"{chr_node}{{{base}}}"
    if name == "nary":
        symbol = _nary_symbol(node)
        lower = _convert_first(node, "sub")
        upper = _convert_first(node, "sup")
        expr = _convert_first(node, "e")
        limits = ""
        if lower:
            limits += rf"_{{{lower}}}"
        if upper:
            limits += rf"^{{{upper}}}"
        return rf"{symbol}{limits} {expr}"
    if name == "limLow":
        base = _convert_first(node, "e")
        lower = _convert_first(node, "lim")
        return rf"\lim_{{{lower}}}{base}"
    if name == "limUpp":
        base = _convert_first(node, "e")
        upper = _convert_first(node, "lim")
        return rf"\lim^{{{upper}}}{base}"
    if name == "matrix":
        rows = [_convert_matrix_row(row) for row in node if _local_name(row) == "mr"]
        body = r" \\ ".join(rows)
        return rf"\begin{{matrix}}{body}\end{{matrix}}"
    if name == "d":
        opening = _convert_first(node, "begChr") or r"\left("
        closing = _convert_first(node, "endChr") or r"\right)"
        expr = _convert_first(node, "e")
        return rf"\left{opening.strip()} {expr} \right{closing.strip()}"
    if name == "box":
        return "".join(_convert_node(child) for child in node if _is_math_content(child))
    if name in {"begChr", "endChr", "sepChr", "chr"}:
        return _read_value(node)
    if name in {"num", "den", "deg", "e", "sub", "sup", "lim", "mr"}:
        return "".join(_convert_node(child) for child in node if _is_math_content(child))
    if name in {"ctrlPr", "rPr", "mathPr", "argPr", "mPr"}:
        return ""
    if name == "bar":
        base = _convert_first(node, "e")
        return rf"\overline{{{base}}}"
    if name == "phant":
        return ""

    # Fallback: concatenate children so we don't lose content.
    return "".join(_convert_node(child) for child in node)


def _convert_first(node: ET.Element, target_name: str) -> str:
    target = _child(node, target_name)
    if target is None:
        return ""
    return _convert_node(target)


def _child(node: ET.Element, target_name: str) -> Optional[ET.Element]:
    for child in node:
        if _local_name(child) == target_name:
            return child
    return None


def _convert_matrix_row(row: ET.Element) -> str:
    entries = [
        _convert_node(child)
        for child in row
        if _local_name(child) == "e"
    ]
    return " & ".join(entries)


def _is_math_content(node: ET.Element) -> bool:
    return _local_name(node) not in {"ctrlPr", "rPr", "mPr", "argPr", "mathPr"}


def _local_name(node: ET.Element | str) -> str:
    tag = node.tag if isinstance(node, ET.Element) else node
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _escape_text(value: str) -> str:
    return "".join(LATEX_ESCAPES.get(ch, ch) for ch in value)


def _nary_symbol(node: ET.Element) -> str:
    chr_node = _child(node, "chr")
    if chr_node is not None:
        text = _read_value(chr_node)
        mapped = NARY_CHAR_MAP.get(text.strip())
        if mapped:
            return mapped
    return r"\operatorname{}"


NARY_CHAR_MAP = {
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∮": r"\oint",
    "⋂": r"\bigcap",
    "⋃": r"\bigcup",
}


def _read_value(node: ET.Element) -> str:
    attr_key = f"{{{MATH_NS}}}val"
    if attr_key in node.attrib:
        return node.attrib[attr_key]

    parts: List[str] = []
    if node.text:
        parts.append(node.text)
    for child in node:
        if child.text:
            parts.append(child.text)
    return "".join(parts).strip()
