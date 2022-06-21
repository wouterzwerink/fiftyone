"""
| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import abc
import atexit
from datetime import datetime
import fnmatch
import logging
import random
import string
import typing as t

from fiftyone.connection import Connection
from fiftyone.base.mapper import Mapper

logger = logging.getLogger(__name__)

TDataset = t.TypeVar("TDataset")  # = t.TypeVar("TDataset", bound=Dataset)
TSample = t.TypeVar("TSample")  # = t.TypeVar("TSample", bound=Sample)
TFrame = t.TypeVar("TFrame")  # = t.TypeVar("TFrame", bound=Frame)


def _get_random_characters(char_count: int) -> str:
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(char_count)
    )


class Client(abc.ABC, t.Generic[TDataset, TSample, TFrame]):
    """Abstract client for interacting with FiftyOne"""

    # region Singleton

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls, *args, **kwargs)
        return cls._instances[cls]

    # endregion

    # region Generic Class

    # The following class attributes should be defined as the classes passed
    # as the Generic's types when subclassing. This is to allow access as
    # getting a Generic's types is not reliable in all versions of python.
    DatasetType: t.ClassVar[t.Type[TDataset]]
    SampleType: t.ClassVar[t.Type[TSample]]
    FrameType: t.ClassVar[t.Type[TFrame]]

    def __init_subclass__(cls, *args, **kwargs):
        # This method ensures the above class atrributes, related to the
        # Generic, are defined on any subclass.
        required_cls_attrs = ("DatasetType", "SampleType", "FrameType")
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

    def __init__(self, connection: Connection, mapper: Mapper):
        if not isinstance(connection, Connection):
            raise TypeError(
                "`connection` must be an instance of "
                f"{Connection.__name__}",
            )

        if not isinstance(mapper, Mapper):
            raise TypeError(
                "`mapper` must be an instance of " f"{Mapper.__name__}",
            )

        if not mapper.has_mappings(
            (self.DatasetType, connection.DatasetSchema, True),
            (self.SampleType, connection.SampleSchema, True),
            (self.FrameType, connection.FrameSchema, True),
        ):
            raise ValueError(
                "Must be able to map between client and connection"
            )

        self._connection = connection
        self._mapper = mapper

        # Caches: could be dicts or some classes
        # self._dataset_cache = {}
        # self._sample_cache = {}
        # self._frame_cache = {}

        self._closed = False
        atexit.register(self.close)  # Attach method to main program exit

    def close(self) -> bool:
        """Closes the client.

        Returns:
            bool: If the client is already closed.
        """
        already_closed, self._closed = self._closed, True
        return already_closed

    # region Dataset

    def _create_dataset(  # pylint: disable=unused-argument,no-self-use
        self,
        name: str,
        persistent: bool,
        **kwargs,
    ) -> t.Tuple(t.Mapping[str, t.Any, t.Type[TSample], t.Type[TFrame]]):
        # TODO: implement this. see fiftyone.core.dataset
        return None, None, None

    def _load_dataset(  # pylint: disable=unused-argument,no-self-use
        self,
        name: str,
        virtual: bool,
        **kwargs,
    ) -> t.Tuple(t.Mapping[str, t.Any, t.Type[TSample], t.Type[TFrame]]):
        # TODO: implement this. see fiftyone.core.dataset
        return None, None, None

    def Dataset(  # pylint: disable=invalid-name
        self,
        name: str = None,
        persistent: bool = False,
        overwrite: bool = False,
        _create: bool = True,
        _virtual: bool = False,
        **kwargs,
    ) -> TDataset:
        """Construct a FiftyOne dataset.

        Args:
            name (None): the name of the dataset. By default,
                :func:`get_default_dataset_name` is used
            persistent (False)
                whether the dataset should persist in the database after the
                session terminates
            overwrite (False)
                whether to overwrite an existing dataset of the same name
        """
        if name is None and _create:
            name = self.get_default_dataset_name()

        if overwrite and self.dataset_exists(name):
            self.delete_dataset(name)

        if _create:
            data, sample_doc_cls, frame_doc_cls = self._create_dataset(
                name, persistent=persistent, **kwargs
            )
        else:
            data, sample_doc_cls, frame_doc_cls = self._load_dataset(
                name, virtual=_virtual
            )

        return self.DatasetType(self, sample_doc_cls, frame_doc_cls, **data)

    def list_datasets(
        self, info: bool = False
    ) -> t.Union[t.List[str], t.List[t.Mapping[str, t.Any]]]:
        """Lists the available FiftyOne datasets.

        Args:
            info (False): whether to return info dicts describing each dataset
                rather than just their names

        Returns:
            a list of dataset names or info dicts
        """
        iterator = self._connection.iter_datasets()
        if info:
            return_value = []
            for data in iterator:
                try:
                    info_keys = (
                        "name",
                        "created_at",
                        "last_loaded_at",
                        "version",
                        "persistent",
                        "media_type",
                    )

                    i = {key: data[key] for key in info_keys}
                    i["num_samples"] = self._connection.count_samples(
                        data["name"]
                    )
                except:  # pylint: disable=bare-except
                    # If the dataset can't be loaded, it likely requires
                    # migration, so we can't show any information about it
                    i = {key: None for key in info_keys[1:]}
                    i["name"] = data["name"]
                    i["num_samples"] = None
                return_value.append(i)
            return return_value
        return list(iterator)

    def dataset_exists(self, name: str) -> bool:
        """Checks if the dataset exists.

        Args:
            name: the name of the dataset

        Returns:
            True/False
        """
        return self._connection.has_dataset(name)

    def load_dataset(self, name: str, ignore_cache=False) -> TDataset:
        """Loads the FiftyOne dataset with the given name.

        To create a new dataset, use the :class:`Dataset` factory method.

        .. note::

            :class:`Dataset` instances are singletons keyed by their name, so
            all calls to this method with a given dataset ``name`` in a program
            will return the same object.

        Args:
            name: the name of the dataset

        Returns:
            a :class:`Dataset`
        """

        if ignore_cache:
            ...
            # TODO: do this for realsies
            #     del self.dataset_cache[name]

        return self.Dataset(name, _create=False)

    def get_default_dataset_name(self) -> str:
        """Returns a default dataset name based on the current time.

        Returns:
            a dataset name
        """
        now = datetime.now()
        name = now.strftime("%Y.%m.%d.%H.%M.%S")
        if name in (
            data["name"]
            for data in self._connection.iter_datasets(include_private=True)
        ):
            name = now.strftime("%Y.%m.%d.%H.%M.%S.%f")

        return name

    def make_unique_dataset_name(self, root: str) -> str:
        """Makes a unique dataset name with the given root name.

        Args:
            root: the root name for the dataset

        Returns:
            the dataset name
        """
        name = root
        dataset_names = list(
            (
                data["name"]
                for data in self._connection.iter_datasets(
                    include_private=True
                )
            )
        )

        if name in dataset_names:
            name += "_" + _get_random_characters(6)

        while name in dataset_names:
            name += _get_random_characters(1)

        return name

    def get_default_dataset_dir(self, name: str) -> str:
        # TODO : get config
        # os.path.join(fo.config.default_dataset_dir, name)
        """Returns the default dataset directory for the dataset with the given
        name.

        Args:
            name: the dataset name

        Returns:
            the default directory for the dataset
        """

    def delete_dataset(self, name, verbose=False):
        """Deletes the FiftyOne dataset with the given name.

        Args:
            name: the name of the dataset
            verbose (False): whether to log the name of the deleted dataset
        """
        self._connection.delete_dataset(name)

        if verbose:
            logger.info(f"Dataset '{name}' deleted")

    def delete_datasets(self, glob_patt, verbose=False):
        """Deletes all FiftyOne datasets whose names match the given glob
            pattern.

        Args:
            glob_patt: a glob pattern of datasets to delete
            verbose (False): whether to log the names of deleted datasets
        """
        all_datasets = (
            data["name"] for data in self._connection.iter_datasets()
        )
        for name in fnmatch.filter(all_datasets, glob_patt):
            self.delete_dataset(name, verbose=verbose)

    def delete_non_persistent_datasets(self, verbose=False):
        """Deletes all non-persistent datasets.

        Args:
            verbose (False): whether to log the names of deleted datasets
        """
        for data in self._connection.iter_datasets(persistent=True):
            self.delete_dataset(data["name"], verbose=verbose)

    # [New Public Method]
    def get_dataset_stats(
        self,
        dataset: TDataset,
        include_media: bool = False,
        compressed: bool = False,
    ) -> t.Mapping[str, t.Any]:
        """Returns stats about the dataset on disk.

        The ``samples`` keys refer to the sample-level labels for the dataset
        as they are stored in the database.

        The ``media`` keys refer to the raw media associated with each sample
        in the dataset on disk (only included if ``include_media`` is True).

        The ``frames`` keys refer to the frame labels for the dataset as they
        are stored in the database (video datasets only).

        Args:
            include_media (False): whether to include stats about the size of
                the raw media in the dataset
            compressed (False): whether to return the sizes of collections in
                their compressed form on disk (True) or the logical
                uncompressed size of  the collections (False)

        Returns:
            a stats dict
        """
        # stats = {}

        # conn = foo.get_db_conn()

        # cs = conn.command("collstats", self._sample_collection_name)
        # samples_bytes = cs["storageSize"] if compressed else cs["size"]
        # stats["samples_count"] = cs["count"]
        # stats["samples_bytes"] = samples_bytes
        # stats["samples_size"] = etau.to_human_bytes_str(samples_bytes)
        # total_bytes = samples_bytes

        # if self.media_type == fom.VIDEO:
        #     cs = conn.command("collstats", self._frame_collection_name)
        #     frames_bytes = cs["storageSize"] if compressed else cs["size"]
        #     stats["frames_count"] = cs["count"]
        #     stats["frames_bytes"] = frames_bytes
        #     stats["frames_size"] = etau.to_human_bytes_str(frames_bytes)
        #     total_bytes += frames_bytes

        # if include_media:
        #     self.compute_metadata()
        #     media_bytes = self.sum("metadata.size_bytes")
        #     stats["media_bytes"] = media_bytes
        #     stats["media_size"] = etau.to_human_bytes_str(media_bytes)
        #     total_bytes += media_bytes

        # stats["total_bytes"] = total_bytes
        # stats["total_size"] = etau.to_human_bytes_str(total_bytes)

        # return stats

    # [New Public Method]
    def rename_dataset(self, old_name: str, new_name: str) -> None:
        """Rename a dataset"""
        if new_name in self.list_datasets():
            raise ValueError("A dataset with name '{name}' already exists")

        self._connection.patch_dataset(old_name, name=new_name)

        # Update Dataset singleton
        # self._instances.pop(_name, None)
        # self._instances[name] = self

    # [New Public Method]
    def save_dataset(self, dataset: TDataset) -> None:
        """Save a dataset"""
        data = self._mapper.map(dataset, self._connection.DatasetSchema)
        self._connection.save_dataset(dataset.name, data)

    # endregion

    def load_sample(self, dataset: TDataset, value: str) -> TSample:
        """Loads the FiftyOne sample with the given value.


        Args:
            value: the id or filepath of the sample

        Returns:
            a :class:`Sample`
        """

        data = self._connection.get_sample(dataset.name, value)

        sample = self._mapper.map(data, self.SampleType)
        sample.dataset = dataset

        # TODO: transform sample_data to TSample
        # doc = self._sample_dict_to_doc(d)
        # return fos.Sample.from_doc(doc, dataset=self)

        return sample
