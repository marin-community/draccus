# SPDX-License-Identifier: MIT
# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson

from dataclasses import dataclass
from typing import Tuple

import pytest
from pydantic import ValidationError

from draccus import ParsingError
from draccus.utils import DecodingError
from tests.testutils import TestSetup


def test_tuple_with_n_items_takes_only_n_values(snapshot):
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, int] = (1, 5)

    c = Container.setup("")
    assert c.ints == (1, 5)
    c = Container.setup("--ints [4,8]")
    assert c.ints == (4, 8)
    with pytest.raises(ValidationError) as e:
        c = Container.setup("--ints [4,5,6,7,8]")

    assert snapshot == str(e.value)


def test_tuple_elipsis_takes_any_number_of_args():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, ...] = (1, 2, 3)

    c = Container.setup("")
    assert c.ints == (1, 2, 3)
    c = Container.setup("--ints '[4, 5, 6, 7, 8]'")
    assert c.ints == (4, 5, 6, 7, 8)


@pytest.mark.skip("TODO(jder): resolve str-vs-int")
def test_each_type_is_used_correctly():
    @dataclass
    class Container(TestSetup):
        """A container with mixed items in a tuple."""

        mixed: Tuple[int, str, bool, float] = (1, "bob", False, 1.23)

    c = Container.setup("")
    assert c.mixed == (1, "bob", False, 1.23)

    c = Container.setup("--mixed [1,2,false,1]")
    assert c.mixed == (1, "2", False, 1.0)
