#!/usr/bin/env python3
"""
Master script: reproduce all analyses from a single command.

Usage:
    cd lets-go-indigo-checkmate/
    python scripts/run_all.py \
        --indigo-pdf <path> \
        --checkmate-pdf <path> \
        --checkmate-s1ab <path> \
        --checkmate-s1cd <path>
"""
from __future__ import annotations
import argparse, subprocess, sys, json, time
from pathlib import Path


def run_step(label: str, cmd: list[str], log_dir: Path):
    """Run a subprocess step with logging."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    log_file = log_dir / f"{label.replace(' ', '_').lower()}.log"
    t0 = time.time()
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(Path(__file__).parent.parent)
    )
    elapsed = time.time() - t0
    with open(log_file, "w") as f:
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Return code: {result.returncode}\n")
        f.write(f"Elapsed: {elapsed:.1f}s\n\n")
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n=== STDERR ===\n")
        f.write(result.stderr)

    if result.returncode != 0:
        print(f"  WARNING: {label} returned code {result.returncode}")
        print(f"  See {log_file} for details")
    else:
        print(f"  Completed in {elapsed:.1f}s")
    return result.returncode


def main():
    ap = argparse.ArgumentParser(description="Reproduce all analyses")
    ap.add_argument("--indigo-pdf", required=True)
    ap.add_argument("--checkmate-pdf", required=True)
    ap.add_argument("--checkmate-s1ab", default=None)
    ap.add_argument("--checkmate-s1cd", default=None)
    args = ap.parse_args()

    log_dir = Path("outputs/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable

    # Step 1: INDIGO
    run_step("INDIGO extraction and reconstruction", [
        py, "scripts/run_indigo.py",
        "--pdf", args.indigo_pdf,
        "--out", "data/extracted/indigo",
        "--results", "outputs",
        "--figures", "figures",
    ], log_dir)

    # Step 2: CheckMate blinded
    run_step("CheckMate blinded", [
        py, "scripts/run_checkmate_blinded.py",
        "--pdf", args.checkmate_pdf,
        "--out", "data/extracted/checkmate_blinded",
        "--results", "outputs",
        "--figures", "figures",
    ], log_dir)

    # Step 3: CheckMate unblinded
    cm_unblinded_cmd = [
        py, "scripts/run_checkmate_unblinded.py",
        "--pdf", args.checkmate_pdf,
        "--blinded-results", "outputs/cm_blinded_os_envelope_summaries.csv",
        "--out", "data/extracted/checkmate_unblinded",
        "--results", "outputs",
        "--figures", "figures",
    ]
    if args.checkmate_s1ab:
        cm_unblinded_cmd += ["--supplement-img-s1ab", args.checkmate_s1ab]
    if args.checkmate_s1cd:
        cm_unblinded_cmd += ["--supplement-img-s1cd", args.checkmate_s1cd]

    run_step("CheckMate unblinded", cm_unblinded_cmd, log_dir)

    # Step 4: Generate figures and tables
    run_step("Generate figures and tables", [
        py, "scripts/generate_figures_tables.py",
    ], log_dir)

    # Step 5: Merge results
    print("\n=== Merging results summaries ===")
    combined = {}
    for jf in Path("outputs").glob("results_summary_*.json"):
        with open(jf) as f:
            combined[jf.stem] = json.load(f)
    with open("outputs/results_summary.json", "w") as f:
        json.dump(combined, f, indent=2)

    print("\n=== All steps complete ===")
    print(f"Results in: outputs/")
    print(f"Figures in: figures/")
    print(f"Data in:    data/")
    print(f"Logs in:    outputs/logs/")


if __name__ == "__main__":
    main()
