"""Run the unit tests, one process per test module, in parallel.

The default run skips the slow exhaustive checks, for iterating; --full includes them (SCHLIEREN_TESTS=full,
see schlieren.testing). Run it from the repo root. Plain `python -m unittest` still works, one module or all.
"""

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from schlieren.testing import FULL_ENV

# Test modules with the heaviest fixtures, started first so they overlap the rest.
HEAVY = {"test_light_source", "test_camera_support", "test_carriage", "test_slit_head"}


def _run(module: str, env: dict) -> tuple[str, float, int, str]:
    start = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-m", "unittest", f"tests.{module}"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return module, time.monotonic() - start, done.returncode, done.stderr + done.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="*", help="Test modules, such as test_frame (default: all)")
    parser.add_argument("--full", action="store_true", help="Include the slow tests")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1, help="Parallel processes")
    args = parser.parse_args()

    tests = Path("tests")
    available = sorted(path.stem for path in tests.glob("test_*.py"))
    modules = [m.removesuffix(".py").removeprefix("tests.") for m in args.modules] or available
    unknown = [m for m in modules if m not in available]
    if unknown:
        sys.exit(f"No such test module: {', '.join(unknown)} (in {tests.resolve()})")
    env = {**os.environ, FULL_ENV: "full" if args.full else ""}

    start = time.monotonic()
    failed, ran, skipped = [], 0, 0
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(_run, m, env) for m in sorted(modules, key=lambda m: m not in HEAVY)]
        for future in as_completed(futures):
            module, seconds, code, output = future.result()
            count = re.search(r"Ran (\d+) tests?", output)
            skips = re.search(r"skipped=(\d+)", output)
            ran += int(count.group(1)) if count else 0
            skipped += int(skips.group(1)) if skips else 0
            print(f"{'ok  ' if code == 0 else 'FAIL'} {module:<24}{seconds:6.1f}s", flush=True)
            if code:
                failed.append((module, output))
    for module, output in failed:
        print(f"\n===== {module} =====\n{output}")
    note = "" if args.full else f", {skipped} slow skipped (--full runs them)"
    print(f"\n{ran} tests in {time.monotonic() - start:.1f}s{note}; {len(failed)} module(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
