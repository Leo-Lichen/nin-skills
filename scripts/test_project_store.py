"""Behavior checks for identity, append-only history and evidence correction."""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/nin-project/scripts/project_store.py"
spec = importlib.util.spec_from_file_location("project_store", SCRIPT)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)

# Real child processes use the same on-disk project. Optional gates pause a
# writer after reading history, allowing the other process to contend while
# the first transaction is still in progress. No production test hook is used.
WORKER = r'''
import importlib.util, json, sys, time
from pathlib import Path
script, project, source, started, gate, read_gate, read_ready = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("store_worker", script)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)
started.write_text("ready", encoding="utf-8")
while not gate.exists():
    time.sleep(0.01)
if str(read_ready) != "unused":
    original = store.records
    def paused_records(root):
        result = original(root)
        read_ready.write_text("history read", encoding="utf-8")
        while not read_gate.exists():
            time.sleep(0.01)
        return result
    store.records = paused_records
try:
    print(json.dumps(store.save(project, source), ensure_ascii=False))
except (ValueError, OSError) as exc:
    print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
'''

LOCK_HOLDER = r'''
import importlib.util, sys, time
from pathlib import Path
script, project, marker = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("store_holder", script)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)
with store.project_lock(project):
    marker.write_text("locked", encoding="utf-8")
    while True:
        time.sleep(0.1)
'''


