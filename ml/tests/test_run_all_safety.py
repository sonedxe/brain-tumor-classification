"""Synthetic tests for orchestration and report overwrite protection."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

ML_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ML_DIR / "training"), str(ML_DIR / "evaluation")]

import metrics  # noqa: E402
import run_all  # noqa: E402


def make_args(preset: Path, *, skip_train: bool = False, skip_eval: bool = False) -> Namespace:
    return Namespace(
        preset=preset,
        models=None,
        device="cuda",
        epochs=None,
        data_root=None,
        overwrite=False,
        skip_train=skip_train,
        skip_eval=skip_eval,
    )


class RunAllSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="run-all-safety-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.preset = self.root / "preset.yaml"
        self.preset.write_text(
            "models:\n  - mobilenetv3\n  - resnet18\n", encoding="utf-8"
        )
        self.models_dir = self.root / "models"
        self.reports_dir = self.root / "reports"

    def test_failed_training_never_evaluates_stale_checkpoint(self) -> None:
        stale_checkpoint = self.models_dir / "mobilenetv3" / "best.pt"
        stale_checkpoint.parent.mkdir(parents=True)
        stale_checkpoint.write_bytes(b"old checkpoint")
        commands: list[list[str]] = []

        def fake_run(command: list[str]) -> int:
            commands.append(command)
            if "train.py" in command[1]:
                model = command[command.index("--model") + 1]
                if model == "mobilenetv3":
                    return 2
                checkpoint = self.models_dir / model / "best.pt"
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                checkpoint.write_bytes(b"current checkpoint")
                return 0

            model = command[command.index("--model") + 1]
            output_dir = Path(command[command.index("--reports-dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{model}_metrics.json").write_text(
                json.dumps({"accuracy": 0.75, "macro_f1": 0.7}), encoding="utf-8"
            )
            return 0

        args = make_args(self.preset)
        stdout = io.StringIO()
        with (
            mock.patch.object(run_all, "parse_args", return_value=args),
            mock.patch.object(run_all, "MODELS_DIR", self.models_dir),
            mock.patch.object(run_all, "REPORTS_DIR", self.reports_dir),
            mock.patch.object(run_all, "run", side_effect=fake_run),
            contextlib.redirect_stdout(stdout),
        ):
            result = run_all.main()

        eval_models = [
            command[command.index("--model") + 1]
            for command in commands if "metrics.py" in command[1]
        ]
        self.assertEqual(result, 1)
        self.assertEqual(eval_models, ["resnet18"])
        self.assertEqual(stale_checkpoint.read_bytes(), b"old checkpoint")
        self.assertIn("train:mobilenetv3", stdout.getvalue())
        run_dirs = list((self.reports_dir / "runs").iterdir())
        self.assertEqual(len(run_dirs), 1)
        comparison = json.loads((run_dirs[0] / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual(list(comparison), ["resnet18"])

    def test_skip_eval_does_not_read_old_reports_or_write_comparison(self) -> None:
        old_report = self.reports_dir / "mobilenetv3_metrics.json"
        old_report.parent.mkdir(parents=True)
        old_report.write_text("invalid stale json", encoding="utf-8")
        old_comparison = self.reports_dir / "comparison.json"
        old_comparison.write_text("old comparison", encoding="utf-8")
        commands: list[list[str]] = []

        def fake_run(command: list[str]) -> int:
            commands.append(command)
            model = command[command.index("--model") + 1]
            checkpoint = self.models_dir / model / "best.pt"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_bytes(b"current checkpoint")
            return 0

        args = make_args(self.preset, skip_eval=True)
        stdout = io.StringIO()
        with (
            mock.patch.object(run_all, "parse_args", return_value=args),
            mock.patch.object(run_all, "MODELS_DIR", self.models_dir),
            mock.patch.object(run_all, "REPORTS_DIR", self.reports_dir),
            mock.patch.object(run_all, "run", side_effect=fake_run),
            contextlib.redirect_stdout(stdout),
        ):
            result = run_all.main()

        self.assertEqual(result, 0)
        self.assertEqual(len(commands), 2)  # training only, no metrics subprocess
        self.assertEqual(old_report.read_text(encoding="utf-8"), "invalid stale json")
        self.assertEqual(old_comparison.read_text(encoding="utf-8"), "old comparison")
        self.assertFalse((self.reports_dir / "runs").exists())
        self.assertIn("no se leyeron informes previos", stdout.getvalue())

    def test_metric_report_refuses_overwrite_unless_explicit(self) -> None:
        output_dir = self.root / "one-run"
        path = metrics.save_report(
            "mobilenetv3", {"accuracy": 0.5}, reports_dir=output_dir
        )
        original = path.read_text(encoding="utf-8")
        with self.assertRaises(FileExistsError):
            metrics.save_report("mobilenetv3", {"accuracy": 0.9}, reports_dir=output_dir)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

        metrics.save_report(
            "mobilenetv3", {"accuracy": 0.9}, reports_dir=output_dir, overwrite=True
        )
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["accuracy"], 0.9)


if __name__ == "__main__":
    unittest.main()
