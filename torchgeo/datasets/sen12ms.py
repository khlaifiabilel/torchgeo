# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""SEN12MS dataset."""

import os
from typing import Callable, Dict, List, Optional

import numpy as np
import rasterio
import torch
from torch import Tensor

from .geo import VisionDataset
from .utils import check_integrity


class SEN12MS(VisionDataset):
    """SEN12MS dataset.

    The `SEN12MS <https://doi.org/10.14459/2019mp1474000>`_ dataset contains
    180,662 patch triplets of corresponding Sentinel-1 dual-pol SAR data,
    Sentinel-2 multi-spectral images, and MODIS-derived land cover maps.
    The patches are distributed across the land masses of the Earth and
    spread over all four meteorological seasons. This is reflected by the
    dataset structure. All patches are provided in the form of 16-bit GeoTiffs
    containing the following specific information:

    * Sentinel-1 SAR: 2 channels corresponding to sigma nought backscatter
      values in dB scale for VV and VH polarization.
    * Sentinel-2 Multi-Spectral: 13 channels corresponding to the 13 spectral bands
      (B1, B2, B3, B4, B5, B6, B7, B8, B8a, B9, B10, B11, B12).
    * MODIS Land Cover: 4 channels corresponding to IGBP, LCCS Land Cover,
      LCCS Land Use, and LCCS Surface Hydrology layers.

    If you use this dataset in your research, please cite the following paper:

    * https://doi.org/10.5194/isprs-annals-IV-2-W7-153-2019

    .. note::

       This dataset can be automatically downloaded using the following bash script:

       .. code-block:: bash

          for season in 1158_spring 1868_summer 1970_fall 2017_winter
          do
              for source in lc s1 s2
              do
                  wget "ftp://m1474000:m1474000@dataserv.ub.tum.de/ROIs${season}_${source}.tar.gz"
                  tar xvzf "ROIs${season}_${source}.tar.gz"
              done
          done

          for split in train test
          do
              wget "https://raw.githubusercontent.com/schmitt-muc/SEN12MS/master/splits/${split}_list.txt"
          done

       or manually downloaded from https://dataserv.ub.tum.de/s/m1474000
       and https://github.com/schmitt-muc/SEN12MS/tree/master/splits.
       This download will likely take several hours.
    """  # noqa: E501

    BAND_SETS: Dict[str, List[int]] = {
        "all": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        "s1": [0, 1],
        "s2-all": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        "s2-reduced": [3, 4, 5, 9, 12, 13],
    }

    filenames = [
        "ROIs1158_spring_lc.tar.gz",
        "ROIs1158_spring_s1.tar.gz",
        "ROIs1158_spring_s2.tar.gz",
        "ROIs1868_summer_lc.tar.gz",
        "ROIs1868_summer_s1.tar.gz",
        "ROIs1868_summer_s2.tar.gz",
        "ROIs1970_fall_lc.tar.gz",
        "ROIs1970_fall_s1.tar.gz",
        "ROIs1970_fall_s2.tar.gz",
        "ROIs2017_winter_lc.tar.gz",
        "ROIs2017_winter_s1.tar.gz",
        "ROIs2017_winter_s2.tar.gz",
        "train_list.txt",
        "test_list.txt",
    ]
    light_filenames = [
        "ROIs1158_spring",
        "ROIs1868_summer",
        "ROIs1970_fall",
        "ROIs2017_winter",
        "train_list.txt",
        "test_list.txt",
    ]
    md5s = [
        "6e2e8fa8b8cba77ddab49fd20ff5c37b",
        "fba019bb27a08c1db96b31f718c34d79",
        "d58af2c15a16f376eb3308dc9b685af2",
        "2c5bd80244440b6f9d54957c6b1f23d4",
        "01044b7f58d33570c6b57fec28a3d449",
        "4dbaf72ecb704a4794036fe691427ff3",
        "9b126a68b0e3af260071b3139cb57cee",
        "19132e0aab9d4d6862fd42e8e6760847",
        "b8f117818878da86b5f5e06400eb1866",
        "0fa0420ef7bcfe4387c7e6fe226dc728",
        "bb8cbfc16b95a4f054a3d5380e0130ed",
        "3807545661288dcca312c9c538537b63",
        "0a68d4e1eb24f128fccdb930000b2546",
        "c7faad064001e646445c4c634169484d",
    ]

    def __init__(
        self,
        root: str = "data",
        split: str = "train",
        bands: List[int] = BAND_SETS["all"],
        transforms: Optional[Callable[[Dict[str, Tensor]], Dict[str, Tensor]]] = None,
        checksum: bool = False,
    ) -> None:
        """Initialize a new SEN12MS dataset instance.

        The ``bands`` argument allows for the subsetting of bands returned by the
        dataset. Integers in ``bands`` index into a stack of Sentinel 1 and Sentinel 2
        imagery. Indices 0 and 1 correspond to the Sentinel 1 imagery where indices 2
        through 14 correspond to the Sentinel 2 imagery.

        Args:
            root: root directory where dataset can be found
            split: one of "train" or "test"
            bands: a list of band indices to use where the indices correspond to the
                array index of combined Sentinel 1 and Sentinel 2
            transforms: a function/transform that takes input sample and its target as
                entry and returns a transformed version
            checksum: if True, check the MD5 of the downloaded files (may be slow)

        Raises:
            AssertionError: if ``split`` argument is invalid
            RuntimeError: if data is not found in ``root``, or checksums don't match
        """
        assert split in ["train", "test"]

        self.root = root
        self.split = split
        self.bands = torch.tensor(bands).long()  # type: ignore[attr-defined]
        self.transforms = transforms
        self.checksum = checksum

        if checksum:
            if not self._check_integrity():
                raise RuntimeError("Dataset not found or corrupted.")
        else:
            if not self._check_integrity_light():
                raise RuntimeError("Dataset not found or corrupted.")

        with open(os.path.join(self.root, split + "_list.txt")) as f:
            self.ids = [line.rstrip() for line in f.readlines()]

    def __getitem__(self, index: int) -> Dict[str, Tensor]:
        """Return an index within the dataset.

        Args:
            index: index to return

        Returns:
            data and label at that index
        """
        filename = self.ids[index]

        lc = self._load_raster(filename, "lc")
        s1 = self._load_raster(filename, "s1")
        s2 = self._load_raster(filename, "s2")

        image = torch.cat(tensors=[s1, s2], dim=0)  # type: ignore[attr-defined]
        image = torch.index_select(  # type: ignore[attr-defined]
            image, dim=0, index=self.bands
        )

        sample: Dict[str, Tensor] = {"image": image, "mask": lc}

        if self.transforms is not None:
            sample = self.transforms(sample)

        return sample

    def __len__(self) -> int:
        """Return the number of data points in the dataset.

        Returns:
            length of the dataset
        """
        return len(self.ids)

    def _load_raster(self, filename: str, source: str) -> Tensor:
        """Load a single raster image or target.

        Args:
            filename: name of the file to load
            source: one of "lc", "s1", or "s2"

        Returns:
            the raster image or target
        """
        parts = filename.split("_")
        parts[2] = source

        with rasterio.open(
            os.path.join(
                self.root,
                "{0}_{1}".format(*parts),
                "{2}_{3}".format(*parts),
                "{0}_{1}_{2}_{3}_{4}".format(*parts),
            )
        ) as f:
            array = f.read().astype(np.int32)
            tensor: Tensor = torch.from_numpy(array)  # type: ignore[attr-defined]
            return tensor

    def _check_integrity_light(self) -> bool:
        """Checks the integrity of the dataset structure.

        Returns:
            True if the dataset directories and split files are found, else False
        """
        for filename in self.light_filenames:
            filepath = os.path.join(self.root, filename)
            if not os.path.exists(filepath):
                return False
        return True

    def _check_integrity(self) -> bool:
        """Check integrity of dataset.

        Returns:
            True if dataset files are found and/or MD5s match, else False
        """
        for filename, md5 in zip(self.filenames, self.md5s):
            filepath = os.path.join(self.root, filename)
            if not check_integrity(filepath, md5 if self.checksum else None):
                return False
        return True
