"""
| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import typing as t

import pymongo

from fiftyone.connection.connection import Connection
from fiftyone.connection.schema import FrameSchema, DatasetSchema, SampleSchema


class DirectConnection(Connection[DatasetSchema, SampleSchema, FrameSchema]):
    """Class for connecting to directly to FiftyOne data"""

    DatasetSchema = DatasetSchema
    SampleSchema = SampleSchema
    FrameSchema = FrameSchema

    @classmethod
    def from_config(cls):
        """Create a :class:`DirectConnection` from the FiftyOne config"""
        # This is just a placeholder. TODO:get real client
        mongo_client = pymongo.MongoClient()
        return cls(mongo_client)

    def __init__(self, mongo_client: pymongo.MongoClient):
        self._mongo_client = mongo_client
        self._mongo_db = mongo_client.get_database(
            "fiftyone"
        )  # TODO: get from config

        self._dataset_collection = self._mongo_db.get_collection("datasets")

    def iter_dataset(
        self,
        *_,
        persistent: bool = None,
        include_private: bool = False,
    ) -> t.Generator[DatasetSchema]:
        # Expand on which query kwargs are able to be passed
        """Iterate over datasets."""

        query = {}
        if persistent is not None:
            query["persistent"] = persistent

        if not include_private:
            # Datasets whose sample collections don't start with `samples.` are
            # private e.g., patches or frames datasets
            query["sample_collection_name"] = {"$regex": "^samples\\."}

        # We don't want an error here if `name == None`
        for doc in self._dataset_collection.find(query):
            if doc.get("name") is not None:
                yield doc  # TODO: transform to DatasetData

    def get_sample(self, value: str) -> SampleSchema:
        """Iterate over datasets."""
        # try:
        #     oid = bson.ObjectId(value)
        #     query = {"_id": oid}
        # except:
        #     oid = None
        #     query = {"filepath": value}

        # doc = self._sample_collection.find_one(query)

        # if doc is None:
        #     field = "ID" if oid is not None else "filepath"
        #     raise ValueError(
        #         "No sample found with %s '%s'" % (field, id_filepath_slice)
        #     )

        # data = doc  # TODO: transform to DatasetData
        # return data
