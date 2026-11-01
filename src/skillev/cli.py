"""skillev command line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import store
from .htmlreport import render_html
from .report import compare, render
from .runner import run_suite
from .scaffold import SCAFFOLD_FILES, write_scaffold


def _print(text: str) -> None:
    sys.stdout.write(text + "\n")


def cmd_init(args) -> int:
    target = Path(args.dir or ".").resolve()
    created = write_scaffold(target)
    if not created:
        _print(f"evals/ already scaffolded at {target} — nothing to do.")
        return 0
    for rel in created:
        _print(f"created {rel}")
    _print("\nNext: edit the case task/grader, then run `skillev run`.")
    return 0


def cmd_run(args) -> int:
    skill_dir = Path(args.dir or ".").resolve()
    suite = _load(skill_dir)
    result = run_suite(suite, adapter_name=args.agent)

    # The current run is not saved yet, so the newest run on disk is the baseline.
    baseline = None if args.no_baseline else store.latest(skill_dir)
    diffs = None
    if baseline is not None:
        diffs, gate_failed = compare(result, baseline)

    if args.json:
        payload = result.to_dict()
        if diffs is not None:
            payload["diffs"] = [vars(d) for d in diffs]
            payload["gate"] = "FAIL" if any(d.status == "gate" for d in diffs) else "PASS"
        _print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print(render(result, diffs, baseline.run_id if baseline else None))

    out = store.save(skill_dir, result)
    if not args.json:
        _print(f"saved: {out.relative_to(skill_dir)}")
    if args.html:
        Path(args.html).write_text(
            render_html(result, diffs, baseline.run_id if baseline else None), encoding="utf-8"
        )
        _print(f"html report: {args.html}")

    if diffs is not None and any(d.status == "gate" for d in diffs):
        return 1
    return 0


def cmd_gate(args) -> int:
    """Compare the newest stored run against a baseline without re-running."""
    skill_dir = Path(args.dir or ".").resolve()
    runs = store.list_runs(skill_dir)
    if not runs:
        _print("no runs yet — run `skillev run` first")
        return 2
    baseline_id = args.against or (runs[-2].stem if len(runs) >= 2 else None)
    if baseline_id is None:
        _print("need at least 2 runs to gate (nothing to compare against)")
        return 2
    current = store.load(skill_dir, runs[-1].stem)
    baseline = store.load(skill_dir, baseline_id)
    if current is None or baseline is None:
        _print(f"run not found: {baseline_id}")
        return 2
    diffs, failed = compare(current, baseline)
    _print(render(current, diffs, baseline.run_id))
    return 1 if failed else 0


def cmd_show(args) -> int:
    """Show one case's check details and transcript from a stored run."""
    skill_dir = Path(args.dir or ".").resolve()
    runs = store.list_runs(skill_dir)
    if not runs:
        _print("no runs yet — run `skillev run` first")
        return 2
    run_id = args.run or runs[-1].stem
    result = store.load(skill_dir, run_id)
    if result is None:
        _print(f"run not found: {run_id}")
        return 2
    matches = [c for c in result.cases if c.case == args.case]
    if not matches:
        _print(f"case '{args.case}' not found in run {run_id}.")
        _print("available: " + ", ".join(c.case for c in result.cases))
        return 2
    c = matches[0]
    _print(f"case: {c.case}   run: {run_id}   score: {c.score}   grade: {c.grade}")
    for ck in c.checks:
        mark = "PASS" if ck.passed else "FAIL"
        _print(f"  [{mark}] {ck.type}" + (f" — {ck.detail}" if ck.detail else ""))
    _print("\n--- transcript ---")
    _print(c.transcript or "(empty)")
    return 0


def cmd_history(args) -> int:
    skill_dir = Path(args.dir or ".").resolve()
    runs = store.list_runs(skill_dir)
    if not runs:
        _print("no runs yet — try `skillev run`")
        return 0
    if args.json:
        _print(json.dumps([r.stem for r in runs], indent=2))
        return 0
    for r in runs:
        data = json.loads(r.read_text(encoding="utf-8"))
        _print(f"{r.stem}  avg={data.get('avg_score')}  adapter={data.get('adapter')}  branch={data.get('git_branch')}")
    return 0


def _load(skill_dir: Path):
    from .spec import load_suite

    return load_suite(skill_dir)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="skillev",
        description="Regression test harness for agent skills.",
    )
    parser.add_argument("--version", action="version", version=f"skillev {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold an evals/ directory in a skill repo")
    p_init.add_argument("dir", nargs="?", help="skill repo directory (default: .)")
    p_init.set_defaults(fn=cmd_init)

    p_run = sub.add_parser("run", help="run the eval suite")
    p_run.add_argument("dir", nargs="?", help="skill repo directory (default: .)")
    p_run.add_argument("--agent", help="override agent adapter (mock, claude)")
    p_run.add_argument("--no-baseline", action="store_true", help="skip regression comparison")
    p_run.add_argument("--json", action="store_true", help="machine-readable output")
    p_run.add_argument("--html", metavar="FILE", help="also write a self-contained HTML report")
    p_run.set_defaults(fn=cmd_run)

    p_gate = sub.add_parser(
        "gate", help="compare the newest run against a baseline; exit 1 on regression"
    )
    p_gate.add_argument("dir", nargs="?", help="skill repo directory (default: .)")
    p_gate.add_argument("--against", help="baseline run id (default: second-newest run)")
    p_gate.set_defaults(fn=cmd_gate)

    p_show = sub.add_parser("show", help="show one case's checks and transcript from a run")
    p_show.add_argument("case", help="case name")
    p_show.add_argument("dir", nargs="?", help="skill repo directory (default: .)")
    p_show.add_argument("--run", help="run id (default: newest run)")
    p_show.set_defaults(fn=cmd_show)

    p_hist = sub.add_parser("history", help="list past runs")
    p_hist.add_argument("dir", nargs="?", help="skill repo directory (default: .)")
    p_hist.add_argument("--json", action="store_true")
    p_hist.set_defaults(fn=cmd_history)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
