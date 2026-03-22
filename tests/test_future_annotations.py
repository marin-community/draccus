# SPDX-License-Identifier: MIT
# Copyright 2025-2026 The Board of Trustees of the Leland Stanford Junior University

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import draccus

# it seems like typing.gettypehints doesn't really work with locals so, we just make these module scope


@dataclass(frozen=True)
class A:
    b: int = 1


@dataclass(frozen=True)
class C:
    a: A = A()
    elems: List[A] = field(default_factory=list)


def test_future_annotations():
    an_a: A = draccus.parse(config_class=A, args="")
    assert an_a.b == 1


def test_nested_future_annotations():
    c: C = draccus.parse(config_class=C, args="")
    assert c.a.b == 1


def test_encode_future_annotations():
    """Encoding a dataclass defined with `from __future__ import annotations` should work."""
    from draccus.parsers.encoding import encode

    a = A(b=42)
    result = encode(a)
    assert result == {"b": 42}


def test_encode_nested_future_annotations():
    """Encoding nested dataclasses with future annotations should work."""
    from draccus.parsers.encoding import encode

    c = C(a=A(b=7), elems=[A(b=1), A(b=2)])
    result = encode(c)
    assert result == {"a": {"b": 7}, "elems": [{"b": 1}, {"b": 2}]}
