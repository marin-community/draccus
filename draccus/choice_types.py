# SPDX-License-Identifier: MIT
# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University

"""
A Choice Type aka "Sum Type" is a type that can be one of several types. Typically this is through subtyping,
but could be a tagged union or something else.

Typically you'll write a config like this:

```yaml
model:
    type: gpt
    pdrop: 0.1
    layers: 3
```

with a class hierarchy that looks like this:

```python
class ModelConfig(ChoiceRegistry):
    pass

@ModelConfig.register_subclass("gpt")
class GPTConfig(ModelConfig):
    pdrop: float
    layers: int
```

For now, Draccus choice types are implemented as classes that conform to a protocol. The protocol defines
a "get_choice_class(name)" method that returns the class corresponding to the given name, along with a few
other methods.

We may add support for Unions.

All registered types must be *dataclasses*
"""

import functools
import importlib
import pkgutil
from typing import Any, Callable, ClassVar, Dict, Optional, Protocol, Type, TypeVar, overload, runtime_checkable

from pydantic import TypeAdapter, model_serializer, model_validator

from draccus.utils import ParsingError

T = TypeVar("T")


CHOICE_TYPE_KEY = "type"
"""name of key to use in configuration to specify the type of a choice type"""


@runtime_checkable
class ChoiceType(Protocol):
    @classmethod
    def get_choice_class(cls, name: str) -> Any: ...

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]: ...

    @classmethod
    def get_choice_name(cls, subcls: Type) -> str:
        """
        Returns the name of the given subclass of this choice type.
        """
        ...

    @classmethod
    def default_choice_name(cls) -> Optional[str]:
        """
        Returns the name of the default subclass of this choice type.
        """
        ...


class ChoiceRegistryBase:
    _choice_registry: ClassVar[Dict[str, Any]]

    @model_validator(mode="wrap")
    @classmethod
    def validate_choice_registry(cls, values, handler) -> Any:
        if isinstance(values, cls):
            return values
        type_name = values.get(CHOICE_TYPE_KEY, None)
        if cls in cls.get_known_choices().values():
            # We are one of the choices already
            if type_name is not None:
                raise ParsingError(f"got choice key '{type_name}' when decoding a {cls} (as opposed to a superclass)")
            return handler(values)
        else:
            if type_name is None:
                type_name = cls.default_choice_name()
            if type_name is None:
                raise ParsingError(
                    f"expected a '{CHOICE_TYPE_KEY}' key with a value of one of {cls.get_known_choices().keys()}"
                )
            try:
                choice_class = cls.get_choice_class(type_name)
            except KeyError:
                raise ParsingError(
                    f"got choice key '{type_name}' but expected one of {cls.get_known_choices().keys()}"
                ) from None

            adapter = TypeAdapter(choice_class)
            return adapter.validate_python({k: v for k, v in values.items() if k != CHOICE_TYPE_KEY})

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        result = handler(self)
        typ = self.__class__.get_choice_name(self.__class__)
        old_typ = result.setdefault(CHOICE_TYPE_KEY, typ)
        assert old_typ == typ, f"Expected {typ} but got {old_typ}"
        return result

    @classmethod
    def get_choice_class(cls, name: str) -> Any:
        return cls._choice_registry[name]

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]:
        return cls._choice_registry

    @classmethod
    def get_choice_name(cls, subcls: Type) -> str:
        for name, choice_type in cls._choice_registry.items():
            if choice_type == subcls:
                return name
        raise ValueError(f"Cannot find choice name for {subcls}")

    @classmethod
    def default_choice_name(cls) -> Optional[str]:
        return None

    @overload
    @classmethod
    def register_subclass(cls, name: str, choice_type: Type) -> Type[T]: ...

    @overload
    @classmethod
    def register_subclass(cls, name: str) -> Callable[[Type[T]], Type[T]]: ...

    @classmethod
    def register_subclass(cls, name: str, choice_type: Optional[Type[T]] = None):
        if choice_type is None:
            return functools.partial(cls.register_subclass, name)

        if name in cls._choice_registry:
            other_choice_type = cls._choice_registry[name]
            if other_choice_type != choice_type:
                raise ValueError(
                    f"Cannot register {choice_type} as {name} because {other_choice_type} is already registered as"
                    f" {name}"
                )

        cls._choice_registry[name] = choice_type
        return choice_type


class ChoiceRegistry(ChoiceRegistryBase):
    _choice_registry: ClassVar[Dict[str, Any]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_choice_registry"):
            cls._choice_registry: ClassVar[Dict[str, Any]] = {}


class PluginRegistry(ChoiceRegistryBase):
    """
    A ChoiceRegistry that allows for discovery of plugins.

    It follows the "namespace package plugin" pattern described here:
    https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-namespace-packages

    To use this, you should put all your plugins in a single package, and then pass the path to that package
    to the constructor of this class. Then, when the class looks for plugins, it will look in that package and
    automatically import them.

    This is useful for things like models, where you want to be able to add new models without having to modify
    the code of the library itself.

    Usage:
    ```python
    @dataclasses.dataclass
    class ModelConfig(PluginRegistry):

        pass

    @dataclasses.dataclass
    class GPTConfig(ModelConfig):
        pass

    ModelConfig.register_subclass("gpt", GPTConfig)

    the syntax for a yaml file would be:
    ```yaml
    model:
      type: gpt
      <config for gpt>
    ```

    Unlike with ClassRegistry, import doesn't happen until you call get_choice_class or get_known_choices,
    and you can split your plugins across multiple files.
    """

    # TODO: is it better to lazily import plugins?
    _choice_registry: ClassVar[Dict[str, Any]]
    discover_packages_path: ClassVar[str]
    _did_discover_packages: ClassVar[bool]

    def __init_subclass__(cls, discover_packages_path: Optional[str] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_choice_registry"):
            cls._choice_registry = {}
        if not hasattr(cls, "discover_packages_path"):
            if discover_packages_path is None:
                raise ValueError("discover_packages_path must be specified in the class or constructor")
            cls.discover_packages_path = discover_packages_path
        cls._did_discover_packages = False

    @classmethod
    def get_choice_class(cls, name: str) -> Any:
        cls._discover_packages()
        return cls._choice_registry[name]

    @classmethod
    def get_known_choices(cls) -> Dict[str, Any]:
        cls._discover_packages()
        return cls._choice_registry

    @classmethod
    def _discover_packages(cls):
        if cls._did_discover_packages:
            return

        # from https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
        package_module = importlib.import_module(cls.discover_packages_path, __package__)

        def iter_namespace(ns_pkg):
            # Specifying the second argument (prefix) to iter_modules makes the
            # returned name an absolute name instead of a relative one. This allows
            # import_module to work without having to do additional modification to
            # the name.
            return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

        for _finder, pkg_name, _ispkg in iter_namespace(package_module):
            importlib.import_module(pkg_name)
            # registration should happen in the initialization of the package, so importing is sufficient

        cls._did_discover_packages = True
