"""Verify no-write preview, install integrity and conflict preflight."""
import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("nin_installer", Path(__file__).with_name("install.py"))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nin-install-test-")
        self.base = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)
        self.destination = self.base / "skills"

    def test_preview_creates_nothing(self):
        result = installer.install(self.destination, dry_run=True)
        self.assertEqual(len(result["skills"]), 18)
        self.assertFalse(self.destination.exists())

    def test_copy_matches_sources_and_reinstall_is_rejected(self):
        result = installer.install(self.destination)
        self.assertEqual(len(result["installed"]), 18)
        _, _, files = installer.plan_install(self.base / "other")
        before = {}
        for source, relative in files:
            target = self.destination / relative
            before[str(relative)] = target.read_bytes()
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), hashlib.sha256(target.read_bytes()).digest())
        with self.assertRaisesRegex(ValueError, "not be overwritten"):
            installer.install(self.destination)
        for relative, original in before.items():
            self.assertEqual((self.destination / relative).read_bytes(), original)

    def test_any_conflict_stops_before_other_skills_are_created(self):
        existing = self.destination / "nin-project"
        existing.mkdir(parents=True)
        marker = existing / "personal.txt"
        marker.write_text("keep my version", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not be overwritten"):
            installer.install(self.destination)
        self.assertEqual(list(self.destination.iterdir()), [existing])
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep my version")


if __name__ == "__main__":
    unittest.main(verbosity=2)
