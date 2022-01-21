"""
Parallel processing utilities.

| Copyright 2017-2022, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import multiprocessing

import fiftyone.core.utils as fou


__sample_collection = None
__do = None


def par_do(sample_collection, fcn, num_workers=None):
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()

    sample_ids = sample_collection.values("id")
    total = len(sample_ids)

    name = sample_collection._root_dataset.name
    view_stages = sample_collection._serialize()

    pool = multiprocessing.Pool(
        initializer=_init,
        initargs=(name, view_stages, fcn),
        processes=num_workers,
    )

    with fou.ProgressBar(total=total) as pb:
        with pool:
            for _ in pb(pool.imap_unordered(_do, sample_ids)):
                pass


def _init(name, view_stages, fcn):
    global __sample_collection
    global __do

    import fiftyone.core.dataset as fod
    import fiftyone.core.view as fov

    dataset = fod.load_dataset(name)

    if view_stages:
        __sample_collection = fov.DatasetView._build(dataset, view_stages)
    else:
        __sample_collection = dataset

    __do = fcn


def _do(sample_id):
    __do(__sample_collection[sample_id])
