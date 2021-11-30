"""This script will generate 2 traces: one for `training_step` and one for `validation_step`. The traces can be
visualized in 2 ways:
* With Chrome:
    1. Open Chrome and copy/paste this url: `chrome://tracing/`.
    2. Once tracing opens, click on `Load` at the top-right and load one of the generated traces.
* With PyTorch Tensorboard Profiler (Instructions are here: https://github.com/pytorch/kineto/tree/master/tb_plugin)
    1. pip install tensorboard torch-tb-profiler
    2. tensorboard --logdir={FOLDER}
"""

import sys

import torch
import torchvision
import torchvision.models as models
import torchvision.transforms as T

from pl_examples import _DATASETS_PATH, cli_lightning_logo
from pytorch_lightning import LightningDataModule, LightningModule
from pytorch_lightning.profiler.pytorch import PyTorchProfiler
from pytorch_lightning.utilities.cli import LightningCLI

DEFAULT_CMD_LINE = (
    "fit",
    "--trainer.max_epochs=1",
    "--trainer.limit_train_batches=3",
    "--trainer.limit_val_batches=3",
    "--trainer.profiler=pytorch",
    f"--trainer.gpus={int(torch.cuda.is_available())}",
)


class ModelToProfile(LightningModule):
    def __init__(self, name: str = "resnet18", automatic_optimization: bool = True):
        super().__init__()
        self.model = getattr(models, name)(pretrained=True)
        self.criterion = torch.nn.CrossEntropyLoss()
        self.automatic_optimization = automatic_optimization
        self.training_step = (
            self.automatic_optimization_training_step
            if automatic_optimization
            else self.manual_optimization_training_step
        )

    def automatic_optimization_training_step(self, batch, batch_idx):
        inputs, labels = batch
        outputs = self.model(inputs)
        loss = self.criterion(outputs, labels)
        self.log("train_loss", loss)
        return loss

    def manual_optimization_training_step(self, batch, batch_idx):
        opt = self.optimizers()
        opt.zero_grad()
        inputs, labels = batch
        outputs = self.model(inputs)
        loss = self.criterion(outputs, labels)
        self.log("train_loss", loss)
        self.manual_backward(loss)
        opt.step()

    def validation_step(self, batch, batch_idx):
        inputs, labels = batch
        outputs = self.model(inputs)
        loss = self.criterion(outputs, labels)
        self.log("val_loss", loss)

    def predict_step(self, batch, batch_idx, dataloader_idx: int = None):
        inputs = batch[0]
        return self.model(inputs)

    def configure_optimizers(self):
        return torch.optim.SGD(self.parameters(), lr=0.001, momentum=0.9)


class CIFAR10DataModule(LightningDataModule):

    transform = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor()])

    def train_dataloader(self, *args, **kwargs):
        trainset = torchvision.datasets.CIFAR10(
            root=_DATASETS_PATH, train=True, download=True, transform=self.transform
        )
        return torch.utils.data.DataLoader(trainset, batch_size=2, shuffle=True, num_workers=0)

    def val_dataloader(self, *args, **kwargs):
        valset = torchvision.datasets.CIFAR10(root=_DATASETS_PATH, train=False, download=True, transform=self.transform)
        return torch.utils.data.DataLoader(valset, batch_size=2, shuffle=True, num_workers=0)


def cli_main():
    if len(sys.argv) == 1:
        sys.argv += DEFAULT_CMD_LINE

    LightningCLI(
        ModelToProfile, CIFAR10DataModule, save_config_overwrite=True, trainer_defaults={"profiler": PyTorchProfiler()}
    )


if __name__ == "__main__":
    cli_lightning_logo()
    cli_main()