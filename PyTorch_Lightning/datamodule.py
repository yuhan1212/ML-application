"""
A datamodule is a shareable, reusable class that encapsulates all the 
steps needed to process data.

A datamodule encapsulates the five steps involved in data processing 
in PyTorch:

        - Download / tokenize / process.

        - Clean and (maybe) save to disk.

        - Load inside Dataset.

        - Apply transforms (rotate, tokenize, etc…).

        - Wrap inside a DataLoader.


Why do I need a DataModule?
In normal PyTorch code, the data cleaning/preparation is usually scattered
across many files. This makes sharing and reusing the exact splits and
transforms across projects impossible.

    Datamodules are for you if you ever asked the questions:

        - what splits did you use?

        - what transforms did you use?

        - what normalization did you use?

        - how did you prepare/tokenize the data?    
"""

import os
import platform
from typing import Optional
from urllib.error import HTTPError
from warnings import warn

from torch.utils.data import DataLoader, random_split

from pl_examples import _DATASETS_PATH
from pytorch_lightning import LightningDataModule
from pytorch_lightning.utilities.imports import _TORCHVISION_AVAILABLE

if _TORCHVISION_AVAILABLE:
    from torchvision import transforms as transform_lib

# TODO: add other parts to complete this MINST pl example.
def MNIST(*args, **kwargs):
    torchvision_mnist_available = not bool(os.getenv("PL_USE_MOCKED_MNIST", False))
    if torchvision_mnist_available:
        try:
            from torchvision.datasets import MNIST

            MNIST(_DATASETS_PATH, download=True)
        except HTTPError as e:
            print(f"Error {e} downloading `torchvision.datasets.MNIST`")
            torchvision_mnist_available = False
    if not torchvision_mnist_available:
        print("`torchvision.datasets.MNIST` not available. Using our hosted version")
        from tests.helpers.datasets import MNIST
    return MNIST(*args, **kwargs)


class MNISTDataModule(LightningDataModule):
    """Standard MNIST, train, val, test splits and transforms.
    >>> MNISTDataModule()  # doctest: +ELLIPSIS
    <...mnist_datamodule.MNISTDataModule object at ...>
    """

    name = "mnist"

    def __init__(
        self,
        data_dir: str = _DATASETS_PATH,
        val_split: int = 5000,
        num_workers: int = 16,
        normalize: bool = False,
        seed: int = 42,
        batch_size: int = 32,
        *args,
        **kwargs,
    ):
        """
        Args:
            data_dir: where to save/load the data
            val_split: how many of the training images to use for the validation split
            num_workers: how many workers to use for loading data
            normalize: If true applies image normalize
            seed: starting seed for RNG.
            batch_size: desired batch size.
        """
        super().__init__(*args, **kwargs)

        self.dims = (1, 28, 28)
        self.data_dir = data_dir
        self.val_split = val_split
        self.num_workers = num_workers
        self.normalize = normalize
        self.seed = seed
        self.batch_size = batch_size
        self.dataset_train = ...
        self.dataset_val = ...
        self.test_transforms = self.default_transforms

    @property
    def num_classes(self):
        return 10

    def prepare_data(self):
        """Saves MNIST files to `data_dir`"""
        MNIST(self.data_dir, train=True, download=True)
        MNIST(self.data_dir, train=False, download=True)

    def setup(self, stage: Optional[str] = None):
        """Split the train and valid dataset."""
        extra = dict(transform=self.default_transforms) if self.default_transforms else {}
        dataset = MNIST(self.data_dir, train=True, download=False, **extra)
        train_length = len(dataset)
        self.dataset_train, self.dataset_val = random_split(dataset, [train_length - self.val_split, self.val_split])

    def train_dataloader(self):
        """MNIST train set removes a subset to use for validation."""
        loader = DataLoader(
            self.dataset_train,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            drop_last=True,
            pin_memory=True,
        )
        return loader

    def val_dataloader(self):
        """MNIST val set uses a subset of the training set for validation."""
        loader = DataLoader(
            self.dataset_val,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            drop_last=True,
            pin_memory=True,
        )
        return loader

    def test_dataloader(self):
        """MNIST test set uses the test split."""
        extra = dict(transform=self.test_transforms) if self.test_transforms else {}
        dataset = MNIST(self.data_dir, train=False, download=False, **extra)
        loader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            drop_last=True,
            pin_memory=True,
        )
        return loader

    @property
    def default_transforms(self):
        if not _TORCHVISION_AVAILABLE:
            return None
        if self.normalize:
            mnist_transforms = transform_lib.Compose(
                [transform_lib.ToTensor(), transform_lib.Normalize(mean=(0.5,), std=(0.5,))]
            )
        else:
            mnist_transforms = transform_lib.ToTensor()

        return mnist_transforms