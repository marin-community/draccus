# SPDX-License-Identifier: MIT
# Copyright 2025-2026 The Board of Trustees of the Leland Stanford Junior University
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Union

import pytest

from draccus import utils
from draccus.utils import DecodingError

from .testutils import *


def test_union_type():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, str] = 0

    Foo.get_help_text()

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39():
    assert utils.is_union(float | str)

    @dataclass
    class Foo(TestSetup):
        x: float | str = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39_optional():
    @dataclass
    class Foo(TestSetup):
        x: Optional[float | str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"

    foo = Foo.setup("--x null")
    assert foo.x is None


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39_optional_nested():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, int | str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


def test_union_error_message_atomics(snapshot):
    @dataclass
    class Foo(TestSetup):
        x: Union[float, bool] = 0

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x 1.2.3")

    assert snapshot == str(e.value)


def test_union_error_message_nested(snapshot):
    @dataclass
    class Foo(TestSetup):
        x: Union[float, Union[int, bool]] = 0

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x 1.2.3")

    assert snapshot == str(e.value)


@dataclass(frozen=True)
class Baz_u:
    z: int


@dataclass
class Foo_u(TestSetup):
    x: Union[bool, Baz_u]


def test_decode_union_with_dataclass_and_atomic():
    foo = Foo_u.setup("--x false")
    assert foo.x is False

    foo = Foo_u.setup("--x.z 1")
    assert foo.x == Baz_u(z=1)

    try:
        foo = Foo_u.setup("--x.z 1.2")
        raise AssertionError()
    except DecodingError:
        pass


@dataclass(frozen=True)
class Baz_e:
    z: int
    y: str


@dataclass(frozen=True)
class Bar_e:
    z: bool


@dataclass
class Foo_e(TestSetup):
    x: Union[Baz_e, Bar_e] = Bar_e(False)


def test_union_error_message_dataclasses(snapshot):
    with pytest.raises(DecodingError) as e:
        Foo_e.setup("--x.z 1.2.3")

    assert snapshot(name="wrong-type") == str(e.value)

    with pytest.raises(DecodingError) as e:
        Foo_e.setup("--x.y foo")

    assert snapshot(name="missing") == str(e.value)


@dataclass
class Bar:
    y: int


@dataclass
class Foo(TestSetup):
    x: Optional[Union[Bar, Dict[str, Bar]]] = field(default=None)


def test_union_argparse_dict():
    foo = Foo.setup('--x \'{"a": {"y": 1}, "b": {"y": 2}}\'')
    assert foo.x == {"a": Bar(y=1), "b": Bar(y=2)}


def test_union_field_builds_parser_and_parses():
    """Union-typed fields must survive parser construction.

    Python 3.14 validates that argparse's ``type`` is callable inside
    ``add_argument``, and union objects are not callable there, so building the
    parser used to raise ``TypeError`` before a single argument was parsed.
    """

    @dataclass
    class Foo(TestSetup):
        path: Optional[str] = None
        mapping: Optional[Dict[str, int]] = None
        n: int = 0

    assert Foo.setup("") == Foo()
    assert Foo.setup("--path foo") == Foo(path="foo")
    assert Foo.setup("--n 5") == Foo(n=5)


def test_display_type_wraps_non_callable():
    from draccus.wrappers.field_wrapper import _display_type

    class NotCallable:
        def __repr__(self):
            return "typing.Optional[str]"

    declared = NotCallable()
    assert not callable(declared)

    wrapped = _display_type(declared)
    assert callable(wrapped)
    assert wrapped("abc") == "abc"
    assert wrapped.__name__ == "Optional[str]"
    assert wrapped.__draccus_type__ is declared


def test_union_field_help_with_value_exits_cleanly():
    @dataclass
    class Foo(TestSetup):
        path: Optional[str] = None

    with pytest.raises(SystemExit) as exc:
        Foo.setup("--path foo --help")
    assert exc.value.code == 0


def test_union_field_metavar_preserves_declared_type():
    from draccus.wrappers.field_metavar import get_metavar
    from draccus.wrappers.field_wrapper import _display_type

    wrapped = _display_type(Optional[str])
    assert get_metavar(wrapped) == "[str]"

    wrapped = _display_type(Optional[Dict[str, int]])
    assert get_metavar(wrapped) == "[dict[str,int]]"


def test_union_field_help_text():
    @dataclass
    class Foo(TestSetup):
        path: Optional[str] = None
        mapping: Optional[Dict[str, int]] = None

    help_text = Foo.get_help_text()
    assert "--path [str]" in help_text
    assert "--mapping [dict[str,int]]" in help_text