class StoreBehavior(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nin-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / "中文业务"
        self.payload = {
            "project_id": "中文业务", "title": "第一轮", "summary": "检验交易假设",
            "claims": [{"id": "a", "text": "用户说有人愿意购买", "kind": "user_statement", "source": "用户对话", "supersedes": []}]
        }

    def save(self, data):
        source = self.base / "input.json"
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return store.save(self.project, source)

    def wait_for(self, marker, process, timeout=10):
        deadline = time.monotonic() + timeout
        while not marker.exists():
            if process.poll() is not None:
                self.fail("Child exited before marker: " + repr(process.communicate()))
            if time.monotonic() > deadline:
                self.fail("Timed out waiting for child marker: " + str(marker))
            time.sleep(0.01)

    def launch(self, code, *args):
        child = subprocess.Popen(
            [sys.executable, "-B", "-X", "utf8", "-c", code, *map(str, args)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        )

        def close():
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)

        self.addCleanup(close)
        return child

    def writer(self, name, data, gate, read_gate="unused", read_ready="unused"):
        source = self.base / (name + ".json")
        source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        started = self.base / (name + ".started")
        child = self.launch(WORKER, SCRIPT, self.project, source, started, gate, read_gate, read_ready)
        self.wait_for(started, child)
        return child

    def cli(self, command):
        completed = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(SCRIPT), command, "--project-dir", str(self.project)],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
        return json.loads(completed.stdout)

    def test_read_only_does_not_create_project(self):
        rows, errors = store.records(self.project)
        self.assertEqual((rows, errors), ([], []))
        self.assertFalse(self.project.exists())

    def test_chinese_identity_and_immutable_snapshots(self):
        first = self.save(self.payload)
        original = Path(first["saved"]).read_bytes()
        second = self.save(self.payload)
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(Path(first["saved"]).read_bytes(), original)
        rows, errors = store.records(self.project)
        self.assertEqual(len(rows), 2)
        self.assertFalse(errors)
        self.assertEqual(rows[0][3]["claims"][0]["kind"], "user_statement")

    def test_project_mix_rejected_without_new_record(self):
        self.save(self.payload)
        other = dict(self.payload, project_id="另一业务")
        with self.assertRaisesRegex(ValueError, "project_id"):
            self.save(other)
        self.assertEqual(len(store.records(self.project)[0]), 1)

    def test_explicit_correction_preserves_old_claim(self):
        self.save(self.payload)
        updated = dict(self.payload, claims=[{"id": "b", "text": "只有一人实际支付", "kind": "material_record", "source": "付款记录", "supersedes": ["a"]}])
        self.save(updated)
        rows, _ = store.records(self.project)
        self.assertEqual(rows[0][3]["claims"][0]["id"], "a")
        self.assertEqual(rows[1][3]["claims"][0]["supersedes"], ["a"])
        altered = dict(self.payload, claims=[dict(self.payload["claims"][0], text="悄悄改写")])
        with self.assertRaisesRegex(ValueError, "new ID"):
            self.save(altered)

    def test_unknown_correction_and_invalid_kind_rejected(self):
        invalid = dict(self.payload, claims=[dict(self.payload["claims"][0], supersedes=["missing"])])
        with self.assertRaisesRegex(ValueError, "unknown prior"):
            self.save(invalid)
        self.assertFalse(self.project.exists())
        invalid["claims"][0]["kind"] = "guaranteed_truth"
        with self.assertRaisesRegex(ValueError, "evidence kind"):
            self.save(invalid)

    def test_corruption_visible_and_save_stops(self):
        self.save(self.payload)
        (self.project / "snapshots/bad.json").write_text("broken", encoding="utf-8")
        rows, errors = store.records(self.project)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 1)
        with self.assertRaisesRegex(ValueError, "malformed"):
            self.save(self.payload)

    def test_cli_latest_uses_record_time_not_mtime(self):
        first = self.save(self.payload)
        second = self.save(dict(self.payload, title="第二轮"))
        import os
        os.utime(first["saved"], (2000000000, 2000000000))
        completed = subprocess.run([sys.executable, str(SCRIPT), "show", "--project-dir", str(self.project)], capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(json.loads(completed.stdout)["record"]["id"], second["id"])

    def test_manual_archive_can_be_read_and_corrected_by_script(self):
        # This is the no-Python layout: create complete JSON files directly,
        # without calling save or using internal metadata generation helpers.
        guide = (ROOT / "skills/nin-project/references/project-records.md").read_text(encoding="utf-8")
        examples = [json.loads(block) for block in re.findall(r"```json\s*\n(.*?)\n```", guide, re.S)]
        meta = next(value for value in examples if set(value) == {"schema_version", "project_id"})
        manual = next(value for value in examples if "schema_version" in value and "claims" in value)
        folder = self.project / "snapshots"
        folder.mkdir(parents=True)
        (self.project / "project.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8",
        )
        path = folder / (manual["id"] + ".json")
        path.write_text(json.dumps(manual, ensure_ascii=False), encoding="utf-8")
        original = path.read_bytes()
        restored = self.cli("show")
        self.assertEqual(restored["record"], manual)
        self.assertEqual(restored["errors"], [])
        updated = dict(manual, claims=[{
            "id": "manual-correction", "text": "付款记录表明一人付款", "kind": "material_record",
            "source": "付款记录", "supersedes": [manual["claims"][0]["id"]],
        }])
        self.save(updated)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(len(self.cli("list")["records"]), 2)

    def test_manual_snapshot_without_identity_is_visible_as_error(self):
        folder = self.project / "snapshots"
        folder.mkdir(parents=True)
        row = dict(self.payload, schema_version=1, id=uuid.uuid4().hex, created_at="2026-01-01T10:00:00+08:00")
        (folder / "manual.json").write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        restored = self.cli("show")
        self.assertIsNone(restored["record"])
        self.assertIn("Project identity mismatch", restored["errors"][0]["error"])
        self.assertFalse((self.project / "project.json").exists())

    def test_cross_file_claim_conflicts_visible_on_list_and_show(self):
        first = self.save(self.payload)
        original = Path(first["saved"]).read_bytes()
        row = json.loads(original)
        row["id"] = uuid.uuid4().hex
        row["claims"][0]["text"] = "同一 ID 的不同结论"
        conflicting_path = self.project / "snapshots/legacy-conflict.json"
        conflicting_path.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
        for command in ("list", "show"):
            with self.subTest(command=command):
                output = self.cli(command)
                self.assertEqual(len(output["errors"]), 1)
                error = output["errors"][0]
                self.assertEqual(error["claim_id"], "a")
                self.assertEqual(
                    {Path(error["path"]).resolve(), Path(error["conflicting_path"]).resolve()},
                    {conflicting_path.resolve(), Path(first["saved"]).resolve()},
                )
                self.assertIn("conflicting content", error["error"])
        with self.assertRaisesRegex(ValueError, "conflicting records"):
            self.save(self.payload)
        self.assertEqual(Path(first["saved"]).read_bytes(), original)
        self.assertEqual(len(list((self.project / "snapshots").glob("*.json"))), 2)

    def test_competing_claim_writers_are_serialized_across_processes(self):
        first = self.save(self.payload)
        original = Path(first["saved"]).read_bytes()
        payload_a = dict(self.payload, claims=[dict(self.payload["claims"][0], id="shared", text="版本甲")])
        payload_b = dict(self.payload, claims=[dict(self.payload["claims"][0], id="shared", text="版本乙")])
        gate = self.base / "start"
        gate.touch()
        release = self.base / "release-history"
        read_ready = self.base / "a-read-history"
        writer_a = self.writer("writer-a", payload_a, gate, release, read_ready)
        self.wait_for(read_ready, writer_a)
        writer_b = self.writer("writer-b", payload_b, gate)
        try:
            # A has read old state but has not appended yet. B must remain
            # blocked rather than validate the same old state and also save.
            with self.assertRaises(subprocess.TimeoutExpired):
                writer_b.communicate(timeout=0.5)
        finally:
            release.touch()
        out_a, err_a = writer_a.communicate(timeout=10)
        out_b, err_b = writer_b.communicate(timeout=10)
        self.assertEqual(writer_a.returncode, 0, err_a)
        self.assertEqual(writer_b.returncode, 1, out_b)
        self.assertIn("new ID", json.loads(err_b)["error"])
        rows, errors = store.records(self.project)
        self.assertEqual(len(rows), 2)
        self.assertFalse(errors)
        self.assertEqual(Path(first["saved"]).read_bytes(), original)
        self.assertEqual(json.loads(out_a)["project_id"], "中文业务")

    def test_concurrent_first_saves_with_distinct_claims_all_succeed(self):
        gate = self.base / "start"
        children = []
        for number in range(4):
            payload = dict(self.payload, claims=[dict(self.payload["claims"][0], id=f"claim-{number}")])
            children.append(self.writer(f"writer-{number}", payload, gate))
        gate.touch()
        for child in children:
            out, err = child.communicate(timeout=15)
            self.assertEqual(child.returncode, 0, err)
            self.assertEqual(json.loads(out)["project_id"], "中文业务")
        rows, errors = store.records(self.project)
        self.assertEqual(len(rows), 4)
        self.assertFalse(errors)

    def test_lock_timeout_and_process_exit_release(self):
        marker = self.base / "locked"
        child = self.launch(LOCK_HOLDER, SCRIPT, self.project, marker)
        self.wait_for(marker, child)
        with self.assertRaisesRegex(TimeoutError, "Project is busy"):
            with store.project_lock(self.project, timeout=0.1):
                self.fail("Contending writer obtained the lock")
        child.kill()
        child.communicate(timeout=10)
        with store.project_lock(self.project, timeout=1):
            pass
        self.save(self.payload)
        self.assertFalse(store.records(self.project)[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
