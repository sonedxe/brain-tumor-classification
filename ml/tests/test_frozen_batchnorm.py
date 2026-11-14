"""Synthetic checks for frozen backbones and BatchNorm training behavior."""

from __future__ import annotations

import gc
import sys
import unittest
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

ML_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_DIR / "training"))

from model_factory import (  # noqa: E402
    MODEL_SPECS,
    build_model,
    classifier_module,
    freeze_backbone,
    trainable_parameters,
)
from train import train_one_epoch  # noqa: E402


class FrozenBatchNormTests(unittest.TestCase):
    def test_all_architectures_keep_frozen_backbone_batchnorm_and_train_head(self) -> None:
        previous_threads = torch.get_num_threads()
        torch.set_num_threads(min(previous_threads, 2))
        self.addCleanup(torch.set_num_threads, previous_threads)

        for architecture in MODEL_SPECS:
            with self.subTest(architecture=architecture):
                model = build_model(architecture, num_classes=4, pretrained=False)
                freeze_backbone(model, architecture)
                head = classifier_module(model, architecture)
                head_parameter_ids = {id(parameter) for parameter in head.parameters()}
                trainable = list(trainable_parameters(model))
                self.assertEqual({id(parameter) for parameter in trainable}, head_parameter_ids)

                batchnorms = [
                    module for module in model.modules()
                    if isinstance(module, torch.nn.modules.batchnorm._BatchNorm)
                ]
                self.assertTrue(batchnorms, f"{architecture} should include BatchNorm layers")
                buffers_before = {
                    (name, field): getattr(module, field).detach().clone()
                    for name, module in model.named_modules()
                    if isinstance(module, torch.nn.modules.batchnorm._BatchNorm)
                    for field in ("running_mean", "running_var", "num_batches_tracked")
                    if getattr(module, field) is not None
                }
                params_before = {
                    name: parameter.detach().clone()
                    for name, parameter in model.named_parameters()
                    if id(parameter) not in head_parameter_ids
                }
                head_before = {
                    name: parameter.detach().clone()
                    for name, parameter in model.named_parameters()
                    if id(parameter) in head_parameter_ids
                }

                optimizer = torch.optim.Adam(trainable, lr=0.001)
                criterion = torch.nn.CrossEntropyLoss()
                loader = DataLoader(
                    TensorDataset(torch.randn(2, 3, 224, 224), torch.tensor([0, 1])),
                    batch_size=2,
                )
                for _epoch in range(2):
                    # train_one_epoch calls model.train() at every epoch start.
                    train_one_epoch(model, loader, criterion, optimizer, torch.device("cpu"))
                    self.assertTrue(all(not module.training for module in batchnorms))

                buffers_after = {
                    (name, field): getattr(module, field)
                    for name, module in model.named_modules()
                    if isinstance(module, torch.nn.modules.batchnorm._BatchNorm)
                    for field in ("running_mean", "running_var", "num_batches_tracked")
                    if getattr(module, field) is not None
                }
                self.assertEqual(buffers_before.keys(), buffers_after.keys())
                self.assertTrue(
                    all(torch.equal(before, buffers_after[key]) for key, before in buffers_before.items()),
                    f"{architecture}: BatchNorm buffers changed",
                )

                params_after = dict(model.named_parameters())
                self.assertTrue(
                    all(torch.equal(before, params_after[name]) for name, before in params_before.items()),
                    f"{architecture}: frozen backbone parameters changed",
                )
                self.assertTrue(
                    all(params_after[name].grad is None for name in params_before),
                    f"{architecture}: frozen backbone received gradients",
                )
                self.assertTrue(
                    all(
                        params_after[name].grad is not None
                        and torch.count_nonzero(params_after[name].grad).item() > 0
                        for name in head_before
                    ),
                    f"{architecture}: classifier did not receive nonzero gradients",
                )
                self.assertTrue(
                    any(not torch.equal(before, params_after[name]) for name, before in head_before.items()),
                    f"{architecture}: classifier parameters did not update",
                )
                del model, optimizer, loader
                gc.collect()


if __name__ == "__main__":
    unittest.main()
