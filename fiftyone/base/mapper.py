"""
| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import inspect
import typing as t


TSource = t.TypeVar("TSource")
TTarget = t.TypeVar("TTarget")


class Mapper:
    """A class for maintaining mappings netween classes"""

    def __init__(self):
        self._maps = {}

    def add_mapping(
        self,
        source_cls: t.Type[TSource],
        target_cls: t.Type[TTarget],
        mapping_fn: t.Callable[[TSource], TTarget],
        reverse_mapping_fn: t.Callable[[TTarget], TSource] = None,
    ) -> None:
        """Register a mapping between two classes

        Args:
            source_cls (t.Type[TSource]): The source class
            target_cls (t.Type[TTarget]): The target class
            mapping_fn (t.Callable[[TSource], TTarget]):
                A function which accepts an instance of 'TSource' and returns
                and instance of 'TTarget'
        """

        if not inspect.isclass(source_cls):
            raise TypeError("'source_cls' must be a class")

        if not inspect.isclass(target_cls):
            raise TypeError("'target_cls' must be a class")

        if not callable(mapping_fn):
            raise TypeError("'mapping_fn' must be callable")

        if self.has_mapping(source_cls, target_cls):
            raise ValueError(
                f"A mapping already exists from '{source_cls.__name__}' to "
                f"'{target_cls.__name__}'"
            )

        if reverse_mapping_fn is not None:
            if not callable(reverse_mapping_fn):
                raise TypeError("'reverse_mapping_fn' must be callable")

            if self.has_mapping(  # pylint: disable=arguments-out-of-order
                target_cls, source_cls
            ):
                raise ValueError(
                    f"A mapping already exists from '{target_cls.__name__}' "
                    f"to '{source_cls.__name__}'"
                )

            self._maps[(target_cls, source_cls)] = reverse_mapping_fn

        self._maps[(source_cls, target_cls)] = mapping_fn

    def has_mapping(
        self,
        source_cls: t.Type[TSource],
        target_cls: t.Type[TTarget],
        *,
        bidirectional: bool = False,
    ) -> bool:
        """Determine whether a mapping has been registed

        Args:
            source_cls (t.Type[TSource]): The source class
            target_cls (t.Type[TTarget]): The target class
        Returns:
            bool: Whether or not a map has been registered
        """
        if not inspect.isclass(source_cls):
            raise TypeError("'source_cls' must be a class")

        if not inspect.isclass(target_cls):
            raise TypeError("'target_cls' must be a class")

        if (source_cls, target_cls) not in self._maps:
            return False

        if bidirectional:
            return self.has_mapping(  # pylint: disable=arguments-out-of-order
                target_cls, source_cls
            )

        return True

    def has_mappings(
        self, *args: t.Tuple[t.Type[TSource], t.Type[TTarget], bool]
    ) -> bool:
        """Determine whether a multiple mappings have been registed

        Args:
            *args (t.Tuple[t.Type[TSource], t.Type[TTarget], bool])
                A tuple of source class, target class and whether to check
                bidirectional mappings.
        Returns:
            bool: Whether or not all mappings have been registered
        """
        return all(
            (
                self.has_mapping(
                    source_cls, target_cls, bidirectional=bidirectional
                )
                for source_cls, target_cls, bidirectional in args
            )
        )

    def remove_mapping(
        self,
        source_cls: t.Type[TSource],
        target_cls: t.Type[TTarget],
    ) -> bool:
        """Remove a mapping between two classes

        Args:
            source_cls (t.Type[TSource]): The source class
            target_cls (t.Type[TTarget]): The target class
        """
        try:
            del self._maps[(source_cls, target_cls)]
        except KeyError:
            return None

    def map(
        self,
        source_inst: TSource,
        target_cls: t.Type[TTarget],
    ) -> TTarget:
        """Map an instance to target class instance

        Args:
            source_inst (TSource): The instance to map.
            target_cls (t.Type[TTarget]): The target class for the instance.

        Returns:
            TTarget: The newly mapped  instance.
        """

        try:
            source_cls = source_inst.__class__
        except Exception as err:
            raise TypeError(
                "'source_inst' must be an instance of a class"
            ) from err

        if not self.has_mapping(source_cls, target_cls):
            raise ValueError(
                f"No mapping exists from '{source_cls.__name__}' to "
                f"'{target_cls.__name__}'"
            )

        try:
            return self._maps[(source_cls, target_cls)](source_inst)
        except Exception as err:
            raise RuntimeError(
                "An unknown error occured while mapping from "
                f"'{source_cls.__name__}' to {target_cls.__name__}",
                *err.args,
            ) from err
