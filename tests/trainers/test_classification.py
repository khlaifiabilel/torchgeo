# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from typing import Any, Dict, Union, cast

import pytest
from omegaconf import OmegaConf
from pytorch_lightning import LightningDataModule, Trainer

from torchgeo.datamodules import (
    BigEarthNetDataModule,
    EuroSATDataModule,
    RESISC45DataModule,
    So2SatDataModule,
    UCMercedDataModule,
)
from torchgeo.trainers import ClassificationTask, MultiLabelClassificationTask


class TestClassificationTask:
    @pytest.mark.parametrize(
        "name,classname",
        [
            ("eurosat", EuroSATDataModule),
            ("resisc45", RESISC45DataModule),
            ("so2sat_supervised", So2SatDataModule),
            ("so2sat_unsupervised", So2SatDataModule),
            ("ucmerced", UCMercedDataModule),
        ],
    )
    def test_trainer(self, name: str, classname: LightningDataModule) -> None:
        if name == "so2sat":
            pytest.importorskip("h5py")

        conf = OmegaConf.load(os.path.join("conf", "task_defaults", name + ".yaml"))
        conf_dict = OmegaConf.to_object(conf.experiment)
        conf_dict = cast(Dict[Any, Dict[Any, Any]], conf_dict)

        # Instantiate datamodule
        datamodule_kwargs = conf_dict["datamodule"]
        datamodule = classname(**datamodule_kwargs)

        # Instantiate model
        model_kwargs = conf_dict["module"]
        model = ClassificationTask(**model_kwargs)

        # Instantiate trainer
        trainer = Trainer(fast_dev_run=True, log_every_n_steps=1)
        trainer.fit(model=model, datamodule=datamodule)
        trainer.test(model=model, datamodule=datamodule)

    @pytest.fixture
    def model_kwargs(self) -> Dict[str, Union[str, int]]:
        return {
            "classification_model": "resnet18",
            "in_channels": 1,
            "loss": "ce",
            "num_classes": 1,
            "weights": "random",
        }

    def test_pretrained(
        self, model_kwargs: Dict[str, Union[str, int]], checkpoint: str
    ) -> None:
        model_kwargs["weights"] = checkpoint
        with pytest.warns(UserWarning):
            ClassificationTask(**model_kwargs)

    def test_invalid_pretrained(
        self, model_kwargs: Dict[str, Union[str, int]], checkpoint: str
    ) -> None:
        model_kwargs["weights"] = checkpoint
        model_kwargs["classification_model"] = "resnet50"
        match = "Trying to load resnet18 weights into a resnet50"
        with pytest.raises(ValueError, match=match):
            ClassificationTask(**model_kwargs)

    def test_invalid_loss(self, model_kwargs: Dict[str, Union[str, int]]) -> None:
        model_kwargs["loss"] = "invalid_loss"
        match = "Loss type 'invalid_loss' is not valid."
        with pytest.raises(ValueError, match=match):
            ClassificationTask(**model_kwargs)

    def test_invalid_model(self, model_kwargs: Dict[str, Union[str, int]]) -> None:
        model_kwargs["classification_model"] = "invalid_model"
        match = "Model type 'invalid_model' is not a valid timm model."
        with pytest.raises(ValueError, match=match):
            ClassificationTask(**model_kwargs)

    def test_invalid_weights(self, model_kwargs: Dict[str, Union[str, int]]) -> None:
        model_kwargs["weights"] = "invalid_weights"
        match = "Weight type 'invalid_weights' is not valid."
        with pytest.raises(ValueError, match=match):
            ClassificationTask(**model_kwargs)


class TestMultiLabelClassificationTask:
    @pytest.mark.parametrize(
        "name,classname",
        [
            ("bigearthnet_all", BigEarthNetDataModule),
            ("bigearthnet_s1", BigEarthNetDataModule),
            ("bigearthnet_s2", BigEarthNetDataModule),
        ],
    )
    def test_trainer(self, name: str, classname: LightningDataModule) -> None:
        conf = OmegaConf.load(os.path.join("conf", "task_defaults", name + ".yaml"))
        conf_dict = OmegaConf.to_object(conf.experiment)
        conf_dict = cast(Dict[Any, Dict[Any, Any]], conf_dict)

        # Instantiate datamodule
        datamodule_kwargs = conf_dict["datamodule"]
        datamodule = classname(**datamodule_kwargs)

        # Instantiate model
        model_kwargs = conf_dict["module"]
        model = MultiLabelClassificationTask(**model_kwargs)

        # Instantiate trainer
        trainer = Trainer(fast_dev_run=True, log_every_n_steps=1)
        trainer.fit(model=model, datamodule=datamodule)
        trainer.test(model=model, datamodule=datamodule)

    @pytest.fixture
    def model_kwargs(self) -> Dict[str, Union[str, int]]:
        return {
            "classification_model": "resnet18",
            "in_channels": 1,
            "loss": "ce",
            "num_classes": 1,
            "weights": "random",
        }

    def test_invalid_loss(self, model_kwargs: Dict[str, Union[str, int]]) -> None:
        model_kwargs["loss"] = "invalid_loss"
        match = "Loss type 'invalid_loss' is not valid."
        with pytest.raises(ValueError, match=match):
            MultiLabelClassificationTask(**model_kwargs)
