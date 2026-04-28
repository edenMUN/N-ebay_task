import argparse
import os
import shutil
import subprocess
import sys
from typing import List


def _build_pytest_command(extra_args: List[str], trace_on: bool) -> List[str]:
    trace_flag = ["--trace-on"] if trace_on else []
    return [sys.executable, "-m", "pytest", "--alluredir=allure-results", *trace_flag, *extra_args]


def _resolve_allure_command() -> List[str] | None:
    # On Windows, prefer .bat and run through cmd for reliable process creation.
    if os.name == "nt":
        allure_bat = shutil.which("allure.bat")
        if allure_bat:
            return ["cmd", "/c", allure_bat, "serve", "allure-results"]
        allure_cmd = shutil.which("allure")
        if allure_cmd:
            return ["cmd", "/c", allure_cmd, "serve", "allure-results"]
        return None

    for candidate in ("allure", "allure.bat"):
        if shutil.which(candidate):
            return [candidate, "serve", "allure-results"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--trace-on",
        action="store_true",
        default=False,
        help="Enable Playwright tracing and attach per-test trace to Allure.",
    )
    args, extra_args = parser.parse_known_args(sys.argv[1:])

    pytest_command = _build_pytest_command(extra_args, trace_on=args.trace_on)

    pytest_result = subprocess.run(pytest_command, check=False)

    if not os.getenv("CI"):
        allure_command = _resolve_allure_command()
        if not allure_command:
            print(
                "[WARN] Allure CLI was not found on PATH. "
                "Install it and run `allure serve allure-results` manually."
            )
        else:
            try:
                subprocess.run(allure_command, check=False)
            except KeyboardInterrupt:
                print("\n[INFO] Allure report server stopped by user.")
            except FileNotFoundError:
                print(
                    "[WARN] Allure CLI could not be started from this terminal session. "
                    "Open a new terminal and run `allure serve allure-results` manually."
                )

    return pytest_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
