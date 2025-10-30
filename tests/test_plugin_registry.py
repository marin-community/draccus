# SPDX-License-Identifier: MIT
# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University

# SPDX-License-Identifier: MIT

import draccus


def test_plugin_registry_decode_fully_qualified_name():
    from tests.draccus_choice_plugins.gpt import GptConfig
    from tests.draccus_choice_plugins.model_config import ModelConfig

    config = draccus.decode(
        ModelConfig,
        {
            "type": "tests.draccus_choice_plugins.gpt.GptConfig",
            "layers": 12,
            "attn_pdrop": 0.2,
        },
    )

    assert config == GptConfig(12, 0.2)
