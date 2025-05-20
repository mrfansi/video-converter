"""Base parameter object classes for the Video Converter project.

This module provides base classes for parameter objects used throughout the project.
Parameter objects help reduce function parameter complexity and improve code readability.
"""

from typing import Any, Dict, TypeVar, Generic, Type
from pydantic import BaseModel


T = TypeVar("T")


class BaseParams(BaseModel):
    """Base class for all parameter objects in the project.

    This class provides common functionality for all parameter objects, including
    validation, serialization, and utility methods.
    """

    class Config:
        """Pydantic configuration for parameter objects."""

        arbitrary_types_allowed = True
        extra = "forbid"  # Prevent extra attributes
        validate_assignment = True  # Validate on attribute assignment

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter object to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the parameter object
        """
        return self.dict(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseParams":
        """Create parameter object from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing parameter values

        Returns:
            BaseParams: Parameter object instance
        """
        return cls(**data)


class ParamBuilder(Generic[T]):
    """Builder pattern implementation for parameter objects.

    This class provides a fluent interface for building parameter objects,
    allowing for more readable parameter construction.

    Example:
        ```python
        params = VideoConversionParamBuilder()
            .with_quality("high")
            .with_resolution("720p")
            .build()
        ```
    """

    def __init__(self, param_class: Type[T]):
        """Initialize the parameter builder.

        Args:
            param_class (Type[T]): The parameter class to build
        """
        self.param_class = param_class
        self.params: Dict[str, Any] = {}

    def with_param(self, name: str, value: Any) -> "ParamBuilder[T]":
        """Set a parameter value.

        Args:
            name (str): Parameter name
            value (Any): Parameter value

        Returns:
            ParamBuilder[T]: Self for method chaining
        """
        self.params[name] = value
        return self

    def build(self) -> T:
        """Build the parameter object.

        Returns:
            T: Parameter object instance
        """
        return self.param_class(**self.params)
