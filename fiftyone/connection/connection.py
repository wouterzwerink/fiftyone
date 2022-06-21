"""
| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import abc
import typing as t


TDatasetSchema = t.TypeVar("TDatasetSchema")
TSampleSchema = t.TypeVar("TSampleSchema")
TFrameSchema = t.TypeVar("TFrameSchema")


class Connection(
    abc.ABC, t.Generic[TDatasetSchema, TSampleSchema, TFrameSchema]
):
    """Abstract class for connecting to FiftyOne data"""

    # region Generic Class

    # The following class attributes should be defined as the classes passed
    # as the Generic's types when subclassing. This is to allow access as
    # getting a Generic's types is not reliable in all versions of python.
    DatasetSchema: t.ClassVar[t.Type[TDatasetSchema]]
    SampleSchema: t.ClassVar[t.Type[TSampleSchema]]
    FrameSchema: t.ClassVar[t.Type[TFrameSchema]]

    def __init_subclass__(cls, *args, **kwargs):
        # This method ensures the above class atrributes, related to the
        # Generic, are defined on any subclass.
        required_cls_attrs = (
            "DatasetSchema",
            "SampleSchema",
            "FrameSchema",
        )
        missing_cls_attrs = [
            attr for attr in required_cls_attrs if not hasattr(cls, attr)
        ]
        if missing_cls_attrs:
            raise TypeError(
                f"Cannot instantiate implemetation `{cls.__name__}` without "
                f"the following attributes: [{', '.join(missing_cls_attrs)}]"
            )
        super().__init_subclass__(*args, **kwargs)

    # endregion

    # region Dataset

    @abc.abstractmethod
    def delete_dataset(self, dataset_name: str) -> None:
        """Delete a dataset"""

    @abc.abstractmethod
    def get_dataset(self, dataset_name: str) -> TDatasetSchema:
        """Get a dataset"""

    @abc.abstractmethod
    def has_dataset(self, dataset_name: str) -> bool:
        """Determines whether a dataset exists."""

    @abc.abstractmethod
    def iter_dataset(
        self, *_, persistent: bool = None, include_private: bool = False
    ) -> t.Generator[TDatasetSchema]:
        """Iterate over datasets."""

    @abc.abstractmethod
    def patch_dataset(
        self, dataset_name: str, *_, **update: t.Mapping[str, t.Any]
    ) -> None:
        """Patch update a dataset"""

    @abc.abstractmethod
    def save_dataset(self, dataset: TDatasetSchema) -> None:
        """Create or update a dataset"""

    # endregion

    # region Dataset View

    # endregion

    # region Sample

    @abc.abstractmethod
    def count_samples(self, dataset_name: str) -> int:
        """Count samples in a dataset"""

    # endregion

    # region Frame

    # endregion
