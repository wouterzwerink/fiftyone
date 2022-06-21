# """
# FiftyOne datasets.

# | Copyright 2017-2022, Voxel51, Inc.
# | `voxel51.com <https://voxel51.com/>`_
# |
# """
# from collections import defaultdict
# from copy import deepcopy
# from datetime import datetime
# import logging
# import numbers
# import os

# import typing as t

# from bson import ObjectId
# from deprecated import deprecated
# import mongoengine.errors as moe
# from pymongo import DeleteMany, InsertOne, ReplaceOne, UpdateMany, UpdateOne
# from pymongo.errors import CursorNotFound, BulkWriteError

# import eta.core.serial as etas
# import eta.core.utils as etau

# import fiftyone as fo
# import fiftyone.core.aggregations as foa
# import fiftyone.core.annotation as foan
# import fiftyone.core.brain as fob
# import fiftyone.constants as focn
# import fiftyone.core.collections as foc
# import fiftyone.core.expressions as foex
# import fiftyone.core.evaluation as foe
# import fiftyone.core.fields as fof
# import fiftyone.core.frame as fofr
# import fiftyone.core.labels as fol
# import fiftyone.core.media as fom
# import fiftyone.core.metadata as fome
# from fiftyone.core.odm.dataset import SampleFieldDocument
# import fiftyone.migrations as fomi
# import fiftyone.core.odm as foo
# import fiftyone.core.sample as fos
# from fiftyone.core.singletons import DatasetSingleton
# import fiftyone.core.utils as fou
# import fiftyone.core.view as fov


# fost = fou.lazy_import("fiftyone.core.stages")
# foud = fou.lazy_import("fiftyone.utils.data")


# logger = logging.getLogger(__name__)


# if t.TYPE_CHECKING:
#     from fiftyone.base.client import Client
#     from fiftyone.base.client import TSample
#     from fiftyone.base.client import TFrame


# class Dataset(foc.SampleCollection):
#     """A FiftyOne dataset.

#     Datasets represent an ordered collection of
#     :class:`fiftyone.core.sample.Sample` instances that describe a particular
#     type of raw media (e.g., images or videos) together with a user-defined set
#     of fields.

#     FiftyOne datasets ingest and store the labels for all samples internally;
#     raw media is stored on disk and the dataset provides paths to the data.

#     See :ref:`this page <using-datasets>` for an overview of working with
#     FiftyOne datasets.

#     Args:
#         name (None): the name of the dataset. By default,
#             :func:`get_default_dataset_name` is used
#         persistent (False): whether the dataset should persist in the database
#             after the session terminates
#         overwrite (False): whether to overwrite an existing dataset of the same
#             name
#     """

#     def __init__(  # pylint: disable=too-many-arguments
#         self,
#         client: Client,
#         sample_doc_cls,
#         frame_doc_cls,
#         name: str = None,
#         media_type=None,
#         version=None,
#         created_at=None,
#         last_loaded_at=None,
#         info=None,
#         classes=None,
#         default_classes=None,
#         mask_targets=None,
#         default_mask_targets=None,
#         skeletons=None,
#         default_skeletons=None,
#         sample_fields=None,
#         persistent=False,
#         **kwargs,
#     ):
#         self._client = client

#         self._sample_doc_cls = sample_doc_cls
#         self._frame_doc_cls = frame_doc_cls

#         self._name = name
#         self._media_type = media_type
#         self._sample_fields = sample_fields
#         self._persistent = persistent

#         self._annotation_cache = {}
#         self._brain_cache = {}
#         self._evaluation_cache = {}

#         self._deleted = False

#     @property
#     def client(self) -> "Client":
#         """The FiftyOne client bound to the dataset"""
#         return self._client

#     def save(self) -> None:
#         return self._client.save_dataset(self)

#     def __len__(self) -> int:
#         return self.count()  # TODO: move to sample collection class

#     def __getitem__(
#         self, id_filepath_slice: t.Union[int, slice, str]
#     ) -> t.Any:
#         if isinstance(id_filepath_slice, numbers.Integral):
#             raise ValueError(
#                 "Accessing dataset samples by numeric index is not supported. "
#                 "Use sample IDs, filepaths, slices, boolean arrays, or a "
#                 "boolean ViewExpression instead"
#             )

#         if isinstance(id_filepath_slice, slice):
#             return self.view()[id_filepath_slice]

#         if isinstance(id_filepath_slice, foex.ViewExpression):
#             return self.view()[id_filepath_slice]

#         if etau.is_container(id_filepath_slice):
#             return self.view()[id_filepath_slice]

#         try:
#             return self.client.load_sample(self, id_filepath_slice)
#         except ValueError as err:
#             raise KeyError(*err.args) from err

#     def __delitem__(self, samples_or_ids: t.Union[int, slice, str]) -> None:
#         self.delete_samples(samples_or_ids)

#     def __getattribute__(self, name: str) -> t.Any:
#         #
#         # The attributes necessary to determine a dataset's name and whether
#         # it is deleted are always available. If a dataset is deleted, no other
#         # methods are available
#         #
#         if not (
#             name.startswith("__") or name in ("name", "deleted", "_deleted")
#         ) and getattr(self, "_deleted", False):
#             raise ValueError(f"Dataset '{self.name}' is deleted")
#         return super().__getattribute__(name)

#     @property
#     def _dataset(self) -> "Dataset":
#         return self

#     @property
#     def _root_dataset(self) -> "Dataset":
#         return self

#     @property
#     def _is_generated(self) -> bool:
#         return self._is_patches or self._is_frames or self._is_clips

#     @property
#     def _is_patches(self) -> bool:
#         return self._sample_collection_name.startswith("patches.")

#     @property
#     def _is_frames(self) -> bool:
#         return self._sample_collection_name.startswith("frames.")

#     @property
#     def _is_clips(self) -> bool:
#         return self._sample_collection_name.startswith("clips.")

#     @property
#     def media_type(
#         self,
#     ) -> t.Union[t.Literal["image"], t.Literal["video"], None]:
#         """The media type of the dataset."""
#         return self._media_type

#     @media_type.setter
#     def media_type(self, media_type):
#         # TODO: figure out what todo here
#         # if len(self):
#         #     raise ValueError("Cannot set media type of a non-empty dataset")

#         # if media_type not in fom.MEDIA_TYPES:
#         #     raise ValueError(
#         #         "Invalid media_type '%s'. Supported values are %s"
#         #         % (media_type, fom.MEDIA_TYPES)
#         #     )

#         # if media_type == str(self.__fiftyone_ref__.definition.media_type):
#         #     return

#         # self.__fiftyone_ref__.definition.media_type = MediaType(media_type)
#         # data_type: t.Type[fome.Metadata]

#         # if media_type == fom.IMAGE:
#         #     data_type = fome.ImageMetadata
#         # elif media_type == fom.VIDEO:
#         #     data_type = fome.VideoMetadata
#         # else:
#         #     data_type = fome.Metadata

#         # self.__fiftyone_ref__.schema["metadata"].type = data_type
#         # self.__fiftyone_ref__.commit()

#         if self:
#             raise ValueError("Cannot set media type of a non-empty dataset")

#         if media_type not in fom.MEDIA_TYPES:
#             raise ValueError(
#                 f"Invalid media_type '{media_type}'. "
#                 f"Supported values are {fom.MEDIA_TYPES}"
#             )

#         if media_type == self._media_type:
#             return

#         self._media_type = media_type
#         self._set_metadata(media_type)

#     def _set_metadata(self, media_type):
#         idx = None
#         for i, field in enumerate(self._doc.sample_fields):
#             if field.name == "metadata":
#                 idx = i

#         if idx is not None:
#             if media_type == fom.IMAGE:
#                 doc_type = fome.ImageMetadata
#             elif media_type == fom.VIDEO:
#                 doc_type = fome.VideoMetadata
#             else:
#                 doc_type = fome.Metadata

#             field = foo.create_field(
#                 "metadata",
#                 fof.EmbeddedDocumentField,
#                 embedded_doc_type=doc_type,
#             )
#             field_doc = foo.SampleFieldDocument.from_field(field)
#             self._doc.sample_fields[idx] = field_doc

#         if media_type == fom.VIDEO:
#             # pylint: disable=no-member
#             self._doc.frame_fields = [
#                 foo.SampleFieldDocument.from_field(field)
#                 for field in self._frame_doc_cls._fields.values()
#             ]

#         self.save()
#         self.reload()

#     @property
#     def version(self) -> str:
#         """The version of the ``fiftyone`` package for which the dataset is
#         formatted.
#         """
#         return self._version

#     @property
#     def name(self) -> str:
#         """The name of the dataset."""
#         return self._name

#     @name.setter
#     def name(self, value: str) -> None:
#         if value == self._name:
#             return
#         self.client.rename_dataset(self._name, value)
#         self._name = value

#     @property
#     def created_at(self) -> datetime:
#         """The datetime that the dataset was created."""
#         return self._created_at

#     @property
#     def last_loaded_at(self) -> datetime:
#         """The datetime that the dataset was last loaded."""
#         return self._last_loaded_at

#     @property
#     def persistent(self) -> bool:
#         """Whether the dataset persists in the database after a session is
#         terminated.
#         """
#         return self._persistent

#     @persistent.setter
#     def persistent(self, value: bool) -> None:
#         value = bool(value)

#         if self._persistent is value:
#             return

#         self.client.patch_dataset(self, value)
#         self._persistent = value

#     @property
#     def info(self) -> t.Any:
#         """A user-facing dictionary of information about the dataset.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Store a class list in the dataset's info
#             dataset.info = {"classes": ["cat", "dog"]}

#             # Edit the info
#             dataset.info["other_classes"] = ["bird", "plane"]
#             dataset.save()  # must save after edits
#         """
#         return self._info

#     @info.setter
#     def info(self, info: t.Any) -> None:
#         self._info = info
#         self.save()

#     @property
#     def classes(self) -> t.Mapping[str, t.List[str]]:
#         """A dict mapping field names to list of class label strings for the
#         corresponding fields of the dataset.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set classes for the `ground_truth` and `predictions` fields
#             dataset.classes = {
#                 "ground_truth": ["cat", "dog"],
#                 "predictions": ["cat", "dog", "other"],
#             }

#             # Edit an existing classes list
#             dataset.classes["ground_truth"].append("other")
#             dataset.save()  # must save after edits
#         """
#         return self._classes

#     @classes.setter
#     def classes(self, classes: t.Mapping[str, t.List[str]]) -> None:
#         self._classes = classes
#         self.save()

#     @property
#     def default_classes(self) -> t.Mapping[str, t.List[str]]:
#         """A list of class label strings for all
#         :class:`fiftyone.core.labels.Label` fields of this dataset that do not
#         have customized classes defined in :meth:`classes`.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set default classes
#             dataset.default_classes = ["cat", "dog"]

#             # Edit the default classes
#             dataset.default_classes.append("rabbit")
#             dataset.save()  # must save after edits
#         """
#         return self._default_classes

#     @default_classes.setter
#     def default_classes(self, classes: t.Mapping[str, t.List[str]]) -> None:
#         self._default_classes = classes
#         self.save()

#     @property
#     def mask_targets(self) -> t.Mapping[str, t.Mapping[int, str]]:
#         """A dict mapping field names to mask target dicts, each of which
#         defines a mapping between pixel values and label strings for the
#         segmentation masks in the corresponding field of the dataset.

#         .. note::

#             The pixel value `0` is a reserved "background" class that is
#             rendered as invisible in the App.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set mask targets for the `ground_truth` and `predictions` fields
#             dataset.mask_targets = {
#                 "ground_truth": {1: "cat", 2: "dog"},
#                 "predictions": {1: "cat", 2: "dog", 255: "other"},
#             }

#             # Edit an existing mask target
#             dataset.mask_targets["ground_truth"][255] = "other"
#             dataset.save()  # must save after edits
#         """
#         return self._mask_targets

#     @mask_targets.setter
#     def mask_targets(
#         self, targets: t.Mapping[str, t.Mapping[int, str]]
#     ) -> None:
#         self._mask_targets = targets
#         self.save()

#     @property
#     def default_mask_targets(self) -> t.Mapping[str, t.Mapping[int, str]]:
#         """A dict defining a default mapping between pixel values and label
#         strings for the segmentation masks of all
#         :class:`fiftyone.core.labels.Segmentation` fields of this dataset that
#         do not have customized mask targets defined in :meth:`mask_targets`.

#         .. note::

#             The pixel value `0` is a reserved "background" class that is
#             rendered as invisible in the App.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set default mask targets
#             dataset.default_mask_targets = {1: "cat", 2: "dog"}

#             # Edit the default mask targets
#             dataset.default_mask_targets[255] = "other"
#             dataset.save()  # must save after edits
#         """
#         return self._default_mask_targets

#     @default_mask_targets.setter
#     def default_mask_targets(
#         self, targets: t.Mapping[str, t.Mapping[int, str]]
#     ) -> None:
#         self._default_mask_targets = targets
#         self.save()

#     @property
#     def skeletons(self) -> t.Mapping[str, KeypointSkeleton]:
#         # TODO: redfine and import and KeypointSkeleton
#         """A dict mapping field names to
#         :class:`fiftyone.core.odm.dataset.KeypointSkeleton` instances, each of
#         which defines the semantic labels and point connectivity for the
#         :class:`fiftyone.core.labels.Keypoint` instances in the corresponding
#         field of the dataset.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set keypoint skeleton for the `ground_truth` field
#             dataset.skeletons = {
#                 "ground_truth": fo.KeypointSkeleton(
#                     labels=[
#                         "left hand" "left shoulder", "right shoulder", "right hand",
#                         "left eye", "right eye", "mouth",
#                     ],
#                     edges=[[0, 1, 2, 3], [4, 5, 6]],
#                 )
#             }

#             # Edit an existing skeleton
#             dataset.skeletons["ground_truth"].labels[-1] = "lips"
#             dataset.save()  # must save after edits
#         """
#         return self._skeletons

#     @skeletons.setter
#     def skeletons(self, skeletons: t.Mapping[str, KeypointSkeleton]) -> None:
#         self._skeletons = skeletons
#         self.save()

#     @property
#     def default_skeleton(self) -> t.Mapping[str, KeypointSkeleton]:
#         """A default :class:`fiftyone.core.odm.dataset.KeypointSkeleton`
#         defining the semantic labels and point connectivity for all
#         :class:`fiftyone.core.labels.Keypoint` fields of this dataset that do
#         not have customized skeletons defined in :meth:`skeleton`.

#         Examples::

#             import fiftyone as fo

#             dataset = fo.Dataset()

#             # Set default keypoint skeleton
#             dataset.default_skeleton = fo.KeypointSkeleton(
#                 labels=[
#                     "left hand" "left shoulder", "right shoulder", "right hand",
#                     "left eye", "right eye", "mouth",
#                 ],
#                 edges=[[0, 1, 2, 3], [4, 5, 6]],
#             )

