"""
Test style-handling code.
"""
from styles import StyleStack, style_types

import pytest

def test_push_and_pop():
    """
    Verify that permissible keys are all present, and
    that nested namespaces override the base values.
    """
    ss = StyleStack()
    for s in style_types['paragraph']:
        assert ss[s] is None
    assert ss['borderTop'] is None
    ss.push({'borderTop': "hooray!"})
    assert ss['borderTop'] == 'hooray!'
    ss.pop() == {'borderTop': "hooray!"}
    assert ss['borderTop'] is None

def test_invalid_key():
    """
    Verify non-existent keys raise an exception.
    """
    with pytest.raises(KeyError):
        ss = StyleStack()
        _ = ss["NoSuchKey"]

def test_limited_keys():
    """
    Verify that unacceptable keys raise an exception.
    """
    ss = StyleStack()
    with pytest.raises(ValueError) as exc_info:
        ss['ImpermissibleKey'] = "anything"
    msg = exc_info.value.args[0]
    assert "Impermissible" in msg
    assert "ImpermissibleKey" in msg

def test_flattening():
    """
    Verify we can create an equivalent dictionary.
    """
    ss = StyleStack()
    ss.push({'borderTop': "One Banana"})
    ss.push({'borderBottom': "Two Bananas"})
    ss.push({'borderLeft': "Three Bananas"})
    ss.push({'borderRight': "Four Bananas"})
    d = {k: None for k in style_types['paragraph']}
    d.update({
        'borderTop': "One Banana",
        'borderBottom': "Two Bananas",
        'borderLeft': "Three Bananas",
        'borderRight': "Four Bananas"
    })
    assert d == ss.to_dict()
