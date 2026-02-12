# SPDX-License-Identifier: MIT
# Copyright 2025-2026 The Board of Trustees of the Leland Stanford Junior University

import dataclasses

import pytest

import draccus
from draccus import ParsingError
from draccus.choice_types import ChoiceRegistry, QNamePluginRegistry
from draccus.utils import DecodingError


@dataclasses.dataclass
class Person(ChoiceRegistry):
    name: str  # Person's name


@dataclasses.dataclass
class Adult(Person):
    age: int


@dataclasses.dataclass
class Child(Person):
    favorite_toy: str


Person.register_subclass("adult", Adult)
Person.register_subclass("child", Child)


def test_choice_registry_decode():
    assert draccus.decode(Person, {"type": "adult", "name": "bob", "age": 10}) == Adult("bob", 10)
    assert draccus.decode(Person, {"type": "child", "name": "bob", "favorite_toy": "truck"}) == Child("bob", "truck")

    with pytest.raises(ParsingError):
        draccus.decode(Person, {"type": "baby", "name": "bob"})

    with pytest.raises(DecodingError):
        draccus.decode(Person, {"type": "adult", "name": "bob", "age": 10, "favorite_toy": "truck"})

    with pytest.raises(DecodingError):
        draccus.decode(Person, {"type": "adult", "name": 3})


def test_registry_decode_subtype_without_type():
    draccus.decode(Child, {"name": "bob", "favorite_toy": "truck"})

    with pytest.raises(DecodingError):
        draccus.decode(Child, {"type": "adult", "name": "bob", "age": 10})


def test_choice_registry_encode():
    assert draccus.encode(Adult("bob", 10), Person) == {"type": "adult", "name": "bob", "age": 10}
    assert draccus.encode(Child("bob", "truck"), Person) == {"type": "child", "name": "bob", "favorite_toy": "truck"}


def test_is_choicetype():
    assert draccus.utils.is_choice_type(Person)
    assert not draccus.utils.is_choice_type(Adult)
    assert not draccus.utils.is_choice_type(Child)


@dataclasses.dataclass
class QNameModelConfig(QNamePluginRegistry, discover_packages_path="tests.draccus_choice_plugins"):
    layers: int


@dataclasses.dataclass
class UnregisteredQNameModelConfig(QNameModelConfig):
    width: int


def test_qname_plugin_registry_decode_fallback():
    qname = f"{UnregisteredQNameModelConfig.__module__}.{UnregisteredQNameModelConfig.__qualname__}"

    decoded = draccus.decode(QNameModelConfig, {"type": qname, "layers": 2, "width": 8})

    assert decoded == UnregisteredQNameModelConfig(layers=2, width=8)
    assert QNameModelConfig.get_choice_class(qname) is UnregisteredQNameModelConfig


def test_qname_plugin_registry_encode_fallback():
    encoded = draccus.encode(UnregisteredQNameModelConfig(layers=3, width=16), QNameModelConfig)

    assert encoded == {
        "type": f"{UnregisteredQNameModelConfig.__module__}.{UnregisteredQNameModelConfig.__qualname__}",
        "layers": 3,
        "width": 16,
    }


def test_qname_plugin_registry_rejects_non_subclass_name_lookup():
    with pytest.raises(ValueError):
        QNameModelConfig.get_choice_name(Adult)


def test_qname_plugin_registry_does_not_swallow_import_errors(monkeypatch):
    monkeypatch.setattr(QNameModelConfig, "_did_discover_packages", True)
    failing_module = "tests.draccus_choice_plugins.import_fails"

    def fake_import_module(name: str, package=None):
        if name == failing_module:
            raise ModuleNotFoundError("boom", name="missing_dependency")
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr("draccus.choice_types.importlib.import_module", fake_import_module)

    with pytest.raises(ModuleNotFoundError, match="boom"):
        QNameModelConfig.get_choice_class(f"{failing_module}.BrokenConfig")


class NestedQNameModels:
    @dataclasses.dataclass
    class UnregisteredNestedQNameModelConfig(QNameModelConfig):
        depth: int


def test_qname_plugin_registry_nested_qualname_decode_fallback():
    nested_qname = (
        f"{NestedQNameModels.UnregisteredNestedQNameModelConfig.__module__}."
        f"{NestedQNameModels.UnregisteredNestedQNameModelConfig.__qualname__}"
    )

    decoded = draccus.decode(QNameModelConfig, {"type": nested_qname, "layers": 4, "depth": 2})

    assert decoded == NestedQNameModels.UnregisteredNestedQNameModelConfig(layers=4, depth=2)


def test_qname_plugin_registry_nested_qualname_encode_fallback():
    encoded = draccus.encode(
        NestedQNameModels.UnregisteredNestedQNameModelConfig(layers=5, depth=3),
        QNameModelConfig,
    )

    assert encoded == {
        "type": (
            f"{NestedQNameModels.UnregisteredNestedQNameModelConfig.__module__}."
            f"{NestedQNameModels.UnregisteredNestedQNameModelConfig.__qualname__}"
        ),
        "layers": 5,
        "depth": 3,
    }