#             # Edit the default skeleton
#             dataset.default_skeleton.labels[-1] = "lips"
#             dataset.save()  # must save after edits
#         """
#         return self._doc.default_skeleton

#     @default_skeleton.setter
#     def default_skeleton(
#         self, skeleton: t.Mapping[str, KeypointSkeleton]
#     ) -> None:
#         self._default_skeleton = skeleton
#         self.save()

#     @property
#     def deleted(self) -> bool:  # TODO : this may no longer be necessary
#         """Whether the dataset is deleted."""
#         return self._deleted

#     def summary(self):  # TODO : checkthe innards
#         """Returns a string summary of the dataset.

#         Returns:
#             a string summary
#         """
#         aggs = self.aggregate([foa.Count(), foa.Distinct("tags")])
#         elements = [
#             ("Name:", self.name),
#             ("Media type:", self.media_type),
#             ("Num samples:", aggs[0]),
#             ("Persistent:", self.persistent),
#             ("Tags:", aggs[1]),
#         ]

#         elements = fou.justify_headings(elements)
#         lines = ["%s %s" % tuple(e) for e in elements]

#         lines.extend(
#             ["Sample fields:", self._to_fields_str(self.get_field_schema())]
#         )

#         if self.media_type == fom.VIDEO:
#             lines.extend(
#                 [
#                     "Frame fields:",
#                     self._to_fields_str(self.get_frame_field_schema()),
#                 ]
#             )

#         return "\n".join(lines)

#     def stats(
#         self, include_media: bool = False, compressed: bool = False
#     ) -> t.Mapping[str, t.Any]:
#         """Returns stats about the dataset on disk.

#         The ``samples`` keys refer to the sample-level labels for the dataset
#         as they are stored in the database.

#         The ``media`` keys refer to the raw media associated with each sample
#         in the dataset on disk (only included if ``include_media`` is True).

#         The ``frames`` keys refer to the frame labels for the dataset as they
#         are stored in the database (video datasets only).

#         Args:
#             include_media (False): whether to include stats about the size of
#                 the raw media in the dataset
#             compressed (False): whether to return the sizes of collections in
#                 their compressed form on disk (True) or the logical
#                 uncompressed size of  the collections (False)

#         Returns:
#             a stats dict
#         """
#         return self.client.get_dataset_stats()

#     def first(self):  # pylint: disable=useless-super-delegation
#         """Returns the first sample in the dataset.

#         Returns:
#             a :class:`fiftyone.core.sample.Sample`
#         """
#         return super().first()

#     def last(self):
#         """Returns the last sample in the dataset.

#         Returns:
#             a :class:`fiftyone.core.sample.Sample`
#         """
#         try:
#             sample_view = self[-1:].first()
#         except ValueError as err:
#             raise ValueError(f"{self.__class__.__name__} is empty") from err

#         # TODO : start with sample
#         return fos.Sample.from_doc(sample_view._doc, dataset=self)

#     def head(self, num_samples=3):
#         """Returns a list of the first few samples in the dataset.

#         If fewer than ``num_samples`` samples are in the dataset, only the
#         available samples are returned.

#         Args:
#             num_samples (3): the number of samples

#         Returns:
#             a list of :class:`fiftyone.core.sample.Sample` objects
#         """
#         return [
#             fos.Sample.from_doc(sv._doc, dataset=self)
#             for sv in self[:num_samples]
#         ]

#     def tail(self, num_samples=3):
#         """Returns a list of the last few samples in the dataset.

#         If fewer than ``num_samples`` samples are in the dataset, only the
#         available samples are returned.

#         Args:
#             num_samples (3): the number of samples

#         Returns:
#             a list of :class:`fiftyone.core.sample.Sample` objects
#         """
#         return [
#             fos.Sample.from_doc(sv._doc, dataset=self)
#             for sv in self[-num_samples:]
#         ]

#     def view(self):
#         """Returns a :class:`fiftyone.core.view.DatasetView` containing the
#         entire dataset.

#         Returns:
#             a :class:`fiftyone.core.view.DatasetView`
#         """
#         return fov.DatasetView(self)

#     def get_field_schema(
#         self, ftype=None, embedded_doc_type=None, include_private=False
#     ):
#         """Returns a schema dictionary describing the fields of the samples in
#         the dataset.

#         Args:
#             ftype (None): an optional field type to which to restrict the
#                 returned schema. Must be a subclass of
#                 :class:`fiftyone.core.fields.Field`
#             embedded_doc_type (None): an optional embedded document type to
#                 which to restrict the returned schema. Must be a subclass of
#                 :class:`fiftyone.core.odm.BaseEmbeddedDocument`
#             include_private (False): whether to include fields that start with
#                 ``_`` in the returned schema

#         Returns:
#              an ``OrderedDict`` mapping field names to field types
#         """
#         return self._sample_doc_cls.get_field_schema(
#             ftype=ftype,
#             embedded_doc_type=embedded_doc_type,
#             include_private=include_private,
#         )

#     def get_frame_field_schema(
#         self, ftype=None, embedded_doc_type=None, include_private=False
#     ):
#         """Returns a schema dictionary describing the fields of the frames of
#         the samples in the dataset.

#         Only applicable for video datasets.

#         Args:
#             ftype (None): an optional field type to which to restrict the
#                 returned schema. Must be a subclass of
#                 :class:`fiftyone.core.fields.Field`
#             embedded_doc_type (None): an optional embedded document type to
#                 which to restrict the returned schema. Must be a subclass of
#                 :class:`fiftyone.core.odm.BaseEmbeddedDocument`
#             include_private (False): whether to include fields that start with
#                 ``_`` in the returned schema

#         Returns:
#             a dictionary mapping field names to field types, or ``None`` if
#             the dataset is not a video dataset
#         """
#         if self.media_type != fom.VIDEO:
#             return None

#         return self._frame_doc_cls.get_field_schema(
#             ftype=ftype,
#             embedded_doc_type=embedded_doc_type,
#             include_private=include_private,
#         )

#     def add_sample_field(
#         self,
#         field_name,
#         ftype,
#         embedded_doc_type=None,
#         subfield=None,
#         **kwargs,
#     ):
#         """Adds a new sample field to the dataset.

#         Args:
#             field_name: the field name
#             ftype: the field type to create. Must be a subclass of
#                 :class:`fiftyone.core.fields.Field`
#             embedded_doc_type (None): the
#                 :class:`fiftyone.core.odm.BaseEmbeddedDocument` type of the
#                 field. Only applicable when ``ftype`` is
#                 :class:`fiftyone.core.fields.EmbeddedDocumentField`
#             subfield (None): the :class:`fiftyone.core.fields.Field` type of
#                 the contained field. Only applicable when ``ftype`` is
#                 :class:`fiftyone.core.fields.ListField` or
#                 :class:`fiftyone.core.fields.DictField`
#         """
#         self._sample_doc_cls.add_field(
#             field_name,
#             ftype,
#             embedded_doc_type=embedded_doc_type,
#             subfield=subfield,
#             **kwargs,
#         )
#         self._reload()

#     def _add_sample_field_if_necessary(
#         self,
#         field_name,
#         ftype,
#         embedded_doc_type=None,
#         subfield=None,
#         **kwargs,
#     ):
#         field_kwargs = dict(
#             ftype=ftype,
#             embedded_doc_type=embedded_doc_type,
#             subfield=subfield,
#             **kwargs,
#         )

#         schema = self.get_field_schema()
#         if field_name in schema:
#             foo.validate_fields_match(
#                 field_name, field_kwargs, schema[field_name]
#             )
#         else:
#             self.add_sample_field(field_name, **field_kwargs)

#     def _add_implied_sample_field(self, field_name, value):
#         self._sample_doc_cls.add_implied_field(field_name, value)
#         self._reload()

#     def add_frame_field(
#         self,
#         field_name,
#         ftype,
#         embedded_doc_type=None,
#         subfield=None,
#         **kwargs,
#     ):
#         """Adds a new frame-level field to the dataset.

#         Only applicable to video datasets.

