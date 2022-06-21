"""
| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from fiftyone.base.client import Client as BaseClient
from fiftyone.base.mapper import Mapper
from fiftyone.common.dataset import Dataset
from fiftyone.common.sample import Sample
from fiftyone.common.frame import Frame
from fiftyone.connection import Connection
from fiftyone.connection import DirectConnection
from fiftyone.connection.schema import DatasetSchema, SampleSchema, FrameSchema


class Client(BaseClient[Dataset, Sample, Frame]):
    """Core client implementation for interacting with FiftyOne"""

    def __init__(self, connection: Connection = None, mapper: Mapper = None):
        super().__init__(
            connection=connection or DirectConnection.from_config(),
            mapper=mapper or _get_default_core_mapper(),
        )


def _get_default_core_mapper() -> Mapper:
    mapper = Mapper()
    mapper.add_mapping(
        Dataset,
        DatasetSchema,
        lambda obj: DatasetSchema(**dict(obj)),
        lambda dto: Dataset(**dto.dict()),
    )
    mapper.add_mapping(
        Sample,
        SampleSchema,
        lambda obj: SampleSchema(**dict(obj)),
        lambda dto: Sample(**dto.dict()),
    )
    mapper.add_mapping(
        Frame,
        FrameSchema,
        lambda obj: FrameSchema(**dict(obj)),
        lambda dto: Frame(**dto.dict()),
    )
    return mapper
