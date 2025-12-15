#!/usr/bin/env python3
"""Quick terminal dashboard for Walmart + Jenni import pipelines.

Designed for SSH/terminal use (no web server). Prints a single snapshot.
Run it repeatedly, or use `watch -n 5 python3 tools/dashboard.py`.

It is intentionally dependency-free.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
LOGS_DIR = REPO_ROOT / "logs"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _jenni_progress_path() -> Path:
    return Path(os.getenv("JENNI_PROGRESS_FILE", "results/jenni_progress.json")).expanduser()


def _age_seconds(path: Path) -> int | None:
    try:
        return int(datetime.now().timestamp() - path.stat().st_mtime)
    except FileNotFoundError:
        return None


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, cwd=str(REPO_ROOT), stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="ignore").strip()
    except subprocess.CalledProcessError as e:
        return (e.output or b"").decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return str(e)


def _pgrep(pattern: str) -> list[str]:
    out = _run(["bash", "-lc", f"pgrep -af {pattern!r} || true"])
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # Filter out the helper shell invocation that runs pgrep itself
    lines = [ln for ln in lines if "bash -lc pgrep" not in ln]
    return lines


def _tail(path: Path, n: int = 10) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return lines[-n:]
    except Exception:
        return []


def _count_walmart_imported() -> int:
    p = RESULTS_DIR / "walmart_import_index.json"
    if not p.exists():
        return 0
    try:
        data = _read_json(p)
        if not isinstance(data, dict):
            return 0

        # Historical versions used different casing and even different types.
        # - newer: {"itemIds": {"123": {...}, ...}}
        # - older: {"itemIds": ["123", "456", ...]}
        for key in ("itemIds", "ItemIds"):
            m = data.get(key)
            if isinstance(m, dict):
                return len(m)
            if isinstance(m, list):
                return len([x for x in m if str(x).strip()])
        return 0
    except Exception:
        return 0


def _walmart_status() -> dict[str, Any]:
    out_dir = RESULTS_DIR / "walmart_keywords"
    ndjson_files = sorted(out_dir.glob("*.ndjson")) if out_dir.exists() else []
    total_lines = 0
    newest_age = None
    for p in ndjson_files:
        try:
            # fast-ish line count without external deps
            with p.open("rb") as f:
                total_lines += sum(1 for _ in f)
            a = _age_seconds(p)
            if a is not None:
                newest_age = a if newest_age is None else min(newest_age, a)
        except Exception:
            continue

    importer_logs = {
        "clearance": RESULTS_DIR / "pipeline_logs" / "clearance_import" / "importer.log",
        "makeup": RESULTS_DIR / "pipeline_logs" / "makeup_import" / "importer.log",
        "toys": RESULTS_DIR / "pipeline_logs" / "toys_import" / "importer.log",
    }

    daily_limit = 0
    per_sec = 0
    last_errors: dict[str, str] = {}
    for name, lp in importer_logs.items():
        tail = "\n".join(_tail(lp, 200))
        daily_limit += len(re.findall(r"Daily variant creation limit reached", tail, re.IGNORECASE))
        per_sec += len(re.findall(r"Exceeded\s+\d+\s+calls per second", tail, re.IGNORECASE))
        # show the latest ERROR-ish line
        for ln in reversed(tail.splitlines()):
            if "ERROR" in ln or "Daily variant" in ln or "Exceeded" in ln:
                last_errors[name] = ln.strip()
                break

    return {
        "ndjson_files": len(ndjson_files),
        "ndjson_total_lines": total_lines,
        "ndjson_newest_age_sec": newest_age,
        "imported_shopify_count": _count_walmart_imported(),
        "importer_procs": _pgrep("tools/continuous_import.py"),
        "daily_limit_hits_recent": daily_limit,
        "per_second_hits_recent": per_sec,
        "last_error_lines": last_errors,
    }


def _jenni_status() -> dict[str, Any]:
    ckpt = RESULTS_DIR / "jenni_prod_enum_checkpoint.json"
    ckpt_data = None
    if ckpt.exists():
        try:
            ckpt_data = _read_json(ckpt)
        except Exception:
            ckpt_data = None

    prog_path = _jenni_progress_path()
    prog = _read_json(prog_path)
    prog_age = _age_seconds(prog_path)
    prog_summary = None
    if isinstance(prog, dict):
        imported = prog.get("imported")
        processed = prog.get("processed")
        unique_gtins = prog.get("unique_gtins")
        parts = [f"imported={imported}"]
        if processed is not None:
            parts.append(f"processed={processed}")
        if unique_gtins is not None:
            parts.append(f"unique_gtins={unique_gtins}")
        parts.append(f"age_s={prog_age}")
        prog_summary = " ".join(parts)

    return {
        "procs": _pgrep("import_jenni_sku_graph_products.py"),
        "enum_checkpoint": ckpt_data,
        "enum_checkpoint_age_sec": _age_seconds(ckpt),
        "progress": prog,
        "progress_age_sec": prog_age,
        "progress_summary": prog_summary,
        "log_path": str(LOGS_DIR / "jenni_import.out"),
        "log_lines": (LOGS_DIR / "jenni_import.out").read_text(encoding="utf-8", errors="ignore").count("\n")
        if (LOGS_DIR / "jenni_import.out").exists()
        else 0,
        "log_tail": _tail(LOGS_DIR / "jenni_import.out", 12),
    }


def main() -> int:
    w = _walmart_status()
    j = _jenni_status()

    print("=" * 72)
    print(f"Dashboard @ {datetime.now().isoformat(timespec='seconds')}")
    print("repo:", REPO_ROOT)

    print("\n## Walmart")
    print(f"NDJSON files: {w['ndjson_files']}  total lines: {w['ndjson_total_lines']}  newest age(s): {w['ndjson_newest_age_sec']}")
    print(f"Imported into Shopify (index count): {w['imported_shopify_count']}")
    print(f"Importer processes: {len(w['importer_procs'])}")
    for ln in w["importer_procs"][:5]:
        print("  ", ln)
    if w["daily_limit_hits_recent"] or w["per_second_hits_recent"]:
        print(f"Recent log signals: daily_limit={w['daily_limit_hits_recent']} per_second={w['per_second_hits_recent']}")
        for k, v in w["last_error_lines"].items():
            print(f"  {k}: {v}")

    print("\n## Jenni SKU Graph")
    print(f"Processes: {len(j['procs'])}")
    for ln in j["procs"][:5]:
        print("  ", ln)
    if j.get("progress_summary"):
        print("Progress:", j["progress_summary"])
    else:
        print(f"Progress: (no progress file yet: {_jenni_progress_path()})")
    print("Checkpoint:", j["enum_checkpoint"], f"age(s)={j['enum_checkpoint_age_sec']}")
    print(f"Log: {j['log_path']} lines={j['log_lines']}")
    if j["log_tail"]:
        print("Last log lines:")
        for ln in j["log_tail"]:
            print("  ", ln)

    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