#         Args:
#             field_name: the field name
#             ftype: the field type to create. Must be a subclass of
#                 :class:`fiftyone.core.fields.Field`
#             embedded_doc_type (None): the
#                 :class:`fiftyone.core.odm.BaseEmbeddedDocument` type of the
#                 field. Only applicable when ``ftype`` is
#                 :class:`fiftyone.core.fields.EmbeddedDocumentField`
#             subfield (None): the :class:`fiftyone.core.fields.Field` type of
#                 the contained field. Only applicable when ``ftype`` is
#                 :class:`fiftyone.core.fields.ListField` or
#                 :class:`fiftyone.core.fields.DictField`
#         """
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         self._frame_doc_cls.add_field(
#             field_name,
#             ftype,
#             embedded_doc_type=embedded_doc_type,
#             subfield=subfield,
#             **kwargs,
#         )
#         self._reload()

#     def _add_frame_field_if_necessary(
#         self,
#         field_name,
#         ftype,
#         embedded_doc_type=None,
#         subfield=None,
#         **kwargs,
#     ):
#         field_kwargs = dict(
#             ftype=ftype,
#             embedded_doc_type=embedded_doc_type,
#             subfield=subfield,
#             **kwargs,
#         )

#         schema = self.get_frame_field_schema()
#         if field_name in schema:
#             foo.validate_fields_match(
#                 field_name, field_kwargs, schema[field_name]
#             )
#         else:
#             self.add_frame_field(field_name, **field_kwargs)

#     def _add_implied_frame_field(self, field_name, value):
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         self._frame_doc_cls.add_implied_field(field_name, value)
#         self._reload()

#     def rename_sample_field(self, field_name, new_field_name):
#         """Renames the sample field to the given new name.

#         You can use dot notation (``embedded.field.name``) to rename embedded
#         fields.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             new_field_name: the new field name or ``embedded.field.name``
#         """
#         self._rename_sample_fields({field_name: new_field_name})

#     def rename_sample_fields(self, field_mapping):
#         """Renames the sample fields to the given new names.

#         You can use dot notation (``embedded.field.name``) to rename embedded
#         fields.

#         Args:
#             field_mapping: a dict mapping field names to new field names
#         """
#         self._rename_sample_fields(field_mapping)

#     def rename_frame_field(self, field_name, new_field_name):
#         """Renames the frame-level field to the given new name.

#         You can use dot notation (``embedded.field.name``) to rename embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             new_field_name: the new field name or ``embedded.field.name``
#         """
#         self._rename_frame_fields({field_name: new_field_name})

#     def rename_frame_fields(self, field_mapping):
#         """Renames the frame-level fields to the given new names.

#         You can use dot notation (``embedded.field.name``) to rename embedded
#         frame fields.

#         Args:
#             field_mapping: a dict mapping field names to new field names
#         """
#         self._rename_frame_fields(field_mapping)

#     def _rename_sample_fields(self, field_mapping, view=None):
#         (
#             fields,
#             new_fields,
#             embedded_fields,
#             embedded_new_fields,
#         ) = _parse_field_mapping(field_mapping)

#         if fields:
#             self._sample_doc_cls._rename_fields(fields, new_fields)
#             fos.Sample._rename_fields(
#                 self._sample_collection_name, fields, new_fields
#             )

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._sample_doc_cls._rename_embedded_fields(
#                 embedded_fields, embedded_new_fields, sample_collection
#             )
#             fos.Sample._reload_docs(self._sample_collection_name)

#         self._reload()

#     def _rename_frame_fields(self, field_mapping, view=None):
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         (
#             fields,
#             new_fields,
#             embedded_fields,
#             embedded_new_fields,
#         ) = _parse_field_mapping(field_mapping)

#         if fields:
#             self._frame_doc_cls._rename_fields(fields, new_fields)
#             fofr.Frame._rename_fields(
#                 self._frame_collection_name, fields, new_fields
#             )

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._frame_doc_cls._rename_embedded_fields(
#                 embedded_fields, embedded_new_fields, sample_collection
#             )
#             fofr.Frame._reload_docs(self._frame_collection_name)

#         self._reload()

#     def clone_sample_field(self, field_name, new_field_name):
#         """Clones the given sample field into a new field of the dataset.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         fields.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             new_field_name: the new field name or ``embedded.field.name``
#         """
#         self._clone_sample_fields({field_name: new_field_name})

#     def clone_sample_fields(self, field_mapping):
#         """Clones the given sample fields into new fields of the dataset.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         fields.

#         Args:
#             field_mapping: a dict mapping field names to new field names into
#                 which to clone each field
#         """
#         self._clone_sample_fields(field_mapping)

#     def clone_frame_field(self, field_name, new_field_name):
#         """Clones the frame-level field into a new field.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             new_field_name: the new field name or ``embedded.field.name``
#         """
#         self._clone_frame_fields({field_name: new_field_name})

#     def clone_frame_fields(self, field_mapping):
#         """Clones the frame-level fields into new fields.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_mapping: a dict mapping field names to new field names into
#                 which to clone each field
#         """
#         self._clone_frame_fields(field_mapping)

#     def _clone_sample_fields(self, field_mapping, view=None):
#         (
#             fields,
#             new_fields,
#             embedded_fields,
#             embedded_new_fields,
#         ) = _parse_field_mapping(field_mapping)

#         if fields:
#             self._sample_doc_cls._clone_fields(fields, new_fields, view)

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._sample_doc_cls._clone_embedded_fields(
#                 embedded_fields, embedded_new_fields, sample_collection
#             )

#         fos.Sample._reload_docs(self._sample_collection_name)
#         self._reload()

#     def _clone_frame_fields(self, field_mapping, view=None):
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         (
#             fields,
#             new_fields,
#             embedded_fields,
#             embedded_new_fields,
#         ) = _parse_field_mapping(field_mapping)

#         if fields:
#             self._frame_doc_cls._clone_fields(fields, new_fields, view)

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._frame_doc_cls._clone_embedded_fields(
#                 embedded_fields, embedded_new_fields, sample_collection
#             )

#         fofr.Frame._reload_docs(self._frame_collection_name)
#         self._reload()

#     def clear_sample_field(self, field_name):
#         """Clears the values of the field from all samples in the dataset.

#         The field will remain in the dataset's schema, and all samples will
#         have the value ``None`` for the field.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#         """
#         self._clear_sample_fields(field_name)

#     def clear_sample_fields(self, field_names):
#         """Clears the values of the fields from all samples in the dataset.

#         The field will remain in the dataset's schema, and all samples will
#         have the value ``None`` for the field.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Args:
#             field_names: the field name or iterable of field names
#         """
#         self._clear_sample_fields(field_names)

#     def clear_frame_field(self, field_name):
#         """Clears the values of the frame-level field from all samples in the
#         dataset.

#         The field will remain in the dataset's frame schema, and all frames
#         will have the value ``None`` for the field.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#         """
#         self._clear_frame_fields(field_name)

#     def clear_frame_fields(self, field_names):
#         """Clears the values of the frame-level fields from all samples in the
#         dataset.

#         The fields will remain in the dataset's frame schema, and all frames
#         will have the value ``None`` for the field.

#         You can use dot notation (``embedded.field.name``) to clone embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_names: the field name or iterable of field names
#         """
#         self._clear_frame_fields(field_names)

#     def _clear_sample_fields(self, field_names, view=None):
#         fields, embedded_fields = _parse_fields(field_names)

#         if fields:
#             self._sample_doc_cls._clear_fields(fields, view)

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._sample_doc_cls._clear_embedded_fields(
#                 embedded_fields, sample_collection
#             )

#         fos.Sample._reload_docs(self._sample_collection_name)

#     def _clear_frame_fields(self, field_names, view=None):
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         fields, embedded_fields = _parse_fields(field_names)

#         if fields:
#             self._frame_doc_cls._clear_fields(fields, view)

#         if embedded_fields:
#             sample_collection = self if view is None else view
#             self._frame_doc_cls._clear_embedded_fields(
#                 embedded_fields, sample_collection
#             )

#         fofr.Frame._reload_docs(self._frame_collection_name)

#     def delete_sample_field(self, field_name, error_level=0):
#         """Deletes the field from all samples in the dataset.

#         You can use dot notation (``embedded.field.name``) to delete embedded
#         fields.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             error_level (0): the error level to use. Valid values are:

#             -   0: raise error if a top-level field cannot be deleted
#             -   1: log warning if a top-level field cannot be deleted
#             -   2: ignore top-level fields that cannot be deleted
#         """
#         self._delete_sample_fields(field_name, error_level)

#     def delete_sample_fields(self, field_names, error_level=0):
#         """Deletes the fields from all samples in the dataset.

#         You can use dot notation (``embedded.field.name``) to delete embedded
#         fields.

#         Args:
#             field_names: the field name or iterable of field names
#             error_level (0): the error level to use. Valid values are:

#             -   0: raise error if a top-level field cannot be deleted
#             -   1: log warning if a top-level field cannot be deleted
#             -   2: ignore top-level fields that cannot be deleted
#         """
#         self._delete_sample_fields(field_names, error_level)

#     def delete_frame_field(self, field_name, error_level=0):
#         """Deletes the frame-level field from all samples in the dataset.

#         You can use dot notation (``embedded.field.name``) to delete embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_name: the field name or ``embedded.field.name``
#             error_level (0): the error level to use. Valid values are:

#             -   0: raise error if a top-level field cannot be deleted
#             -   1: log warning if a top-level field cannot be deleted
#             -   2: ignore top-level fields that cannot be deleted
#         """
#         self._delete_frame_fields(field_name, error_level)

#     def delete_frame_fields(self, field_names, error_level=0):
#         """Deletes the frame-level fields from all samples in the dataset.

#         You can use dot notation (``embedded.field.name``) to delete embedded
#         frame fields.

#         Only applicable to video datasets.

#         Args:
#             field_names: a field name or iterable of field names
#             error_level (0): the error level to use. Valid values are:

#             -   0: raise error if a top-level field cannot be deleted
#             -   1: log warning if a top-level field cannot be deleted
#             -   2: ignore top-level fields that cannot be deleted
#         """
#         self._delete_frame_fields(field_names, error_level)

#     def _delete_sample_fields(self, field_names, error_level):
#         fields, embedded_fields = _parse_fields(field_names)

#         if fields:
#             self._sample_doc_cls._delete_fields(
#                 fields, error_level=error_level
#             )
#             fos.Sample._purge_fields(self._sample_collection_name, fields)

#         if embedded_fields:
#             self._sample_doc_cls._delete_embedded_fields(embedded_fields)
#             fos.Sample._reload_docs(self._sample_collection_name)

#         self._reload()

#     def _delete_frame_fields(self, field_names, error_level):
#         if self.media_type != fom.VIDEO:
#             raise ValueError("Only video datasets have frame fields")

#         fields, embedded_fields = _parse_fields(field_names)

#         if fields:
#             self._frame_doc_cls._delete_fields(fields, error_level=error_level)
#             fofr.Frame._purge_fields(self._frame_collection_name, fields)

#         if embedded_fields:
#             self._frame_doc_cls._delete_embedded_fields(embedded_fields)
#             fofr.Frame._reload_docs(self._frame_collection_name)

#         self._reload()

#     def iter_samples(self, progress=False):
#         """Returns an iterator over the samples in the dataset.

#         Args:
#             progress (False): whether to render a progress bar tracking the
#                 iterator's progress

#         Returns:
#             an iterator over :class:`fiftyone.core.sample.Sample` instances
#         """
#         pipeline = self._pipeline(detach_frames=True)

#         if progress:
#             with fou.ProgressBar(total=len(self)) as pb:
#                 for sample in pb(self._iter_samples(pipeline)):
#                     yield sample
#         else:
#             for sample in self._iter_samples(pipeline):
#                 yield sample

#     def _iter_samples(self, pipeline):
#         index = 0

#         try:
#             for d in foo.aggregate(self._sample_collection, pipeline):
#                 doc = self._sample_dict_to_doc(d)
#                 sample = fos.Sample.from_doc(doc, dataset=self)
#                 index += 1
#                 yield sample

#         except CursorNotFound:
#             # The cursor has timed out so we yield from a new one after
#             # skipping to the last offset

#             pipeline.append({"$skip": index})
#             for sample in self._iter_samples(pipeline):
#                 yield sample

#     def add_sample(self, sample, expand_schema=True, validate=True):
#         """Adds the given sample to the dataset.

#         If the sample instance does not belong to a dataset, it is updated
#         in-place to reflect its membership in this dataset. If the sample
#         instance belongs to another dataset, it is not modified.

#         Args:
#             sample: a :class:`fiftyone.core.sample.Sample`
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if the sample's schema is not a subset of the dataset schema
#             validate (True): whether to validate that the fields of the sample
#                 are compliant with the dataset schema before adding it

#         Returns:
#             the ID of the sample in the dataset
#         """
#         return self._add_samples_batch([sample], expand_schema, validate)[0]

#     def add_samples(
#         self, samples, expand_schema=True, validate=True, num_samples=None
#     ):
#         """Adds the given samples to the dataset.

#         Any sample instances that do not belong to a dataset are updated
#         in-place to reflect membership in this dataset. Any sample instances
#         that belong to other datasets are not modified.

#         Args:
#             samples: an iterable of :class:`fiftyone.core.sample.Sample`
#                 instances or a
#                 :class:`fiftyone.core.collections.SampleCollection`
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             validate (True): whether to validate that the fields of each sample
#                 are compliant with the dataset schema before adding it
#             num_samples (None): the number of samples in ``samples``. If not
#                 provided, this is computed via ``len(samples)``, if possible.
#                 This value is optional and is used only for progress tracking

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         if num_samples is None:
#             try:
#                 num_samples = len(samples)
#             except:
#                 pass

#         # Dynamically size batches so that they are as large as possible while
#         # still achieving a nice frame rate on the progress bar
#         batcher = fou.DynamicBatcher(
#             samples, target_latency=0.2, init_batch_size=1, max_batch_beta=2.0
#         )

#         sample_ids = []
#         with fou.ProgressBar(total=num_samples) as pb:
#             for batch in batcher:
#                 sample_ids.extend(
#                     self._add_samples_batch(batch, expand_schema, validate)
#                 )
#                 pb.update(count=len(batch))

#         return sample_ids

#     def add_collection(
#         self, sample_collection, include_info=True, overwrite_info=False
#     ):
#         """Adds the contents of the given collection to the dataset.

#         This method is a special case of :meth:`Dataset.merge_samples` that
#         adds samples with new IDs to this dataset and omits any samples with
#         existing IDs (the latter would only happen in rare cases).

#         Use :meth:`Dataset.merge_samples` if you have multiple datasets whose
#         samples refer to the same source media.

#         Args:
#             samples: a :class:`fiftyone.core.collections.SampleCollection`
#             include_info (True): whether to merge dataset-level information
#                 such as ``info`` and ``classes``
#             overwrite_info (False): whether to overwrite existing dataset-level
#                 information. Only applicable when ``include_info`` is True

#         Returns:
#             a list of IDs of the samples that were added to this dataset
#         """
#         num_samples = len(self)
#         self.merge_samples(
#             sample_collection,
#             key_field="id",
#             skip_existing=True,
#             insert_new=True,
#             include_info=include_info,
#             overwrite_info=overwrite_info,
#         )
#         return self.skip(num_samples).values("id")

#     def _add_samples_batch(self, samples, expand_schema, validate):
#         samples = [s.copy() if s._in_db else s for s in samples]

#         if self.media_type is None and samples:
#             self.media_type = samples[0].media_type

#         if expand_schema:
#             self._expand_schema(samples)

#         if validate:
#             self._validate_samples(samples)

#         dicts = [self._make_dict(sample) for sample in samples]

#         try:
#             # adds `_id` to each dict
#             self._sample_collection.insert_many(dicts)
#         except BulkWriteError as bwe:
#             msg = bwe.details["writeErrors"][0]["errmsg"]
#             raise ValueError(msg) from bwe

#         for sample, d in zip(samples, dicts):
#             doc = self._sample_dict_to_doc(d)
#             sample._set_backing_doc(doc, dataset=self)
#             if self.media_type == fom.VIDEO:
#                 sample.frames.save()

#         return [str(d["_id"]) for d in dicts]

#     def _upsert_samples(
#         self, samples, expand_schema=True, validate=True, num_samples=None
#     ):
#         if num_samples is None:
#             try:
#                 num_samples = len(samples)
#             except:
#                 pass

#         # Dynamically size batches so that they are as large as possible while
#         # still achieving a nice frame rate on the progress bar
#         batcher = fou.DynamicBatcher(
#             samples, target_latency=0.2, init_batch_size=1, max_batch_beta=2.0
#         )

#         with fou.ProgressBar(total=num_samples) as pb:
#             for batch in batcher:
#                 self._upsert_samples_batch(batch, expand_schema, validate)
#                 pb.update(count=len(batch))

#     def _upsert_samples_batch(self, samples, expand_schema, validate):
#         if self.media_type is None and samples:
#             self.media_type = samples[0].media_type

#         if expand_schema:
#             self._expand_schema(samples)

#         if validate:
#             self._validate_samples(samples)

#         dicts = []
#         ops = []
#         for sample in samples:
#             d = self._make_dict(sample, include_id=True)
#             dicts.append(d)

#             if sample.id:
#                 ops.append(ReplaceOne({"_id": sample._id}, d, upsert=True))
#             else:
#                 d.pop("_id", None)
#                 ops.append(InsertOne(d))  # adds `_id` to dict

#         foo.bulk_write(ops, self._sample_collection, ordered=False)

#         for sample, d in zip(samples, dicts):
#             doc = self._sample_dict_to_doc(d)
#             sample._set_backing_doc(doc, dataset=self)

#             if self.media_type == fom.VIDEO:
#                 sample.frames.save()

#     def _make_dict(self, sample, include_id=False):
#         d = sample.to_mongo_dict(include_id=include_id)

#         # We omit None here to allow samples with None-valued new fields to
#         # be added without raising nonexistent field errors. This is safe
#         # because None and missing are equivalent in our data model
#         return {k: v for k, v in d.items() if v is not None}

#     def _bulk_write(self, ops, frames=False, ordered=False):
#         if frames:
#             coll = self._frame_collection
#         else:
#             coll = self._sample_collection

#         foo.bulk_write(ops, coll, ordered=ordered)

#         if frames:
#             fofr.Frame._reload_docs(self._frame_collection_name)
#         else:
#             fos.Sample._reload_docs(self._sample_collection_name)

#     def _merge_doc(
#         self,
#         doc,
#         fields=None,
#         omit_fields=None,
#         expand_schema=True,
#         merge_info=True,
#         overwrite_info=False,
#     ):
#         if fields is not None:
#             if etau.is_str(fields):
#                 fields = [fields]
#             elif not isinstance(fields, dict):
#                 fields = list(fields)

#         if omit_fields is not None:
#             if etau.is_str(omit_fields):
#                 omit_fields = [omit_fields]
#             else:
#                 omit_fields = list(omit_fields)

#         _merge_dataset_doc(
#             self,
#             doc,
#             fields=fields,
#             omit_fields=omit_fields,
#             expand_schema=expand_schema,
#             merge_info=merge_info,
#             overwrite_info=overwrite_info,
#         )

#     def merge_samples(
#         self,
#         samples,
#         key_field="filepath",
#         key_fcn=None,
#         skip_existing=False,
#         insert_new=True,
#         fields=None,
#         omit_fields=None,
#         merge_lists=True,
#         overwrite=True,
#         expand_schema=True,
#         include_info=True,
#         overwrite_info=False,
#         num_samples=None,
#     ):
#         """Merges the given samples into this dataset.

#         By default, samples with the same absolute ``filepath`` are merged, but
#         you can customize this behavior via the ``key_field`` and ``key_fcn``
#         parameters. For example, you could set
#         ``key_fcn = lambda sample: os.path.basename(sample.filepath)`` to merge
#         samples with the same base filename.

#         The behavior of this method is highly customizable. By default, all
#         top-level fields from the provided samples are merged in, overwriting
#         any existing values for those fields, with the exception of list fields
#         (e.g., ``tags``) and label list fields (e.g.,
#         :class:`fiftyone.core.labels.Detections` fields), in which case the
#         elements of the lists themselves are merged. In the case of label list
#         fields, labels with the same ``id`` in both collections are updated
#         rather than duplicated.

#         To avoid confusion between missing fields and fields whose value is
#         ``None``, ``None``-valued fields are always treated as missing while
#         merging.

#         This method can be configured in numerous ways, including:

#         -   Whether existing samples should be modified or skipped
#         -   Whether new samples should be added or omitted
#         -   Whether new fields can be added to the dataset schema
#         -   Whether list fields should be treated as ordinary fields and merged
#             as a whole rather than merging their elements
#         -   Whether to merge only specific fields, or all but certain fields
#         -   Mapping input fields to different field names of this dataset

#         Args:
#             samples: a :class:`fiftyone.core.collections.SampleCollection` or
#                 iterable of :class:`fiftyone.core.sample.Sample` instances
#             key_field ("filepath"): the sample field to use to decide whether
#                 to join with an existing sample
#             key_fcn (None): a function that accepts a
#                 :class:`fiftyone.core.sample.Sample` instance and computes a
#                 key to decide if two samples should be merged. If a ``key_fcn``
#                 is provided, ``key_field`` is ignored
#             skip_existing (False): whether to skip existing samples (True) or
#                 merge them (False)
#             insert_new (True): whether to insert new samples (True) or skip
#                 them (False)
#             fields (None): an optional field or iterable of fields to which to
#                 restrict the merge. If provided, fields other than these are
#                 omitted from ``samples`` when merging or adding samples. One
#                 exception is that ``filepath`` is always included when adding
#                 new samples, since the field is required. This can also be a
#                 dict mapping field names of the input collection to field names
#                 of this dataset
#             omit_fields (None): an optional field or iterable of fields to
#                 exclude from the merge. If provided, these fields are omitted
#                 from ``samples``, if present, when merging or adding samples.
#                 One exception is that ``filepath`` is always included when
#                 adding new samples, since the field is required
#             merge_lists (True): whether to merge the elements of list fields
#                 (e.g., ``tags``) and label list fields (e.g.,
#                 :class:`fiftyone.core.labels.Detections` fields) rather than
#                 merging the entire top-level field like other field types.
#                 For label lists fields, existing
#                 :class:`fiftyone.core.label.Label` elements are either replaced
#                 (when ``overwrite`` is True) or kept (when ``overwrite`` is
#                 False) when their ``id`` matches a label from the provided
#                 samples
#             overwrite (True): whether to overwrite (True) or skip (False)
#                 existing fields and label elements
#             expand_schema (True): whether to dynamically add new fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             include_info (True): whether to merge dataset-level information
#                 such as ``info`` and ``classes``. Only applicable when
#                 ``samples`` is a
#                 :class:`fiftyone.core.collections.SampleCollection`
#             overwrite_info (False): whether to overwrite existing dataset-level
#                 information. Only applicable when ``samples`` is a
#                 :class:`fiftyone.core.collections.SampleCollection` and
#                 ``include_info`` is True
#             num_samples (None): the number of samples in ``samples``. If not
#                 provided, this is computed via ``len(samples)``, if possible.
#                 This value is optional and is used only for progress tracking
#         """
#         if fields is not None:
#             if etau.is_str(fields):
#                 fields = [fields]
#             elif not isinstance(fields, dict):
#                 fields = list(fields)

#         if omit_fields is not None:
#             if etau.is_str(omit_fields):
#                 omit_fields = [omit_fields]
#             else:
#                 omit_fields = list(omit_fields)

#         if isinstance(samples, foc.SampleCollection):
#             _merge_dataset_doc(
#                 self,
#                 samples,
#                 fields=fields,
#                 omit_fields=omit_fields,
#                 expand_schema=expand_schema,
#                 merge_info=include_info,
#                 overwrite_info=overwrite_info,
#             )

#             expand_schema = False

#         # If we're merging a collection, use aggregation pipelines
#         if isinstance(samples, foc.SampleCollection) and key_fcn is None:
#             _merge_samples_pipeline(
#                 samples,
#                 self,
#                 key_field,
#                 skip_existing=skip_existing,
#                 insert_new=insert_new,
#                 fields=fields,
#                 omit_fields=omit_fields,
#                 merge_lists=merge_lists,
#                 overwrite=overwrite,
#             )
#             return

#         #
#         # If we're not merging a collection but the merge key is a field, it's
#         # faster to import into a temporary dataset and then do a merge that
#         # leverages aggregation pipelines, because this avoids the need to
#         # load samples from `self` into memory
#         #

#         if key_fcn is None:
#             tmp = Dataset()
#             tmp.add_samples(samples, num_samples=num_samples)

#             self.merge_samples(
#                 tmp,
#                 key_field=key_field,
#                 skip_existing=skip_existing,
#                 insert_new=insert_new,
#                 fields=fields,
#                 omit_fields=omit_fields,
#                 merge_lists=merge_lists,
#                 overwrite=overwrite,
#                 expand_schema=expand_schema,
#                 include_info=False,
#             )
#             tmp.delete()

#             return

#         _merge_samples_python(
#             self,
#             samples,
#             key_field=key_field,
#             key_fcn=key_fcn,
#             skip_existing=skip_existing,
#             insert_new=insert_new,
#             fields=fields,
#             omit_fields=omit_fields,
#             merge_lists=merge_lists,
#             overwrite=overwrite,
#             expand_schema=expand_schema,
#             num_samples=num_samples,
#         )

#     def delete_samples(self, samples_or_ids):
#         """Deletes the given sample(s) from the dataset.

#         If reference to a sample exists in memory, the sample will be updated
#         such that ``sample.in_dataset`` is False.

#         Args:
#             samples_or_ids: the sample(s) to delete. Can be any of the
#                 following:

#                 -   a sample ID
#                 -   an iterable of sample IDs
#                 -   a :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView`
#                 -   an iterable of :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView` instances
#                 -   a :class:`fiftyone.core.collections.SampleCollection`
#         """
#         sample_ids = _get_sample_ids(samples_or_ids)
#         self._clear(sample_ids=sample_ids)

#     def delete_frames(self, frames_or_ids):
#         """Deletes the given frames(s) from the dataset.

#         If reference to a frame exists in memory, the frame will be updated
#         such that ``frame.in_dataset`` is False.

#         Args:
#             frames_or_ids: the frame(s) to delete. Can be any of the following:

#                 -   a frame ID
#                 -   an iterable of frame IDs
#                 -   a :class:`fiftyone.core.frame.Frame` or
#                     :class:`fiftyone.core.frame.FrameView`
#                 -   a :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView` whose frames to
#                     delete
#                 -   an iterable of :class:`fiftyone.core.frame.Frame` or
#                     :class:`fiftyone.core.frame.FrameView` instances
#                 -   an iterable of :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView` instances whose
#                     frames to delete
#                 -   a :class:`fiftyone.core.collections.SampleCollection` whose
#                     frames to delete
#         """
#         frame_ids = _get_frame_ids(frames_or_ids)
#         self._clear_frames(frame_ids=frame_ids)

#     def delete_labels(
#         self, labels=None, ids=None, tags=None, view=None, fields=None
#     ):
#         """Deletes the specified labels from the dataset.

#         You can specify the labels to delete via any of the following methods:

#         -   Provide the ``labels`` argument, which should contain a list of
#             dicts in the format returned by
#             :meth:`fiftyone.core.session.Session.selected_labels`

#         -   Provide the ``ids`` or ``tags`` arguments to specify the labels to
#             delete via their IDs and/or tags

#         -   Provide the ``view`` argument to delete all of the labels in a view
#             into this dataset. This syntax is useful if you have constructed a
#             :class:`fiftyone.core.view.DatasetView` defining the labels to
#             delete

#         Additionally, you can specify the ``fields`` argument to restrict
#         deletion to specific field(s), either for efficiency or to ensure that
#         labels from other fields are not deleted if their contents are included
#         in the other arguments.

#         Args:
#             labels (None): a list of dicts specifying the labels to delete in
#                 the format returned by
#                 :meth:`fiftyone.core.session.Session.selected_labels`
#             ids (None): an ID or iterable of IDs of the labels to delete
#             tags (None): a tag or iterable of tags of the labels to delete
#             view (None): a :class:`fiftyone.core.view.DatasetView` into this
#                 dataset containing the labels to delete
#             fields (None): a field or iterable of fields from which to delete
#                 labels
#         """
#         if labels is not None:
#             self._delete_labels(labels, fields=fields)

#         if ids is None and tags is None and view is None:
#             return

#         if view is not None and view._dataset is not self:
#             raise ValueError("`view` must be a view into the same dataset")

#         if etau.is_str(ids):
#             ids = [ids]

#         if ids is not None:
#             ids = [ObjectId(_id) for _id in ids]

#         if etau.is_str(tags):
#             tags = [tags]

#         if fields is None:
#             fields = self._get_label_fields()
#         elif etau.is_str(fields):
#             fields = [fields]

#         sample_ops = []
#         frame_ops = []
#         for field in fields:
#             if view is not None:
#                 _, id_path = view._get_label_field_path(field, "_id")
#                 view_ids = view.values(id_path, unwind=True)
#             else:
#                 view_ids = None

#             label_type = self._get_label_field_type(field)
#             field, is_frame_field = self._handle_frame_field(field)

#             ops = []
#             if issubclass(label_type, fol._LABEL_LIST_FIELDS):
#                 array_field = field + "." + label_type._LABEL_LIST_FIELD

#                 if view_ids is not None:
#                     ops.append(
#                         UpdateMany(
#                             {},
#                             {
#                                 "$pull": {
#                                     array_field: {"_id": {"$in": view_ids}}
#                                 }
#                             },
#                         )
#                     )

#                 if ids is not None:
#                     ops.append(
#                         UpdateMany(
#                             {}, {"$pull": {array_field: {"_id": {"$in": ids}}}}
#                         )
#                     )

#                 if tags is not None:
#                     ops.append(
#                         UpdateMany(
#                             {},
#                             {
#                                 "$pull": {
#                                     array_field: {
#                                         "tags": {"$elemMatch": {"$in": tags}}
#                                     }
#                                 }
#                             },
#                         )
#                     )
#             else:
#                 if view_ids is not None:
#                     ops.append(
#                         UpdateMany(
#                             {field + "._id": {"$in": view_ids}},
#                             {"$set": {field: None}},
#                         )
#                     )

#                 if ids is not None:
#                     ops.append(
#                         UpdateMany(
#                             {field + "._id": {"$in": ids}},
#                             {"$set": {field: None}},
#                         )
#                     )

#                 if tags is not None:
#                     ops.append(
#                         UpdateMany(
#                             {field + ".tags": {"$elemMatch": {"$in": tags}}},
#                             {"$set": {field: None}},
#                         )
#                     )

#             if is_frame_field:
#                 frame_ops.extend(ops)
#             else:
#                 sample_ops.extend(ops)

#         if sample_ops:
#             foo.bulk_write(sample_ops, self._sample_collection)
#             fos.Sample._reload_docs(self._sample_collection_name)

#         if frame_ops:
#             foo.bulk_write(frame_ops, self._frame_collection)
#             fofr.Frame._reload_docs(self._frame_collection_name)

#     def _delete_labels(self, labels, fields=None):
#         if etau.is_str(fields):
#             fields = [fields]

#         # Partition labels by field
#         sample_ids = set()
#         labels_map = defaultdict(list)
#         for l in labels:
#             sample_ids.add(l["sample_id"])
#             labels_map[l["field"]].append(l)

#         sample_ops = []
#         frame_ops = []
#         for field, field_labels in labels_map.items():
#             if fields is not None and field not in fields:
#                 continue

#             label_type = self._get_label_field_type(field)
#             field, is_frame_field = self._handle_frame_field(field)

#             if is_frame_field:
#                 # Partition by (sample ID, frame number)
#                 _labels_map = defaultdict(list)
#                 for l in field_labels:
#                     _labels_map[(l["sample_id"], l["frame_number"])].append(
#                         ObjectId(l["label_id"])
#                     )

#                 if issubclass(label_type, fol._LABEL_LIST_FIELDS):
#                     array_field = field + "." + label_type._LABEL_LIST_FIELD

#                     for (
#                         (sample_id, frame_number),
#                         label_ids,
#                     ) in _labels_map.items():
#                         frame_ops.append(
#                             UpdateOne(
#                                 {
#                                     "_sample_id": ObjectId(sample_id),
#                                     "frame_number": frame_number,
#                                 },
#                                 {
#                                     "$pull": {
#                                         array_field: {
#                                             "_id": {"$in": label_ids}
#                                         }
#                                     }
#                                 },
#                             )
#                         )
#                 else:
#                     for (
#                         (sample_id, frame_number),
#                         label_ids,
#                     ) in _labels_map.items():
#                         # If the data is well-formed, `label_ids` should have
#                         # exactly one element, and this is redundant anyhow
#                         # since `sample_id` should uniquely define the label to
#                         # delete, but we still include `label_id` in the query
#                         # just to be safe
#                         for label_id in label_ids:
#                             frame_ops.append(
#                                 UpdateOne(
#                                     {
#                                         "_sample_id": ObjectId(sample_id),
#                                         "frame_number": frame_number,
#                                         field + "._id": label_id,
#                                     },
#                                     {"$set": {field: None}},
#                                 )
#                             )
#             else:
#                 # Partition by sample ID
#                 _labels_map = defaultdict(list)
#                 for l in field_labels:
#                     _labels_map[l["sample_id"]].append(ObjectId(l["label_id"]))

#                 if issubclass(label_type, fol._LABEL_LIST_FIELDS):
#                     array_field = field + "." + label_type._LABEL_LIST_FIELD

#                     for sample_id, label_ids in _labels_map.items():
#                         sample_ops.append(
#                             UpdateOne(
#                                 {"_id": ObjectId(sample_id)},
#                                 {
#                                     "$pull": {
#                                         array_field: {
#                                             "_id": {"$in": label_ids}
#                                         }
#                                     }
#                                 },
#                             )
#                         )
#                 else:
#                     for sample_id, label_ids in _labels_map.items():
#                         # If the data is well-formed, `label_ids` should have
#                         # exactly one element, and this is redundant anyhow
#                         # since `sample_id` and `frame_number` should uniquely
#                         # define the label to delete, but we still include
#                         # `label_id` in the query just to be safe
#                         for label_id in label_ids:
#                             sample_ops.append(
#                                 UpdateOne(
#                                     {
#                                         "_id": ObjectId(sample_id),
#                                         field + "._id": label_id,
#                                     },
#                                     {"$set": {field: None}},
#                                 )
#                             )

#         if sample_ops:
#             foo.bulk_write(sample_ops, self._sample_collection)

#             fos.Sample._reload_docs(
#                 self._sample_collection_name, sample_ids=sample_ids
#             )

#         if frame_ops:
#             foo.bulk_write(frame_ops, self._frame_collection)

#             # pylint: disable=unexpected-keyword-arg
#             fofr.Frame._reload_docs(
#                 self._frame_collection_name, sample_ids=sample_ids
#             )

#     @deprecated(reason="Use delete_samples() instead")
#     def remove_sample(self, sample_or_id):
#         """Removes the given sample from the dataset.

#         If reference to a sample exists in memory, the sample will be updated
#         such that ``sample.in_dataset`` is False.

#         .. warning::

#             This method is deprecated and will be removed in a future release.
#             Use the drop-in replacement :meth:`delete_samples` instead.

#         Args:
#             sample_or_id: the sample to remove. Can be any of the following:

#                 -   a sample ID
#                 -   a :class:`fiftyone.core.sample.Sample`
#                 -   a :class:`fiftyone.core.sample.SampleView`
#         """
#         self.delete_samples(sample_or_id)

#     @deprecated(reason="Use delete_samples() instead")
#     def remove_samples(self, samples_or_ids):
#         """Removes the given samples from the dataset.

#         If reference to a sample exists in memory, the sample will be updated
#         such that ``sample.in_dataset`` is False.

#         .. warning::

#             This method is deprecated and will be removed in a future release.
#             Use the drop-in replacement :meth:`delete_samples` instead.

#         Args:
#             samples_or_ids: the samples to remove. Can be any of the following:

#                 -   a sample ID
#                 -   an iterable of sample IDs
#                 -   a :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView`
#                 -   an iterable of :class:`fiftyone.core.sample.Sample` or
#                     :class:`fiftyone.core.sample.SampleView` instances
#                 -   a :class:`fiftyone.core.collections.SampleCollection`
#         """
#         self.delete_samples(samples_or_ids)

#     def save(self):
#         """Saves the dataset to the database.

#         This only needs to be called when dataset-level information such as its
#         :meth:`Dataset.info` is modified.
#         """
#         self._save()

#     def _save(self, view=None, fields=None):
#         if view is not None:
#             _save_view(view, fields=fields)

#         self._doc.save()

#     def clone(self, name=None):
#         """Creates a clone of the dataset containing deep copies of all samples
#         and dataset-level information in this dataset.

#         Args:
#             name (None): a name for the cloned dataset. By default,
#                 :func:`get_default_dataset_name` is used

#         Returns:
#             the new :class:`Dataset`
#         """
#         return self._clone(name=name)

#     def _clone(self, name=None, view=None):
#         if name is None:
#             name = get_default_dataset_name()

#         if view is not None:
#             sample_collection = view
#         else:
#             sample_collection = self

#         return _clone_dataset_or_view(sample_collection, name)

#     def clear(self):
#         """Removes all samples from the dataset.

#         If reference to a sample exists in memory, the sample will be updated
#         such that ``sample.in_dataset`` is False.
#         """
#         self._clear()

#     def _clear(self, view=None, sample_ids=None):
#         if view is not None:
#             sample_ids = view.values("id")

#         if sample_ids is not None:
#             d = {"_id": {"$in": [ObjectId(_id) for _id in sample_ids]}}
#         else:
#             d = {}

#         self._sample_collection.delete_many(d)
#         fos.Sample._reset_docs(
#             self._sample_collection_name, sample_ids=sample_ids
#         )

#         self._clear_frames(sample_ids=sample_ids)

#     def _keep(self, view=None, sample_ids=None):
#         if view is not None:
#             clear_view = self.exclude(view)
#         else:
#             clear_view = self.exclude(sample_ids)

#         self._clear(view=clear_view)

#     def _keep_fields(self, view=None):
#         if view is None:
#             return

#         del_sample_fields = view._get_missing_fields()
#         if del_sample_fields:
#             self.delete_sample_fields(del_sample_fields)

#         if self.media_type == fom.VIDEO:
#             del_frame_fields = view._get_missing_fields(frames=True)
#             if del_frame_fields:
#                 self.delete_frame_fields(del_frame_fields)

#     def clear_frames(self):
#         """Removes all frame labels from the video dataset.

#         If reference to a frame exists in memory, the frame will be updated
#         such that ``frame.in_dataset`` is False.
#         """
#         self._clear_frames()

#     def _clear_frames(self, view=None, sample_ids=None, frame_ids=None):
#         if self.media_type != fom.VIDEO:
#             return

#         if self._is_clips:
#             if sample_ids is not None:
#                 view = self.select(sample_ids)
#             elif frame_ids is None and view is None:
#                 view = self

#             if view is not None:
#                 frame_ids = view.values("frames.id", unwind=True)

#         if frame_ids is not None:
#             self._frame_collection.delete_many(
#                 {"_id": {"$in": [ObjectId(_id) for _id in frame_ids]}}
#             )
#             fofr.Frame._reset_docs_by_frame_id(
#                 self._frame_collection_name, frame_ids
#             )
#             return

#         if view is not None:
#             sample_ids = view.values("id")

#         if sample_ids is not None:
#             d = {"_sample_id": {"$in": [ObjectId(_id) for _id in sample_ids]}}
#         else:
#             d = {}

#         self._frame_collection.delete_many(d)
#         fofr.Frame._reset_docs(
#             self._frame_collection_name, sample_ids=sample_ids
#         )

#     def _keep_frames(self, view=None, frame_ids=None):
#         if self.media_type != fom.VIDEO:
#             return

#         if self._is_clips:
#             if frame_ids is None and view is None:
#                 view = self

#             if view is not None:
#                 frame_ids = view.values("frames.id", unwind=True)

#         if frame_ids is not None:
#             self._frame_collection.delete_many(
#                 {
#                     "_id": {
#                         "$not": {"$in": [ObjectId(_id) for _id in frame_ids]}
#                     }
#                 }
#             )
#             fofr.Frame._reset_docs_by_frame_id(
#                 self._frame_collection_name, frame_ids, keep=True
#             )
#             return

#         if view is None:
#             return

#         sample_ids, frame_numbers = view.values(["id", "frames.frame_number"])

#         ops = []
#         for sample_id, fns in zip(sample_ids, frame_numbers):
#             ops.append(
#                 DeleteMany(
#                     {
#                         "_sample_id": ObjectId(sample_id),
#                         "frame_number": {"$not": {"$in": fns}},
#                     }
#                 )
#             )

#         if not ops:
#             return

#         foo.bulk_write(ops, self._frame_collection)
#         for sample_id, fns in zip(sample_ids, frame_numbers):
#             fofr.Frame._reset_docs_for_sample(
#                 self._frame_collection_name, sample_id, fns, keep=True
#             )

#     def ensure_frames(self):
#         """Ensures that the video dataset contains frame instances for every
#         frame of each sample's source video.

#         Empty frames will be inserted for missing frames, and already existing
#         frames are left unchanged.
#         """
#         self._ensure_frames()

#     def _ensure_frames(self, view=None):
#         if self.media_type != fom.VIDEO:
#             return

#         if view is not None:
#             sample_collection = view
#         else:
#             sample_collection = self

#         sample_collection.compute_metadata()

#         pipeline = sample_collection._pipeline()
#         pipeline.extend(
#             [
#                 {
#                     "$project": {
#                         "_id": False,
#                         "_sample_id": "$_id",
#                         "frame_number": {
#                             "$range": [
#                                 1,
#                                 {"$add": ["$metadata.total_frame_count", 1]},
#                             ]
#                         },
#                     }
#                 },
#                 {"$unwind": "$frame_number"},
#                 {
#                     "$merge": {
#                         "into": self._frame_collection_name,
#                         "on": ["_sample_id", "frame_number"],
#                         "whenMatched": "keepExisting",
#                         "whenNotMatched": "insert",
#                     }
#                 },
#             ]
#         )

#         self._aggregate(pipeline=pipeline)

#     def delete(self):
#         """Deletes the dataset.

#         Once deleted, only the ``name`` and ``deleted`` attributes of a dataset
#         may be accessed.

#         If reference to a sample exists in memory, the sample will be updated
#         such that ``sample.in_dataset`` is False.
#         """
#         self._sample_collection.drop()
#         fos.Sample._reset_docs(self._sample_collection_name)

#         # Clips datasets directly inherit frames from source dataset
#         if not self._is_clips:
#             self._frame_collection.drop()
#             fofr.Frame._reset_docs(self._frame_collection_name)

#         # Update singleton
#         self._instances.pop(self._doc.name, None)

#         _delete_dataset_doc(self._doc)
#         self._deleted = True

#     def add_dir(
#         self,
#         dataset_dir=None,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#         add_info=True,
#         **kwargs,
#     ):
#         """Adds the contents of the given directory to the dataset.

#         You can perform imports with this method via the following basic
#         patterns:

#         (a) Provide ``dataset_dir`` and ``dataset_type`` to import the contents
#             of a directory that is organized in the default layout for the
#             dataset type as documented in
#             :ref:`this guide <loading-datasets-from-disk>`

#         (b) Provide ``dataset_type`` along with ``data_path``, ``labels_path``,
#             or other type-specific parameters to perform a customized import.
#             This syntax provides the flexibility to, for example, perform
#             labels-only imports or imports where the source media lies in a
#             different location than the labels

#         In either workflow, the remaining parameters of this method can be
#         provided to further configure the import.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         Args:
#             dataset_dir (None): the dataset directory. This can be omitted for
#                 certain dataset formats if you provide arguments such as
#                 ``data_path`` and ``labels_path``
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``export_dir`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``dataset_dir`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``dataset_dir`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``dataset_dir`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in ``dataset_dir``
#                     of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``dataset_dir`` has no effect on the
#                     location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``dataset_dir`` of the labels for the default layout of the
#                 dataset type being imported
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer (if
#                 any) to the dataset's ``info``
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         dataset_importer, _ = foud.build_dataset_importer(
#             dataset_type,
#             dataset_dir=dataset_dir,
#             data_path=data_path,
#             labels_path=labels_path,
#             name=self.name,
#             **kwargs,
#         )

#         return self.add_importer(
#             dataset_importer,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#             add_info=add_info,
#         )

#     def merge_dir(
#         self,
#         dataset_dir=None,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         label_field=None,
#         tags=None,
#         key_field="filepath",
#         key_fcn=None,
#         skip_existing=False,
#         insert_new=True,
#         fields=None,
#         omit_fields=None,
#         merge_lists=True,
#         overwrite=True,
#         expand_schema=True,
#         add_info=True,
#         **kwargs,
#     ):
#         """Merges the contents of the given directory into the dataset.

#         You can perform imports with this method via the following basic
#         patterns:

#         (a) Provide ``dataset_dir`` and ``dataset_type`` to import the contents
#             of a directory that is organized in the default layout for the
#             dataset type as documented in
#             :ref:`this guide <loading-datasets-from-disk>`

#         (b) Provide ``dataset_type`` along with ``data_path``, ``labels_path``,
#             or other type-specific parameters to perform a customized import.
#             This syntax provides the flexibility to, for example, perform
#             labels-only imports or imports where the source media lies in a
#             different location than the labels

#         In either workflow, the remaining parameters of this method can be
#         provided to further configure the import.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         By default, samples with the same absolute ``filepath`` are merged, but
#         you can customize this behavior via the ``key_field`` and ``key_fcn``
#         parameters. For example, you could set
#         ``key_fcn = lambda sample: os.path.basename(sample.filepath)`` to merge
#         samples with the same base filename.

#         The behavior of this method is highly customizable. By default, all
#         top-level fields from the imported samples are merged in, overwriting
#         any existing values for those fields, with the exception of list fields
#         (e.g., ``tags``) and label list fields (e.g.,
#         :class:`fiftyone.core.labels.Detections` fields), in which case the
#         elements of the lists themselves are merged. In the case of label list
#         fields, labels with the same ``id`` in both collections are updated
#         rather than duplicated.

#         To avoid confusion between missing fields and fields whose value is
#         ``None``, ``None``-valued fields are always treated as missing while
#         merging.

#         This method can be configured in numerous ways, including:

#         -   Whether existing samples should be modified or skipped
#         -   Whether new samples should be added or omitted
#         -   Whether new fields can be added to the dataset schema
#         -   Whether list fields should be treated as ordinary fields and merged
#             as a whole rather than merging their elements
#         -   Whether to merge only specific fields, or all but certain fields
#         -   Mapping input fields to different field names of this dataset

#         Args:
#             dataset_dir (None): the dataset directory. This can be omitted for
#                 certain dataset formats if you provide arguments such as
#                 ``data_path`` and ``labels_path``
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``export_dir`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``dataset_dir`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``dataset_dir`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``dataset_dir`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in ``dataset_dir``
#                     of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``dataset_dir`` has no effect on the
#                     location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``dataset_dir`` of the labels for the default layout of the
#                 dataset type being imported
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             key_field ("filepath"): the sample field to use to decide whether
#                 to join with an existing sample
#             key_fcn (None): a function that accepts a
#                 :class:`fiftyone.core.sample.Sample` instance and computes a
#                 key to decide if two samples should be merged. If a ``key_fcn``
#                 is provided, ``key_field`` is ignored
#             skip_existing (False): whether to skip existing samples (True) or
#                 merge them (False)
#             insert_new (True): whether to insert new samples (True) or skip
#                 them (False)
#             fields (None): an optional field or iterable of fields to which to
#                 restrict the merge. If provided, fields other than these are
#                 omitted from ``samples`` when merging or adding samples. One
#                 exception is that ``filepath`` is always included when adding
#                 new samples, since the field is required. This can also be a
#                 dict mapping field names of the input collection to field names
#                 of this dataset
#             omit_fields (None): an optional field or iterable of fields to
#                 exclude from the merge. If provided, these fields are omitted
#                 from imported samples, if present. One exception is that
#                 ``filepath`` is always included when adding new samples, since
#                 the field is required
#             merge_lists (True): whether to merge the elements of list fields
#                 (e.g., ``tags``) and label list fields (e.g.,
#                 :class:`fiftyone.core.labels.Detections` fields) rather than
#                 merging the entire top-level field like other field types. For
#                 label lists fields, existing :class:`fiftyone.core.label.Label`
#                 elements are either replaced (when ``overwrite`` is True) or
#                 kept (when ``overwrite`` is False) when their ``id`` matches a
#                 label from the provided samples
#             overwrite (True): whether to overwrite (True) or skip (False)
#                 existing fields and label elements
#             expand_schema (True): whether to dynamically add new fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer
#                 (if any) to the dataset
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``
#         """
#         dataset_importer, _ = foud.build_dataset_importer(
#             dataset_type,
#             dataset_dir=dataset_dir,
#             data_path=data_path,
#             labels_path=labels_path,
#             name=self.name,
#             **kwargs,
#         )

#         return self.merge_importer(
#             dataset_importer,
#             label_field=label_field,
#             tags=tags,
#             key_field=key_field,
#             key_fcn=key_fcn,
#             skip_existing=skip_existing,
#             insert_new=insert_new,
#             fields=fields,
#             omit_fields=omit_fields,
#             merge_lists=merge_lists,
#             overwrite=overwrite,
#             expand_schema=expand_schema,
#             add_info=add_info,
#         )

#     def add_archive(
#         self,
#         archive_path,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#         add_info=True,
#         cleanup=True,
#         **kwargs,
#     ):
#         """Adds the contents of the given archive to the dataset.

#         If a directory with the same root name as ``archive_path`` exists, it
#         is assumed that this directory contains the extracted contents of the
#         archive, and thus the archive is not re-extracted.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         .. note::

#             The following archive formats are explicitly supported::

#                 .zip, .tar, .tar.gz, .tgz, .tar.bz, .tbz

#             If an archive *not* in the above list is found, extraction will be
#             attempted via the ``patool`` package, which supports many formats
#             but may require that additional system packages be installed.

#         Args:
#             archive_path: the path to an archive of a dataset directory
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset in ``archive_path``
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``archive_path`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``archive_path`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``archive_path`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``archive_path`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in
#                     ``archive_path`` of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``archive_path`` has no effect on
#                     the location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``archive_path`` of the labels for the default layout of the
#                 dataset type being imported
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer (if
#                 any) to the dataset's ``info``
#             cleanup (True): whether to delete the archive after extracting it
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         dataset_dir = _extract_archive_if_necessary(archive_path, cleanup)
#         return self.add_dir(
#             dataset_dir=dataset_dir,
#             dataset_type=dataset_type,
#             data_path=data_path,
#             labels_path=labels_path,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#             add_info=add_info,
#             **kwargs,
#         )

#     def merge_archive(
#         self,
#         archive_path,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         label_field=None,
#         tags=None,
#         key_field="filepath",
#         key_fcn=None,
#         skip_existing=False,
#         insert_new=True,
#         fields=None,
#         omit_fields=None,
#         merge_lists=True,
#         overwrite=True,
#         expand_schema=True,
#         add_info=True,
#         cleanup=True,
#         **kwargs,
#     ):
#         """Merges the contents of the given archive into the dataset.

#         If a directory with the same root name as ``archive_path`` exists, it
#         is assumed that this directory contains the extracted contents of the
#         archive, and thus the archive is not re-extracted.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         .. note::

#             The following archive formats are explicitly supported::

#                 .zip, .tar, .tar.gz, .tgz, .tar.bz, .tbz

#             If an archive *not* in the above list is found, extraction will be
#             attempted via the ``patool`` package, which supports many formats
#             but may require that additional system packages be installed.

#         By default, samples with the same absolute ``filepath`` are merged, but
#         you can customize this behavior via the ``key_field`` and ``key_fcn``
#         parameters. For example, you could set
#         ``key_fcn = lambda sample: os.path.basename(sample.filepath)`` to merge
#         samples with the same base filename.

#         The behavior of this method is highly customizable. By default, all
#         top-level fields from the imported samples are merged in, overwriting
#         any existing values for those fields, with the exception of list fields
#         (e.g., ``tags``) and label list fields (e.g.,
#         :class:`fiftyone.core.labels.Detections` fields), in which case the
#         elements of the lists themselves are merged. In the case of label list
#         fields, labels with the same ``id`` in both collections are updated
#         rather than duplicated.

#         To avoid confusion between missing fields and fields whose value is
#         ``None``, ``None``-valued fields are always treated as missing while
#         merging.

#         This method can be configured in numerous ways, including:

#         -   Whether existing samples should be modified or skipped
#         -   Whether new samples should be added or omitted
#         -   Whether new fields can be added to the dataset schema
#         -   Whether list fields should be treated as ordinary fields and merged
#             as a whole rather than merging their elements
#         -   Whether to merge only specific fields, or all but certain fields
#         -   Mapping input fields to different field names of this dataset

#         Args:
#             archive_path: the path to an archive of a dataset directory
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset in ``archive_path``
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``archive_path`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``archive_path`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``archive_path`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``archive_path`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in
#                     ``archive_path`` of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``archive_path`` has no effect on
#                     the location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``archive_path`` of the labels for the default layout of the
#                 dataset type being imported
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             key_field ("filepath"): the sample field to use to decide whether
#                 to join with an existing sample
#             key_fcn (None): a function that accepts a
#                 :class:`fiftyone.core.sample.Sample` instance and computes a
#                 key to decide if two samples should be merged. If a ``key_fcn``
#                 is provided, ``key_field`` is ignored
#             skip_existing (False): whether to skip existing samples (True) or
#                 merge them (False)
#             insert_new (True): whether to insert new samples (True) or skip
#                 them (False)
#             fields (None): an optional field or iterable of fields to which to
#                 restrict the merge. If provided, fields other than these are
#                 omitted from ``samples`` when merging or adding samples. One
#                 exception is that ``filepath`` is always included when adding
#                 new samples, since the field is required. This can also be a
#                 dict mapping field names of the input collection to field names
#                 of this dataset
#             omit_fields (None): an optional field or iterable of fields to
#                 exclude from the merge. If provided, these fields are omitted
#                 from imported samples, if present. One exception is that
#                 ``filepath`` is always included when adding new samples, since
#                 the field is required
#             merge_lists (True): whether to merge the elements of list fields
#                 (e.g., ``tags``) and label list fields (e.g.,
#                 :class:`fiftyone.core.labels.Detections` fields) rather than
#                 merging the entire top-level field like other field types. For
#                 label lists fields, existing :class:`fiftyone.core.label.Label`
#                 elements are either replaced (when ``overwrite`` is True) or
#                 kept (when ``overwrite`` is False) when their ``id`` matches a
#                 label from the provided samples
#             overwrite (True): whether to overwrite (True) or skip (False)
#                 existing fields and label elements
#             expand_schema (True): whether to dynamically add new fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer
#                 (if any) to the dataset
#             cleanup (True): whether to delete the archive after extracting it
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``
#         """
#         dataset_dir = _extract_archive_if_necessary(archive_path, cleanup)
#         return self.merge_dir(
#             dataset_dir=dataset_dir,
#             dataset_type=dataset_type,
#             data_path=data_path,
#             labels_path=labels_path,
#             label_field=label_field,
#             tags=tags,
#             key_field=key_field,
#             key_fcn=key_fcn,
#             skip_existing=skip_existing,
#             insert_new=insert_new,
#             fields=fields,
#             omit_fields=omit_fields,
#             merge_lists=merge_lists,
#             overwrite=overwrite,
#             expand_schema=expand_schema,
#             add_info=add_info,
#             **kwargs,
#         )

#     def add_importer(
#         self,
#         dataset_importer,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#         add_info=True,
#     ):
#         """Adds the samples from the given
#         :class:`fiftyone.utils.data.importers.DatasetImporter` to the dataset.

#         See :ref:`this guide <custom-dataset-importer>` for more details about
#         importing datasets in custom formats by defining your own
#         :class:`DatasetImporter <fiftyone.utils.data.importers.DatasetImporter>`.

#         Args:
#             dataset_importer: a
#                 :class:`fiftyone.utils.data.importers.DatasetImporter`
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer (if
#                 any) to the dataset's ``info``

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         return foud.import_samples(
#             self,
#             dataset_importer,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#             add_info=add_info,
#         )

#     def merge_importer(
#         self,
#         dataset_importer,
#         label_field=None,
#         tags=None,
#         key_field="filepath",
#         key_fcn=None,
#         skip_existing=False,
#         insert_new=True,
#         fields=None,
#         omit_fields=None,
#         merge_lists=True,
#         overwrite=True,
#         expand_schema=True,
#         add_info=True,
#     ):
#         """Merges the samples from the given
#         :class:`fiftyone.utils.data.importers.DatasetImporter` into the
#         dataset.

#         See :ref:`this guide <custom-dataset-importer>` for more details about
#         importing datasets in custom formats by defining your own
#         :class:`DatasetImporter <fiftyone.utils.data.importers.DatasetImporter>`.

#         By default, samples with the same absolute ``filepath`` are merged, but
#         you can customize this behavior via the ``key_field`` and ``key_fcn``
#         parameters. For example, you could set
#         ``key_fcn = lambda sample: os.path.basename(sample.filepath)`` to merge
#         samples with the same base filename.

#         The behavior of this method is highly customizable. By default, all
#         top-level fields from the imported samples are merged in, overwriting
#         any existing values for those fields, with the exception of list fields
#         (e.g., ``tags``) and label list fields (e.g.,
#         :class:`fiftyone.core.labels.Detections` fields), in which case the
#         elements of the lists themselves are merged. In the case of label list
#         fields, labels with the same ``id`` in both collections are updated
#         rather than duplicated.

#         To avoid confusion between missing fields and fields whose value is
#         ``None``, ``None``-valued fields are always treated as missing while
#         merging.

#         This method can be configured in numerous ways, including:

#         -   Whether existing samples should be modified or skipped
#         -   Whether new samples should be added or omitted
#         -   Whether new fields can be added to the dataset schema
#         -   Whether list fields should be treated as ordinary fields and merged
#             as a whole rather than merging their elements
#         -   Whether to merge only specific fields, or all but certain fields
#         -   Mapping input fields to different field names of this dataset

#         Args:
#             dataset_importer: a
#                 :class:`fiftyone.utils.data.importers.DatasetImporter`
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             key_field ("filepath"): the sample field to use to decide whether
#                 to join with an existing sample
#             key_fcn (None): a function that accepts a
#                 :class:`fiftyone.core.sample.Sample` instance and computes a
#                 key to decide if two samples should be merged. If a ``key_fcn``
#                 is provided, ``key_field`` is ignored
#             skip_existing (False): whether to skip existing samples (True) or
#                 merge them (False)
#             insert_new (True): whether to insert new samples (True) or skip
#                 them (False)
#             fields (None): an optional field or iterable of fields to which to
#                 restrict the merge. If provided, fields other than these are
#                 omitted from ``samples`` when merging or adding samples. One
#                 exception is that ``filepath`` is always included when adding
#                 new samples, since the field is required. This can also be a
#                 dict mapping field names of the input collection to field names
#                 of this dataset
#             omit_fields (None): an optional field or iterable of fields to
#                 exclude from the merge. If provided, these fields are omitted
#                 from imported samples, if present. One exception is that
#                 ``filepath`` is always included when adding new samples, since
#                 the field is required
#             merge_lists (True): whether to merge the elements of list fields
#                 (e.g., ``tags``) and label list fields (e.g.,
#                 :class:`fiftyone.core.labels.Detections` fields) rather than
#                 merging the entire top-level field like other field types. For
#                 label lists fields, existing :class:`fiftyone.core.label.Label`
#                 elements are either replaced (when ``overwrite`` is True) or
#                 kept (when ``overwrite`` is False) when their ``id`` matches a
#                 label from the provided samples
#             overwrite (True): whether to overwrite (True) or skip (False)
#                 existing fields and label elements
#             expand_schema (True): whether to dynamically add new fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema
#             add_info (True): whether to add dataset info from the importer
#                 (if any) to the dataset
#         """
#         return foud.merge_samples(
#             self,
#             dataset_importer,
#             label_field=label_field,
#             tags=tags,
#             key_field=key_field,
#             key_fcn=key_fcn,
#             skip_existing=skip_existing,
#             insert_new=insert_new,
#             fields=fields,
#             omit_fields=omit_fields,
#             merge_lists=merge_lists,
#             overwrite=overwrite,
#             expand_schema=expand_schema,
#             add_info=add_info,
#         )

#     def add_images(self, paths_or_samples, sample_parser=None, tags=None):
#         """Adds the given images to the dataset.

#         This operation does not read the images.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         adding images to a dataset by defining your own
#         :class:`UnlabeledImageSampleParser <fiftyone.utils.data.parsers.UnlabeledImageSampleParser>`.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of image paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledImageSampleParser`
#                 instance to use to parse the samples
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         if sample_parser is None:
#             sample_parser = foud.ImageSampleParser()

#         return foud.add_images(
#             self, paths_or_samples, sample_parser, tags=tags
#         )

#     def add_labeled_images(
#         self,
#         samples,
#         sample_parser,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#     ):
#         """Adds the given labeled images to the dataset.

#         This operation will iterate over all provided samples, but the images
#         will not be read (unless the sample parser requires it in order to
#         compute image metadata).

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         adding labeled images to a dataset by defining your own
#         :class:`LabeledImageSampleParser <fiftyone.utils.data.parsers.LabeledImageSampleParser>`.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledImageSampleParser`
#                 instance to use to parse the samples
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. If the parser produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample, this
#                 argument specifies the name of the field to use; the default is
#                 ``"ground_truth"``. If the parser produces a dictionary of
#                 labels per sample, this argument specifies a string prefix to
#                 prepend to each label key; the default in this case is to
#                 directly use the keys of the imported label dictionaries as
#                 field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         return foud.add_labeled_images(
#             self,
#             samples,
#             sample_parser,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#         )

#     def add_images_dir(self, images_dir, tags=None, recursive=True):
#         """Adds the given directory of images to the dataset.

#         See :class:`fiftyone.types.dataset_types.ImageDirectory` for format
#         details. In particular, note that files with non-image MIME types are
#         omitted.

#         This operation does not read the images.

#         Args:
#             images_dir: a directory of images
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             recursive (True): whether to recursively traverse subdirectories

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         image_paths = foud.parse_images_dir(images_dir, recursive=recursive)
#         sample_parser = foud.ImageSampleParser()
#         return self.add_images(image_paths, sample_parser, tags=tags)

#     def add_images_patt(self, images_patt, tags=None):
#         """Adds the given glob pattern of images to the dataset.

#         This operation does not read the images.

#         Args:
#             images_patt: a glob pattern of images like
#                 ``/path/to/images/*.jpg``
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         image_paths = etau.get_glob_matches(images_patt)
#         sample_parser = foud.ImageSampleParser()
#         return self.add_images(image_paths, sample_parser, tags=tags)

#     def ingest_images(
#         self,
#         paths_or_samples,
#         sample_parser=None,
#         tags=None,
#         dataset_dir=None,
#         image_format=None,
#     ):
#         """Ingests the given iterable of images into the dataset.

#         The images are read in-memory and written to ``dataset_dir``.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         ingesting images into a dataset by defining your own
#         :class:`UnlabeledImageSampleParser <fiftyone.utils.data.parsers.UnlabeledImageSampleParser>`.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of image paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledImageSampleParser`
#                 instance to use to parse the samples
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             dataset_dir (None): the directory in which the images will be
#                 written. By default, :func:`get_default_dataset_dir` is used
#             image_format (None): the image format to use to write the images to
#                 disk. By default, ``fiftyone.config.default_image_ext`` is used

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         if sample_parser is None:
#             sample_parser = foud.ImageSampleParser()

#         if dataset_dir is None:
#             dataset_dir = get_default_dataset_dir(self.name)

#         dataset_ingestor = foud.UnlabeledImageDatasetIngestor(
#             dataset_dir,
#             paths_or_samples,
#             sample_parser,
#             image_format=image_format,
#         )

#         return self.add_importer(dataset_ingestor, tags=tags)

#     def ingest_labeled_images(
#         self,
#         samples,
#         sample_parser,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#         dataset_dir=None,
#         image_format=None,
#     ):
#         """Ingests the given iterable of labeled image samples into the
#         dataset.

#         The images are read in-memory and written to ``dataset_dir``.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         ingesting labeled images into a dataset by defining your own
#         :class:`LabeledImageSampleParser <fiftyone.utils.data.parsers.LabeledImageSampleParser>`.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledImageSampleParser`
#                 instance to use to parse the samples
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. If the parser produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample, this
#                 argument specifies the name of the field to use; the default is
#                 ``"ground_truth"``. If the parser produces a dictionary of
#                 labels per sample, this argument specifies a string prefix to
#                 prepend to each label key; the default in this case is to
#                 directly use the keys of the imported label dictionaries as
#                 field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if the sample's schema is not a subset of the dataset schema
#             dataset_dir (None): the directory in which the images will be
#                 written. By default, :func:`get_default_dataset_dir` is used
#             image_format (None): the image format to use to write the images to
#                 disk. By default, ``fiftyone.config.default_image_ext`` is used

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         if dataset_dir is None:
#             dataset_dir = get_default_dataset_dir(self.name)

#         dataset_ingestor = foud.LabeledImageDatasetIngestor(
#             dataset_dir,
#             samples,
#             sample_parser,
#             image_format=image_format,
#         )

#         return self.add_importer(
#             dataset_ingestor,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#         )

#     def add_videos(self, paths_or_samples, sample_parser=None, tags=None):
#         """Adds the given videos to the dataset.

#         This operation does not read the videos.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         adding videos to a dataset by defining your own
#         :class:`UnlabeledVideoSampleParser <fiftyone.utils.data.parsers.UnlabeledVideoSampleParser>`.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of video paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledVideoSampleParser`
#                 instance to use to parse the samples
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         if sample_parser is None:
#             sample_parser = foud.VideoSampleParser()

#         return foud.add_videos(
#             self, paths_or_samples, sample_parser, tags=tags
#         )

#     def add_labeled_videos(
#         self,
#         samples,
#         sample_parser,
#         label_field=None,
#         tags=None,
#         expand_schema=True,
#     ):
#         """Adds the given labeled videos to the dataset.

#         This operation will iterate over all provided samples, but the videos
#         will not be read/decoded/etc.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         adding labeled videos to a dataset by defining your own
#         :class:`LabeledVideoSampleParser <fiftyone.utils.data.parsers.LabeledVideoSampleParser>`.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledVideoSampleParser`
#                 instance to use to parse the samples
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. If the parser produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the parser produces a
#                 dictionary of labels per sample/frame, this argument specifies
#                 a string prefix to prepend to each label key; the default in
#                 this case is to directly use the keys of the imported label
#                 dictionaries as field names
#             label_field ("ground_truth"): the name (or root name) of the
#                 frame field(s) to use for the labels
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if a sample's schema is not a subset of the dataset schema

#         Returns:
#             a list of IDs of the samples that were added to the dataset
#         """
#         return foud.add_labeled_videos(
#             self,
#             samples,
#             sample_parser,
#             label_field=label_field,
#             tags=tags,
#             expand_schema=expand_schema,
#         )

#     def add_videos_dir(self, videos_dir, tags=None, recursive=True):
#         """Adds the given directory of videos to the dataset.

#         See :class:`fiftyone.types.dataset_types.VideoDirectory` for format
#         details. In particular, note that files with non-video MIME types are
#         omitted.

#         This operation does not read/decode the videos.

#         Args:
#             videos_dir: a directory of videos
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             recursive (True): whether to recursively traverse subdirectories

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         video_paths = foud.parse_videos_dir(videos_dir, recursive=recursive)
#         sample_parser = foud.VideoSampleParser()
#         return self.add_videos(video_paths, sample_parser, tags=tags)

#     def add_videos_patt(self, videos_patt, tags=None):
#         """Adds the given glob pattern of videos to the dataset.

#         This operation does not read/decode the videos.

#         Args:
#             videos_patt: a glob pattern of videos like
#                 ``/path/to/videos/*.mp4``
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         video_paths = etau.get_glob_matches(videos_patt)
#         sample_parser = foud.VideoSampleParser()
#         return self.add_videos(video_paths, sample_parser, tags=tags)

#     def ingest_videos(
#         self, paths_or_samples, sample_parser=None, tags=None, dataset_dir=None
#     ):
#         """Ingests the given iterable of videos into the dataset.

#         The videos are copied to ``dataset_dir``.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         ingesting videos into a dataset by defining your own
#         :class:`UnlabeledVideoSampleParser <fiftyone.utils.data.parsers.UnlabeledVideoSampleParser>`.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of video paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledVideoSampleParser`
#                 instance to use to parse the samples
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             dataset_dir (None): the directory in which the videos will be
#                 written. By default, :func:`get_default_dataset_dir` is used

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         if sample_parser is None:
#             sample_parser = foud.VideoSampleParser()

#         if dataset_dir is None:
#             dataset_dir = get_default_dataset_dir(self.name)

#         dataset_ingestor = foud.UnlabeledVideoDatasetIngestor(
#             dataset_dir, paths_or_samples, sample_parser
#         )

#         return self.add_importer(dataset_ingestor, tags=tags)

#     def ingest_labeled_videos(
#         self,
#         samples,
#         sample_parser,
#         tags=None,
#         expand_schema=True,
#         dataset_dir=None,
#     ):
#         """Ingests the given iterable of labeled video samples into the
#         dataset.

#         The videos are copied to ``dataset_dir``.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         ingesting labeled videos into a dataset by defining your own
#         :class:`LabeledVideoSampleParser <fiftyone.utils.data.parsers.LabeledVideoSampleParser>`.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledVideoSampleParser`
#                 instance to use to parse the samples
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             expand_schema (True): whether to dynamically add new sample fields
#                 encountered to the dataset schema. If False, an error is raised
#                 if the sample's schema is not a subset of the dataset schema
#             dataset_dir (None): the directory in which the videos will be
#                 written. By default, :func:`get_default_dataset_dir` is used

#         Returns:
#             a list of IDs of the samples in the dataset
#         """
#         if dataset_dir is None:
#             dataset_dir = get_default_dataset_dir(self.name)

#         dataset_ingestor = foud.LabeledVideoDatasetIngestor(
#             dataset_dir, samples, sample_parser
#         )

#         return self.add_importer(
#             dataset_ingestor, tags=tags, expand_schema=expand_schema
#         )

#     @classmethod
#     def from_dir(
#         cls,
#         dataset_dir=None,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         name=None,
#         label_field=None,
#         tags=None,
#         **kwargs,
#     ):
#         """Creates a :class:`Dataset` from the contents of the given directory.

#         You can create datasets with this method via the following basic
#         patterns:

#         (a) Provide ``dataset_dir`` and ``dataset_type`` to import the contents
#             of a directory that is organized in the default layout for the
#             dataset type as documented in
#             :ref:`this guide <loading-datasets-from-disk>`

#         (b) Provide ``dataset_type`` along with ``data_path``, ``labels_path``,
#             or other type-specific parameters to perform a customized
#             import. This syntax provides the flexibility to, for example,
#             perform labels-only imports or imports where the source media lies
#             in a different location than the labels

#         In either workflow, the remaining parameters of this method can be
#         provided to further configure the import.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         Args:
#             dataset_dir (None): the dataset directory. This can be omitted if
#                 you provide arguments such as ``data_path`` and ``labels_path``
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``export_dir`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``dataset_dir`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``dataset_dir`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``dataset_dir`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in ``dataset_dir``
#                     of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``dataset_dir`` has no effect on the
#                     location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``dataset_dir`` of the labels for the default layout of the
#                 dataset type being imported
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_dir(
#             dataset_dir=dataset_dir,
#             dataset_type=dataset_type,
#             data_path=data_path,
#             labels_path=labels_path,
#             label_field=label_field,
#             tags=tags,
#             **kwargs,
#         )
#         return dataset

#     @classmethod
#     def from_archive(
#         cls,
#         archive_path,
#         dataset_type=None,
#         data_path=None,
#         labels_path=None,
#         name=None,
#         label_field=None,
#         tags=None,
#         cleanup=True,
#         **kwargs,
#     ):
#         """Creates a :class:`Dataset` from the contents of the given archive.

#         If a directory with the same root name as ``archive_path`` exists, it
#         is assumed that this directory contains the extracted contents of the
#         archive, and thus the archive is not re-extracted.

#         See :ref:`this guide <loading-datasets-from-disk>` for example usages
#         of this method and descriptions of the available dataset types.

#         .. note::

#             The following archive formats are explicitly supported::

#                 .zip, .tar, .tar.gz, .tgz, .tar.bz, .tbz

#             If an archive *not* in the above list is found, extraction will be
#             attempted via the ``patool`` package, which supports many formats
#             but may require that additional system packages be installed.

#         Args:
#             archive_path: the path to an archive of a dataset directory
#             dataset_type (None): the
#                 :class:`fiftyone.types.dataset_types.Dataset` type of the
#                 dataset in ``archive_path``
#             data_path (None): an optional parameter that enables explicit
#                 control over the location of the media for certain dataset
#                 types. Can be any of the following:

#                 -   a folder name like ``"data"`` or ``"data/"`` specifying a
#                     subfolder of ``dataset_dir`` in which the media lies
#                 -   an absolute directory path in which the media lies. In this
#                     case, the ``archive_path`` has no effect on the location of
#                     the data
#                 -   a filename like ``"data.json"`` specifying the filename of
#                     a JSON manifest file in ``archive_path`` that maps UUIDs to
#                     media filepaths. Files of this format are generated when
#                     passing the ``export_media="manifest"`` option to
#                     :meth:`fiftyone.core.collections.SampleCollection.export`
#                 -   an absolute filepath to a JSON manifest file. In this case,
#                     ``archive_path`` has no effect on the location of the data
#                 -   a dict mapping filenames to absolute filepaths

#                 By default, it is assumed that the data can be located in the
#                 default location within ``archive_path`` for the dataset type
#             labels_path (None): an optional parameter that enables explicit
#                 control over the location of the labels. Only applicable when
#                 importing certain labeled dataset formats. Can be any of the
#                 following:

#                 -   a type-specific folder name like ``"labels"`` or
#                     ``"labels/"`` or a filename like ``"labels.json"`` or
#                     ``"labels.xml"`` specifying the location in
#                     ``archive_path`` of the labels file(s)
#                 -   an absolute directory or filepath containing the labels
#                     file(s). In this case, ``archive_path`` has no effect on
#                     the location of the labels

#                 For labeled datasets, this parameter defaults to the location
#                 in ``archive_path`` of the labels for the default layout of the
#                 dataset type being imported
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             cleanup (True): whether to delete the archive after extracting it
#             **kwargs: optional keyword arguments to pass to the constructor of
#                 the :class:`fiftyone.utils.data.importers.DatasetImporter` for
#                 the specified ``dataset_type``

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_archive(
#             archive_path,
#             dataset_type=dataset_type,
#             data_path=data_path,
#             labels_path=labels_path,
#             label_field=label_field,
#             tags=tags,
#             cleanup=cleanup,
#             **kwargs,
#         )
#         return dataset

#     @classmethod
#     def from_importer(
#         cls, dataset_importer, name=None, label_field=None, tags=None
#     ):
#         """Creates a :class:`Dataset` by importing the samples in the given
#         :class:`fiftyone.utils.data.importers.DatasetImporter`.

#         See :ref:`this guide <custom-dataset-importer>` for more details about
#         providing a custom
#         :class:`DatasetImporter <fiftyone.utils.data.importers.DatasetImporter>`
#         to import datasets into FiftyOne.

#         Args:
#             dataset_importer: a
#                 :class:`fiftyone.utils.data.importers.DatasetImporter`
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. Only applicable if ``dataset_importer`` is a
#                 :class:`fiftyone.utils.data.importers.LabeledImageDatasetImporter` or
#                 :class:`fiftyone.utils.data.importers.LabeledVideoDatasetImporter`.
#                 If the importer produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the importer produces a
#                 dictionary of labels per sample, this argument specifies a
#                 string prefix to prepend to each label key; the default in this
#                 case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_importer(
#             dataset_importer, label_field=label_field, tags=tags
#         )
#         return dataset

#     @classmethod
#     def from_images(
#         cls, paths_or_samples, sample_parser=None, name=None, tags=None
#     ):
#         """Creates a :class:`Dataset` from the given images.

#         This operation does not read the images.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         providing a custom
#         :class:`UnlabeledImageSampleParser <fiftyone.utils.data.parsers.UnlabeledImageSampleParser>`
#         to load image samples into FiftyOne.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of image paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledImageSampleParser`
#                 instance to use to parse the samples
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_images(
#             paths_or_samples, sample_parser=sample_parser, tags=tags
#         )
#         return dataset

#     @classmethod
#     def from_labeled_images(
#         cls,
#         samples,
#         sample_parser,
#         name=None,
#         label_field=None,
#         tags=None,
#     ):
#         """Creates a :class:`Dataset` from the given labeled images.

#         This operation will iterate over all provided samples, but the images
#         will not be read.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         providing a custom
#         :class:`LabeledImageSampleParser <fiftyone.utils.data.parsers.LabeledImageSampleParser>`
#         to load labeled image samples into FiftyOne.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledImageSampleParser`
#                 instance to use to parse the samples
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. If the parser produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample, this
#                 argument specifies the name of the field to use; the default is
#                 ``"ground_truth"``. If the parser produces a dictionary of
#                 labels per sample, this argument specifies a string prefix to
#                 prepend to each label key; the default in this case is to
#                 directly use the keys of the imported label dictionaries as
#                 field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_labeled_images(
#             samples,
#             sample_parser,
#             label_field=label_field,
#             tags=tags,
#         )
#         return dataset

#     @classmethod
#     def from_images_dir(cls, images_dir, name=None, tags=None, recursive=True):
#         """Creates a :class:`Dataset` from the given directory of images.

#         This operation does not read the images.

#         Args:
#             images_dir: a directory of images
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             recursive (True): whether to recursively traverse subdirectories

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_images_dir(images_dir, tags=tags, recursive=recursive)
#         return dataset

#     @classmethod
#     def from_images_patt(cls, images_patt, name=None, tags=None):
#         """Creates a :class:`Dataset` from the given glob pattern of images.

#         This operation does not read the images.

#         Args:
#             images_patt: a glob pattern of images like
#                 ``/path/to/images/*.jpg``
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_images_patt(images_patt, tags=tags)
#         return dataset

#     @classmethod
#     def from_videos(
#         cls, paths_or_samples, sample_parser=None, name=None, tags=None
#     ):
#         """Creates a :class:`Dataset` from the given videos.

#         This operation does not read/decode the videos.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         providing a custom
#         :class:`UnlabeledVideoSampleParser <fiftyone.utils.data.parsers.UnlabeledVideoSampleParser>`
#         to load video samples into FiftyOne.

#         Args:
#             paths_or_samples: an iterable of data. If no ``sample_parser`` is
#                 provided, this must be an iterable of video paths. If a
#                 ``sample_parser`` is provided, this can be an arbitrary
#                 iterable whose elements can be parsed by the sample parser
#             sample_parser (None): a
#                 :class:`fiftyone.utils.data.parsers.UnlabeledVideoSampleParser`
#                 instance to use to parse the samples
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_videos(
#             paths_or_samples, sample_parser=sample_parser, tags=tags
#         )
#         return dataset

#     @classmethod
#     def from_labeled_videos(
#         cls, samples, sample_parser, name=None, label_field=None, tags=None
#     ):
#         """Creates a :class:`Dataset` from the given labeled videos.

#         This operation will iterate over all provided samples, but the videos
#         will not be read/decoded/etc.

#         See :ref:`this guide <custom-sample-parser>` for more details about
#         providing a custom
#         :class:`LabeledVideoSampleParser <fiftyone.utils.data.parsers.LabeledVideoSampleParser>`
#         to load labeled video samples into FiftyOne.

#         Args:
#             samples: an iterable of data
#             sample_parser: a
#                 :class:`fiftyone.utils.data.parsers.LabeledVideoSampleParser`
#                 instance to use to parse the samples
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             label_field (None): controls the field(s) in which imported labels
#                 are stored. If the parser produces a single
#                 :class:`fiftyone.core.labels.Label` instance per sample/frame,
#                 this argument specifies the name of the field to use; the
#                 default is ``"ground_truth"``. If the parser produces a
#                 dictionary of labels per sample/frame, this argument specifies
#                 a string prefix to prepend to each label key; the default in
#                 this case is to directly use the keys of the imported label
#                 dictionaries as field names
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_labeled_videos(
#             samples, sample_parser, label_field=label_field, tags=tags
#         )
#         return dataset

#     @classmethod
#     def from_videos_dir(cls, videos_dir, name=None, tags=None, recursive=True):
#         """Creates a :class:`Dataset` from the given directory of videos.

#         This operation does not read/decode the videos.

#         Args:
#             videos_dir: a directory of videos
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample
#             recursive (True): whether to recursively traverse subdirectories

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_videos_dir(videos_dir, tags=tags, recursive=recursive)
#         return dataset

#     @classmethod
#     def from_videos_patt(cls, videos_patt, name=None, tags=None):
#         """Creates a :class:`Dataset` from the given glob pattern of videos.

#         This operation does not read/decode the videos.

#         Args:
#             videos_patt: a glob pattern of videos like
#                 ``/path/to/videos/*.mp4``
#             name (None): a name for the dataset. By default,
#                 :func:`get_default_dataset_name` is used
#             tags (None): an optional tag or iterable of tags to attach to each
#                 sample

#         Returns:
#             a :class:`Dataset`
#         """
#         dataset = cls(name)
#         dataset.add_videos_patt(videos_patt, tags=tags)
#         return dataset

#     @classmethod
#     def from_dict(cls, d, name=None, rel_dir=None, frame_labels_dir=None):
#         """Loads a :class:`Dataset` from a JSON dictionary generated by
#         :func:`fiftyone.core.collections.SampleCollection.to_dict`.

#         The JSON dictionary can contain an export of any
#         :class:`fiftyone.core.collections.SampleCollection`, e.g.,
#         :class:`Dataset` or :class:`fiftyone.core.view.DatasetView`.

#         Args:
#             d: a JSON dictionary
#             name (None): a name for the new dataset. By default, ``d["name"]``
#                 is used
#             rel_dir (None): a relative directory to prepend to the ``filepath``
#                 of each sample if the filepath is not absolute (begins with a
#                 path separator). The path is converted to an absolute path
#                 (if necessary) via :func:`fiftyone.core.utils.normalize_path`
#             frame_labels_dir (None): a directory of per-sample JSON files
#                 containing the frame labels for video samples. If omitted, it
#                 is assumed that the frame labels are included directly in the
#                 provided JSON dict. Only applicable to video datasets

#         Returns:
#             a :class:`Dataset`
#         """
#         if name is None:
#             name = d["name"]

#         if rel_dir is not None:
#             rel_dir = fou.normalize_path(rel_dir)

#         name = make_unique_dataset_name(name)
#         dataset = cls(name)

#         media_type = d.get("media_type", None)
#         if media_type is not None:
#             dataset.media_type = media_type

#         dataset._apply_field_schema(d["sample_fields"])
#         if media_type == fom.VIDEO:
#             dataset._apply_frame_field_schema(d["frame_fields"])

#         dataset.info = d.get("info", {})

#         dataset.classes = d.get("classes", {})
#         dataset.default_classes = d.get("default_classes", [])

#         dataset.mask_targets = dataset._parse_mask_targets(
#             d.get("mask_targets", {})
#         )
#         dataset.default_mask_targets = dataset._parse_default_mask_targets(
#             d.get("default_mask_targets", {})
#         )

#         dataset.skeletons = dataset._parse_skeletons(d.get("skeletons", {}))
#         dataset.default_skeleton = dataset._parse_default_skeleton(
#             d.get("default_skeleton", None)
#         )

#         def parse_sample(sd):
#             if rel_dir and not os.path.isabs(sd["filepath"]):
#                 sd["filepath"] = os.path.join(rel_dir, sd["filepath"])

#             if media_type == fom.VIDEO:
#                 frames = sd.pop("frames", {})

#                 if etau.is_str(frames):
#                     frames_path = os.path.join(frame_labels_dir, frames)
#                     frames = etas.load_json(frames_path).get("frames", {})

#                 sample = fos.Sample.from_dict(sd)

#                 for key, value in frames.items():
#                     sample.frames[int(key)] = fofr.Frame.from_dict(value)
#             else:
#                 sample = fos.Sample.from_dict(sd)

#             return sample

#         samples = d["samples"]
#         num_samples = len(samples)

#         _samples = map(parse_sample, samples)
#         dataset.add_samples(
#             _samples, expand_schema=False, num_samples=num_samples
#         )

#         return dataset

#     @classmethod
#     def from_json(
#         cls, path_or_str, name=None, rel_dir=None, frame_labels_dir=None
#     ):
#         """Loads a :class:`Dataset` from JSON generated by
#         :func:`fiftyone.core.collections.SampleCollection.write_json` or
#         :func:`fiftyone.core.collections.SampleCollection.to_json`.

#         The JSON file can contain an export of any
#         :class:`fiftyone.core.collections.SampleCollection`, e.g.,
#         :class:`Dataset` or :class:`fiftyone.core.view.DatasetView`.

#         Args:
#             path_or_str: the path to a JSON file on disk or a JSON string
#             name (None): a name for the new dataset. By default, ``d["name"]``
#                 is used
#             rel_dir (None): a relative directory to prepend to the ``filepath``
#                 of each sample, if the filepath is not absolute (begins with a
#                 path separator). The path is converted to an absolute path
#                 (if necessary) via :func:`fiftyone.core.utils.normalize_path`

#         Returns:
#             a :class:`Dataset`
#         """
#         d = etas.load_json(path_or_str)
#         return cls.from_dict(
#             d, name=name, rel_dir=rel_dir, frame_labels_dir=frame_labels_dir
#         )

#     def _add_view_stage(self, stage):
#         return self.view().add_stage(stage)

#     def _pipeline(
#         self,
#         pipeline=None,
#         attach_frames=False,
#         detach_frames=False,
#         frames_only=False,
#     ):
#         if self.media_type != fom.VIDEO:
#             attach_frames = False
#             detach_frames = False
#             frames_only = False

#         if not attach_frames:
#             detach_frames = False

#         if frames_only:
#             attach_frames = True

#         if attach_frames:
#             _pipeline = self._frames_lookup_pipeline()
#         else:
#             _pipeline = []

#         if pipeline is not None:
#             _pipeline.extend(pipeline)

#         if detach_frames:
#             _pipeline.append({"$project": {"frames": False}})
#         elif frames_only:
#             _pipeline.extend(
#                 [
#                     {"$project": {"frames": True}},
#                     {"$unwind": "$frames"},
#                     {"$replaceRoot": {"newRoot": "$frames"}},
#                 ]
#             )

#         return _pipeline

#     def _frames_lookup_pipeline(self):
#         if self._is_clips:
#             return [
#                 {
#                     "$lookup": {
#                         "from": self._frame_collection_name,
#                         "let": {
#                             "sample_id": "$_sample_id",
#                             "first": {"$arrayElemAt": ["$support", 0]},
#                             "last": {"$arrayElemAt": ["$support", 1]},
#                         },
#                         "pipeline": [
#                             {
#                                 "$match": {
#                                     "$expr": {
#                                         "$and": [
#                                             {
#                                                 "$eq": [
#                                                     "$_sample_id",
#                                                     "$$sample_id",
#                                                 ]
#                                             },
#                                             {
#                                                 "$gte": [
#                                                     "$frame_number",
#                                                     "$$first",
#                                                 ]
#                                             },
#                                             {
#                                                 "$lte": [
#                                                     "$frame_number",
#                                                     "$$last",
#                                                 ]
#                                             },
#                                         ]
#                                     }
#                                 }
#                             },
#                             {"$sort": {"frame_number": 1}},
#                         ],
#                         "as": "frames",
#                     }
#                 }
#             ]

#         return [
#             {
#                 "$lookup": {
#                     "from": self._frame_collection_name,
#                     "let": {"sample_id": "$_id"},
#                     "pipeline": [
#                         {
#                             "$match": {
#                                 "$expr": {
#                                     "$eq": ["$$sample_id", "$_sample_id"]
#                                 }
#                             }
#                         },
#                         {"$sort": {"frame_number": 1}},
#                     ],
#                     "as": "frames",
#                 }
#             }
#         ]

#     def _aggregate(
#         self,
#         pipeline=None,
#         attach_frames=False,
#         detach_frames=False,
#         frames_only=False,
#     ):
#         _pipeline = self._pipeline(
#             pipeline=pipeline,
#             attach_frames=attach_frames,
#             detach_frames=detach_frames,
#             frames_only=frames_only,
#         )

#         return foo.aggregate(self._sample_collection, _pipeline)

#     @property
#     def _sample_collection_name(self):
#         return self._doc.sample_collection_name

#     @property
#     def _sample_collection(self):
#         return foo.get_db_conn()[self._sample_collection_name]

#     @property
#     def _frame_collection_name(self):
#         return self._doc.frame_collection_name

#     @property
#     def _frame_collection(self):
#         return foo.get_db_conn()[self._frame_collection_name]

#     @property
#     def _frame_indexes(self):
#         index_info = self._frame_collection.index_information()
#         return [k["key"][0][0] for k in index_info.values()]

#     def _apply_field_schema(self, new_fields):
#         curr_fields = self.get_field_schema()
#         add_field_fcn = self.add_sample_field
#         self._apply_schema(curr_fields, new_fields, add_field_fcn)

#     def _apply_frame_field_schema(self, new_fields):
#         curr_fields = self.get_frame_field_schema()
#         add_field_fcn = self.add_frame_field
#         self._apply_schema(curr_fields, new_fields, add_field_fcn)

#     def _apply_schema(self, curr_fields, new_fields, add_field_fcn):
#         for field_name, field_str in new_fields.items():
#             if field_name in curr_fields:
#                 # Ensure that existing field matches the requested field
#                 _new_field_str = str(field_str)
#                 _curr_field_str = str(curr_fields[field_name])
#                 if _new_field_str != _curr_field_str:
#                     raise ValueError(
#                         "Existing field %s=%s does not match new field type %s"
#                         % (field_name, _curr_field_str, _new_field_str)
#                     )
#             else:
#                 # Add new field
#                 ftype, embedded_doc_type, subfield = fof.parse_field_str(
#                     field_str
#                 )
#                 add_field_fcn(
#                     field_name,
#                     ftype,
#                     embedded_doc_type=embedded_doc_type,
#                     subfield=subfield,
#                 )

#     def _ensure_label_field(self, label_field, label_cls):
#         if label_field not in self.get_field_schema():
#             self.add_sample_field(
#                 label_field,
#                 fof.EmbeddedDocumentField,
#                 embedded_doc_type=label_cls,
#             )

#     def _expand_schema(self, samples):
#         expanded = False
#         fields = self.get_field_schema(include_private=True)
#         for sample in samples:
#             self._validate_media_type(sample)

#             if self.media_type == fom.VIDEO:
#                 expanded |= self._expand_frame_schema(sample.frames)

#             for field_name in sample._get_field_names(include_private=True):
#                 if field_name == "_id":
#                     continue

#                 if field_name in fields:
#                     continue

#                 value = sample[field_name]
#                 if value is None:
#                     continue

#                 self._sample_doc_cls.add_implied_field(field_name, value)
#                 fields = self.get_field_schema(include_private=True)
#                 expanded = True

#         if expanded:
#             self._reload()

#     def _expand_frame_schema(self, frames):
#         expanded = False
#         fields = self.get_frame_field_schema(include_private=True)
#         for frame in frames.values():
#             for field_name in frame._get_field_names(include_private=True):
#                 if field_name == "_id":
#                     continue

#                 if field_name in fields:
#                     continue

#                 value = frame[field_name]
#                 if value is None:
#                     continue

#                 self._frame_doc_cls.add_implied_field(field_name, value)
#                 fields = self.get_frame_field_schema(include_private=True)
#                 expanded = True

#         return expanded

#     def _validate_media_type(self, sample):
#         if self.media_type != sample.media_type:
#             raise fom.MediaTypeError(
#                 "Sample media type '%s' does not match dataset media type '%s'"
#                 % (sample.media_type, self.media_type)
#             )

#     def _sample_dict_to_doc(self, d):
#         try:
#             return self._sample_doc_cls.from_dict(d, extended=False)
#         except:
#             # The dataset's schema may have been changed in another process;
#             # let's try reloading to see if that fixes things
#             self.reload()

#             return self._sample_doc_cls.from_dict(d, extended=False)

#     def _frame_dict_to_doc(self, d):
#         try:
#             return self._frame_doc_cls.from_dict(d, extended=False)
#         except:
#             # The dataset's schema may have been changed in another process;
#             # let's try reloading to see if that fixes things
#             self.reload()

#             return self._frame_doc_cls.from_dict(d, extended=False)

#     def _validate_samples(self, samples):
#         fields = self.get_field_schema(include_private=True)
#         for sample in samples:
#             non_existent_fields = set()

#             for field_name, value in sample.iter_fields():
#                 field = fields.get(field_name, None)
#                 if field is None:
#                     if value is not None:
#                         non_existent_fields.add(field_name)
#                 else:
#                     if value is not None or not field.null:
#                         try:
#                             field.validate(value)
#                         except moe.ValidationError as e:
#                             raise moe.ValidationError(
#                                 "Invalid value for field '%s'. Reason: %s"
#                                 % (field_name, str(e))
#                             )

#             if non_existent_fields:
#                 raise ValueError(
#                     "Fields %s do not exist on dataset '%s'"
#                     % (non_existent_fields, self.name)
#                 )

#     def reload(self):
#         # TODO: this belongs in a another level, the dataset class should not manage caching
#         """Reloads the dataset and any in-memory samples from the database."""
#         self._reload(hard=True)
#         self._reload_docs(hard=True)

#         self._annotation_cache.clear()
#         self._brain_cache.clear()
#         self._evaluation_cache.clear()

#     def _reload(self, hard=False):
#         # TODO: this belongs in a another level, the dataset class should not manage caching
#         if not hard:
#             self._doc.reload()
#             return

#         doc, sample_doc_cls, frame_doc_cls = _load_dataset(
#             self.name, virtual=True
#         )

#         self._doc = doc
#         self._sample_doc_cls = sample_doc_cls
#         self._frame_doc_cls = frame_doc_cls

#     def _reload_docs(self, hard=False):
#         # TODO: this belongs in a another level, the dataset class should not manage caching
#         fos.Sample._reload_docs(self._sample_collection_name, hard=hard)

#         if self.media_type == fom.VIDEO:
#             fofr.Frame._reload_docs(self._frame_collection_name, hard=hard)

#     def _serialize(self):
#         # TODO: This should return a dict, not necessarily a mongo doc
#         return self._doc.to_dict(extended=True)
