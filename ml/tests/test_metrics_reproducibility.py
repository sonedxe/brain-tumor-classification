"""Synthetic tests for evaluation provenance and metric serialization."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ML_DIR = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ML_DIR / "training"), str(ML_DIR / "evaluation")]

import metrics  # noqa: E402


CLASSES = ["glioma", "meningioma", "pituitario", "no_tumor"]
CONFIG = {
    "input": {"size": 224},
    "normalization": {
        "mode": "imagenet",
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
    },
}


def checkpoint_metadata() -> dict:
    return {
        "architecture": "mobilenetv3",
        "classes": CLASSES.copy(),
        "class_to_idx": {name: index for index, name in enumerate(CLASSES)},
        "input_size": 224,
        "normalization": CONFIG["normalization"],
        "state_dict": {},
    }


class MetricsReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="metrics-repro-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_checkpoint_validation_rejects_class_order_mismatch(self) -> None:
        checkpoint = checkpoint_metadata()
        checkpoint["classes"] = list(reversed(CLASSES))
        with self.assertRaisesRegex(ValueError, "Orden de clases incompatible"):
            metrics.validate_checkpoint_metadata(checkpoint, "mobilenetv3", CLASSES, CONFIG)

    def test_checkpoint_validation_rejects_class_to_idx_mismatch(self) -> None:
        checkpoint = checkpoint_metadata()
        checkpoint["class_to_idx"]["glioma"] = 3
        with self.assertRaisesRegex(ValueError, "class_to_idx incompatible"):
            metrics.validate_checkpoint_metadata(checkpoint, "mobilenetv3", CLASSES, CONFIG)

    def test_checkpoint_validation_rejects_preprocessing_mismatch(self) -> None:
        checkpoint = checkpoint_metadata()
        checkpoint["normalization"] = {**CONFIG["normalization"], "mean": [0, 0, 0]}
        with self.assertRaisesRegex(ValueError, "Normalización incompatible en mean"):
            metrics.validate_checkpoint_metadata(checkpoint, "mobilenetv3", CLASSES, CONFIG)

    def _make_manifest_dataset(self):
        root = self.root / "processed"
        source_paths = []
        target_indices = []
        manifest_paths = []
        counts = {name: 0 for name in CLASSES}
        for index, name in enumerate(CLASSES):
            raw_class = {"pituitario": "pituitary", "no_tumor": "notumor"}.get(name, name)
            processed_relative = Path("test") / name / f"Testing__{raw_class}__sample.jpg"
            sample_path = root / processed_relative
            sample_path.parent.mkdir(parents=True, exist_ok=True)
            sample_path.write_bytes(b"synthetic path placeholder")
            source_paths.append((str(sample_path), index))
            target_indices.append(index)
            manifest_paths.append(f"Testing/{raw_class}/sample.jpg")
            counts[name] += 1

        manifest = {
            "source": str(self.root / "raw"),
            "seed": 42,
            "classes": CLASSES,
            "counts": {"train": {}, "val": {}, "test": counts},
            "files": {"train": [], "val": [], "test": manifest_paths},
            "split_fingerprint": "synthetic-split-fingerprint",
            "split_fingerprint_scope": "synthetic paths only",
        }
        (root / "splits.json").write_text(json.dumps(manifest), encoding="utf-8")
        dataset = SimpleNamespace(
            base=SimpleNamespace(samples=source_paths),
            targets=target_indices,
            classes=CLASSES,
        )
        return root, dataset, manifest_paths

    def test_manifest_routes_and_labels_match_test_dataset_and_hashes(self) -> None:
        root, dataset, _ = self._make_manifest_dataset()
        result = metrics.verify_test_manifest(root, dataset, CLASSES, required=True)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["n_samples"], 4)
        self.assertEqual(result["split_fingerprint"], "synthetic-split-fingerprint")
        manifest_bytes = (root / "splits.json").read_bytes()
        self.assertEqual(result["manifest_sha256"], hashlib.sha256(manifest_bytes).hexdigest())

    def test_manifest_mismatch_is_rejected(self) -> None:
        root, dataset, _ = self._make_manifest_dataset()
        extra = root / "test" / "glioma" / "extra.jpg"
        extra.write_bytes(b"extra")
        dataset.base.samples.append((str(extra), 0))
        dataset.targets.append(0)
        with self.assertRaisesRegex(metrics.ManifestMismatchError, "adicionales"):
            metrics.verify_test_manifest(root, dataset, CLASSES, required=True)

    def test_manifest_label_mismatch_is_rejected(self) -> None:
        root, dataset, _ = self._make_manifest_dataset()
        dataset.targets[0] = 1
        with self.assertRaisesRegex(metrics.ManifestMismatchError, "Etiquetas del test"):
            metrics.verify_test_manifest(root, dataset, CLASSES, required=True)

    def test_manifest_duplicate_and_missing_evaluation_routes_are_rejected(self) -> None:
        root, dataset, _ = self._make_manifest_dataset()
        manifest_path = root / "splits.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["test"].append(manifest["files"]["test"][0])
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(metrics.ManifestMismatchError, "duplicadas"):
            metrics.verify_test_manifest(root, dataset, CLASSES, required=True)

        root, dataset, _ = self._make_manifest_dataset()
        dataset.base.samples.pop()
        dataset.targets.pop()
        with self.assertRaisesRegex(metrics.ManifestMismatchError, "faltan="):
            metrics.verify_test_manifest(root, dataset, CLASSES, required=True)

    def test_missing_manifest_is_a_limit_or_a_hard_error(self) -> None:
        root = self.root / "no-manifest"
        root.mkdir()
        optional = metrics.verify_test_manifest(root, SimpleNamespace(), CLASSES, required=False)
        self.assertEqual(optional["status"], "unavailable")
        with self.assertRaisesRegex(FileNotFoundError, "Se requiere el manifiesto"):
            metrics.verify_test_manifest(root, SimpleNamespace(), CLASSES, required=True)

    def test_sha256_hashes_exact_file_bytes(self) -> None:
        path = self.root / "checkpoint.bin"
        path.write_bytes(b"synthetic checkpoint bytes")
        self.assertEqual(metrics.sha256_file(path), hashlib.sha256(path.read_bytes()).hexdigest())

    def test_prediction_serialization_keeps_order_probabilities_and_refuses_overwrite(self) -> None:
        payload = metrics.prediction_payload(
            run_id="run-1",
            model_name="mobilenetv3",
            architecture="mobilenetv3",
            checkpoint_sha256="abc123",
            classes=CLASSES,
            y_true=np.array([1]),
            y_pred=np.array([0]),
            probabilities=np.array([[0.7, 0.1, 0.1, 0.1]]),
            identifiers=["test/glioma/sample.jpg"],
        )
        path = metrics.save_predictions("mobilenetv3", payload, self.root / "reports")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["classes"], CLASSES)
        self.assertEqual(saved["predictions"][0]["y_true"], "meningioma")
        self.assertEqual(saved["predictions"][0]["probabilities"]["glioma"], 0.7)
        with self.assertRaises(FileExistsError):
            metrics.save_predictions("mobilenetv3", payload, self.root / "reports")

    def test_multiclass_metrics_confusion_and_auc(self) -> None:
        labels = np.array([0, 0, 1, 1, 2, 2, 3, 3])
        probabilities = np.full((8, 4), 0.02)
        probabilities[np.arange(8), labels] = 0.94
        result = metrics.compute_metrics(labels, labels.copy(), CLASSES, probabilities)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["macro_f1"], 1.0)
        self.assertEqual(result["weighted_f1"], 1.0)
        self.assertEqual(result["confusion_matrix"], np.diag([2, 2, 2, 2]).tolist())
        self.assertEqual(result["roc_auc_macro_ovr"], 1.0)
        self.assertEqual(result["per_class"]["glioma"]["support"], 2)
        self.assertNotIn("tumor_sensitivity", result)
        self.assertNotIn("specificity_no_tumor", result)

    def test_undefined_auc_is_null_with_reason(self) -> None:
        labels = np.array([0, 1])
        probabilities = np.array([[0.8, 0.2, 0.0, 0.0], [0.2, 0.8, 0.0, 0.0]])
        result = metrics.compute_metrics(labels, labels.copy(), CLASSES, probabilities)
        self.assertIsNone(result["roc_auc_per_class"]["pituitario"])
        self.assertIsNone(result["roc_auc_per_class"]["no_tumor"])
        self.assertIsNone(result["roc_auc_macro_ovr"])
        self.assertIn("roc_auc_per_class.pituitario", result["undefined_metric_reasons"])
        self.assertIn("roc_auc_macro_ovr", result["undefined_metric_reasons"])

    def test_loss_and_probabilities_are_computed_from_same_synthetic_logits(self) -> None:
        logits = np.array([[2.0, 0.0, 0.0, 0.0], [0.0, 2.0, 0.0, 0.0]])
        y_true = np.array([0, 1])
        y_pred, probabilities, loss = metrics.logits_to_predictions(logits, y_true)
        self.assertEqual(y_pred.tolist(), [0, 1])
        self.assertTrue(np.allclose(probabilities.sum(axis=1), 1.0))
        self.assertAlmostEqual(loss, 0.340753, places=5)


if __name__ == "__main__":
    unittest.main()
