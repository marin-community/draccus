# SPDX-License-Identifier: MIT
# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University

import dataclasses
from typing import Optional

from pydantic import ConfigDict

from draccus.choice_types import PluginRegistry


@dataclasses.dataclass(frozen=True)
class ModelConfig(PluginRegistry, discover_packages_path="tests.draccus_choice_plugins"):
    __pydantic_config__ = ConfigDict(extra="forbid")
    layers: int

    @classmethod
    def default_choice_name(cls) -> Optional[str]:
        return "mlp"


@ModelConfig.register_subclass("mlp")
@dataclasses.dataclass(frozen=True)
class MlpConfig(ModelConfig):
    hidden_size: int = 100
