# SPDX-License-Identifier: MIT
# Copyright 2025-2026 The Board of Trustees of the Leland Stanford Junior University

import argparse
import dataclasses
import sys

import pytest

from draccus import ParsingError

from .draccus_choice_plugins.model_config import MlpConfig, ModelConfig
from .testutils import TestSetup


def test_plugin_registry_argparse():
    @dataclasses.dataclass(frozen=True)
    class Something(TestSetup):
        model: ModelConfig = MlpConfig(10, 5)

    s = Something.setup("")
    assert s.model == MlpConfig(10, 5)

    s = Something.setup("--model.type mlp --model.layers 12 --model.hidden_size 6")
    assert s.model == MlpConfig(12, 6)

    s = Something.setup("--model.layers 12 --model.hidden_size 6")
    assert s.model == MlpConfig(12, 6)

    s = Something.setup("--model.type gpt --model.layers 12 --model.attn_pdrop 0.2")
    from .draccus_choice_plugins.gpt import GptConfig

    assert s.model == GptConfig(12, 0.2)

    with pytest.raises(argparse.ArgumentError):
        Something.setup("--model.type baby")

    with pytest.raises(ParsingError):
        Something.setup("--model.type gpt --model.layers 12 --model.hidden_size 6")

    with pytest.raises(ParsingError):
        Something.setup("--model.attn_pdrop 12")


# skip this test if using python 3.8
# the help text is a bit different in 3.8


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.9 or higher")
def test_choice_registry_examine_help(snapshot):
    @dataclasses.dataclass
    class Something(TestSetup):
        model: ModelConfig = MlpConfig(10, 5)

    assert Something.get_help_text() == snapshot
