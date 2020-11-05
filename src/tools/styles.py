"""
The style in which text is rendered is maintained in TextStyles
and ParagraphStyles. Each type of style is kept in a stack, and
whenever a new style is encountered another layer is added to
the appropriate style stack. Attribute lookup recurses down the
stack, effectively emulating
"""

style_types = {
    'paragraph': {
        'headingId': None,
        'namedStyleType': None,
        'alignment': None,
        'lineSpacing': None,
        'direction': None,
        'spacingMode': None,
        'spaceAbove': None,
        'spaceBelow': None,
        'borderBetween': None,
        'borderTop': None,
        'borderBottom': None,
        'borderLeft': None,
        'borderRight': None,
        'indentFirstLine': None,
        'indentStart': None,
        'indentEnd': None,
        'tabStops': None,
        'keepLinesTogether': None,
        'keepWithNext': None,
        'avoidWidowAndOrphan': None,
        'shading': None,
    },
    'text': {
        'bold': None,
        'italic': None,
        'underline': None,
        'strikethrough': None,
        'smallCaps': None,
        'backgroundColor': None,
        'foregroundColor': None,
        'weightedFontFamily': None,
        'baselineOffset': None,
        'link': None,
    },
}


class StyleStack:
    def __init__(self, style_type='paragraph', level=-1):
        self.style_types = style_types[style_type].copy()
        self.stack = [self.style_types]

    def push(self, style=None):
        if style is None:
            style = {}
        self.stack.append(style)

    def pop(self):
        return self.stack.pop()

    def __getitem__(self, key):
        for s in self.stack[::-1]:
            if key in s:
                return s[key]
        else:
            raise KeyError(f"Key {key!r} not found")

    def __setitem__(self, key, value):
        if key not in self.style_types:
            raise ValueError(f"Impermissible key {key!r}")
        self.stack[-1][key] = value

    def to_dict(self):
        """
        Flatten the stack, returning an equivalent dict.
        """
        result = {}
        for stack in self.stack[::-1]:
            for k, v in stack.items():
                if k not in result:
                    result[k] = v
        return result
