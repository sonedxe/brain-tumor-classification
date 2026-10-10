"""Synthetic, filesystem-isolated tests for dataset preparation safety."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

ML_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_DIR / "dataset"))
import prepare as prepare_module  # noqa: E402


class PrepareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="prepare-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "raw"
        self.dest = self.root / "processed"
        self._original_expected_counts = prepare_module.EXPECTED_COUNTS
        prepare_module.EXPECTED_COUNTS = {
            "Training": {name: 2 for name in prepare_module.EXPECTED_RAW_CLASS_MAP},
            "Testing": {name: 1 for name in prepare_module.EXPECTED_RAW_CLASS_MAP},
        }
        self.addCleanup(setattr, prepare_module, "EXPECTED_COUNTS", self._original_expected_counts)

        for split, per_class in (("Training", 2), ("Testing", 1)):
            for class_name in prepare_module.EXPECTED_RAW_CLASS_MAP:
                folder = self.source / split / class_name
                folder.mkdir(parents=True)
                for index in range(per_class):
                    self.write_image(folder / f"{split.lower()}_{index}.png", index)

    @staticmethod
    def write_image(path: Path, value: int = 1) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), (value, value, value)).save(path)

    def test_success_preserves_partition_and_testing_independence(self) -> None:
        self.dest.mkdir()
        (self.dest / ".gitkeep").write_text("", encoding="utf-8")
        manifest = prepare_module.prepare(self.source, self.dest, seed=42)

        self.assertEqual(manifest["total"], 12)
        self.assertEqual(sum(manifest["counts"]["train"].values()), 6)
        self.assertEqual(sum(manifest["counts"]["val"].values()), 2)
        self.assertEqual(sum(manifest["counts"]["test"].values()), 4)
        training_paths = {
            path.relative_to(self.source).as_posix()
            for path in (self.source / "Training").rglob("*.png")
        }
        testing_paths = {
            path.relative_to(self.source).as_posix()
            for path in (self.source / "Testing").rglob("*.png")
        }
        train_val = set(manifest["files"]["train"] + manifest["files"]["val"])
        self.assertEqual(train_val, training_paths)
        self.assertEqual(len(manifest["files"]["train"] + manifest["files"]["val"]), len(training_paths))
        self.assertEqual(set(manifest["files"]["test"]), testing_paths)
        self.assertFalse(train_val & set(manifest["files"]["test"]))
        self.assertTrue((self.dest / ".gitkeep").is_file())
        self.assertTrue((self.dest / "splits.json").is_file())
        self.assertIn("no incluye el contenido binario", manifest["split_fingerprint_scope"])

        second_manifest = prepare_module.prepare(self.source, self.root / "processed-again", seed=42)
        self.assertEqual(manifest["split_fingerprint"], second_manifest["split_fingerprint"])
        self.assertEqual(training_paths | testing_paths, {
            path.relative_to(self.source).as_posix()
            for path in self.source.rglob("*.png")
        })

    def test_rejects_destination_overlapping_source_or_its_parents(self) -> None:
        candidates = (
            self.source,
            self.source / "Training",
            self.source / "Testing",
            self.root,
        )
        original_images = list(self.source.rglob("*.png"))
        for candidate in candidates:
            with self.subTest(dest=candidate), self.assertRaisesRegex(ValueError, "se solapa"):
                prepare_module.prepare(self.source, candidate, overwrite=True)
        self.assertTrue(all(path.is_file() for path in original_images))

    def test_rejects_bad_files_unknown_classes_and_incomplete_counts_before_output(self) -> None:
        bad_image = self.source / "Training" / "glioma" / "broken.png"
        bad_image.write_bytes(b"not an image")
        (self.source / "Training" / "glioma" / "training_0.png").unlink()
        unsupported = self.source / "Testing" / "pituitary" / "notes.tiff"
        unsupported.write_bytes(b"metadata")
        unknown_class = self.source / "Training" / "unknown" / "sample.jpg"
        self.write_image(unknown_class)

        with self.assertRaises(ValueError) as raised:
            prepare_module.prepare(self.source, self.dest)
        message = str(raised.exception)
        self.assertIn("imagen ilegible", message)
        self.assertIn("extensión no admitida", message)
        self.assertIn("Clase desconocida", message)
        self.assertIn("Conteo incorrecto", message)
        self.assertIn(str(bad_image), message)
        self.assertFalse(self.dest.exists())

    def test_rejects_wrong_count_with_path_class_and_detected_count(self) -> None:
        missing = next((self.source / "Training" / "glioma").glob("*.png"))
        missing.unlink()
        with self.assertRaisesRegex(
            ValueError,
            r"Training.*glioma.*esperado 2, detectado 1",
        ):
            prepare_module.prepare(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_class_mapping_discrepancy_fails_before_output(self) -> None:
        with mock.patch.dict(prepare_module.SUBTYPE_TO_CLASS, {"pituitary": "no_tumor"}):
            with self.assertRaisesRegex(ValueError, "Discrepancia de etiquetas"):
                prepare_module.prepare(self.source, self.dest)
        self.assertFalse(self.dest.exists())

    def test_existing_payload_requires_overwrite_and_placeholders_survive(self) -> None:
        self.dest.mkdir()
        (self.dest / ".gitkeep").write_text("placeholder", encoding="utf-8")
        marker = self.dest / "previous-result.txt"
        marker.write_text("keep until explicit overwrite", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            prepare_module.prepare(self.source, self.dest)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep until explicit overwrite")

        manifest = prepare_module.prepare(self.source, self.dest, overwrite=True)
        self.assertEqual(manifest["total"], 12)
        self.assertTrue((self.dest / ".gitkeep").is_file())
        self.assertFalse(marker.exists())

    def test_detects_output_filename_collision(self) -> None:
        first = self.source / "Training" / "glioma" / "A" / "B" / "same.png"
        second = self.source / "Training" / "glioma" / "C" / "A" / "B" / "same.png"
        first.parent.mkdir(parents=True)
        second.parent.mkdir(parents=True)
        self.write_image(first)
        self.write_image(second)
        planned = {
            "train": [("glioma", first), ("glioma", second)],
            "val": [],
        }
        with self.assertRaisesRegex(ValueError, "Colisión de nombre"):
            prepare_module._plan_outputs(planned, {})

        case_only_collision = {
            "train": [
                ("glioma", self.source / "Training" / "glioma" / "A" / "same.png"),
                ("glioma", self.source / "Training" / "glioma" / "A" / "SAME.PNG"),
            ],
            "val": [],
        }
        with self.assertRaisesRegex(ValueError, "Colisión de nombre"):
            prepare_module._plan_outputs(case_only_collision, {})

    def test_copy_failure_does_not_publish_partial_destination(self) -> None:
        self.dest.mkdir()
        marker = self.dest / "old-result.txt"
        marker.write_text("old complete result", encoding="utf-8")
        real_copy2 = shutil.copy2

        def fail_on_image(source: Path, destination: Path):
            if Path(source).suffix.lower() != ".gitkeep":
                raise OSError("synthetic copy failure")
            return real_copy2(source, destination)

        with mock.patch.object(prepare_module.shutil, "copy2", side_effect=fail_on_image):
            with self.assertRaisesRegex(OSError, "synthetic copy failure"):
                prepare_module.prepare(self.source, self.dest, overwrite=True)

        self.assertEqual(marker.read_text(encoding="utf-8"), "old complete result")
        self.assertFalse(list(self.root.glob(".processed.staging-*")))
        self.assertFalse(list(self.root.glob(".processed.backup-*")))

    def test_publish_failure_restores_old_destination(self) -> None:
        self.dest.mkdir()
        marker = self.dest / "old-result.txt"
        marker.write_text("old complete result", encoding="utf-8")
        real_replace = prepare_module.os.replace

        def fail_staging_publish(source: Path, destination: Path):
            if Path(source).name.startswith(".processed.staging-"):
                raise OSError("synthetic publish failure")
            return real_replace(source, destination)

        with mock.patch.object(prepare_module.os, "replace", side_effect=fail_staging_publish):
            with self.assertRaisesRegex(OSError, "synthetic publish failure"):
                prepare_module.prepare(self.source, self.dest, overwrite=True)

        self.assertEqual(marker.read_text(encoding="utf-8"), "old complete result")
        self.assertFalse(list(self.root.glob(".processed.staging-*")))
        self.assertFalse(list(self.root.glob(".processed.backup-*")))


if __name__ == "__main__":
    unittest.main()
