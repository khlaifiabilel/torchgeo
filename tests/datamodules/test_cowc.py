# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

import pytest

from torchgeo.datamodules import COWCCountingDataModule


class TestCOWCCountingDataModule:
    @pytest.fixture(scope="class")
    def datamodule(self) -> COWCCountingDataModule:
        root = os.path.join("tests", "data", "cowc_counting")
        seed = 0
        batch_size = 1
        num_workers = 0
        dm = COWCCountingDataModule(root, seed, batch_size, num_workers)
        dm.prepare_data()
        dm.setup()
        return dm

    def test_train_dataloader(self, datamodule: COWCCountingDataModule) -> None:
        next(iter(datamodule.train_dataloader()))

    def test_val_dataloader(self, datamodule: COWCCountingDataModule) -> None:
        next(iter(datamodule.val_dataloader()))

    def test_test_dataloader(self, datamodule: COWCCountingDataModule) -> None:
        next(iter(datamodule.test_dataloader()))
