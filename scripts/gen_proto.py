#!/usr/bin/env python3
"""
Script to generate Python protobuf code from .proto files and fix relative imports.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Paths relative to the repository root
PROTO_SRC_DIR = Path("proto")
PROTO_OUT_DIR = Path("custom_components/tesla_ble/core/proto")


def clean_output_dir():
    """Remove generated files but keep __init__.py and google folder structure."""
    if not PROTO_OUT_DIR.exists():
        PROTO_OUT_DIR.mkdir(parents=True)


def generate_protos():
    """Run grpc_tools.protoc"""
    print("Generating protobuf files...")

    # Calculate relative path from PROTO_SRC_DIR to PROTO_OUT_DIR
    rel_out_dir = os.path.relpath(PROTO_OUT_DIR.absolute(), PROTO_SRC_DIR.absolute())

    cmd_args = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        "--proto_path=.",
        f"--python_out={rel_out_dir}",
        f"--pyi_out={rel_out_dir}",
    ]

    # Glob files inside proto dir
    cwd_proto_files = list(Path(PROTO_SRC_DIR).glob("*.proto"))
    cwd_proto_files_names = [p.name for p in cwd_proto_files]

    # Add google/protobuf/timestamp.proto
    cmd_args.extend(cwd_proto_files_names)
    cmd_args.append("google/protobuf/timestamp.proto")

    print(f"Running command in {PROTO_SRC_DIR}: {' '.join(cmd_args)}")

    result = subprocess.run(cmd_args, cwd=PROTO_SRC_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error generating protobufs:")
        print(result.stderr)
        sys.exit(1)

    print("Protoc success.")


def fix_imports():
    """Fix imports in generated files to be relative."""
    print("Fixing imports...")

    files_to_fix = list(PROTO_OUT_DIR.glob("*.py")) + list(PROTO_OUT_DIR.glob("*.pyi"))

    for file_path in files_to_fix:
        if file_path.name == "__init__.py":
            continue

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # 1. Make local imports relative e.g. `import vcsec_pb2` -> `from . import ...`
        # logic: import (something)_pb2 -> from . import \1_pb2
        content = re.sub(
            r"^import ([a-zA-Z0-9_]+_pb2)",
            r"from . import \1",
            content,
            flags=re.MULTILINE,
        )

        # 2. Make vendored google protobuf import relative
        # `from google.protobuf import timestamp_pb2` -> `from .google.protobuf`
        content = re.sub(
            r"^(from google\.protobuf import timestamp_pb2)",
            r"from .google.protobuf import timestamp_pb2",
            content,
            flags=re.MULTILINE,
        )

        # 3. Fix alias if present (from Makefile)
        # `as google_dot_protobuf_dot_timestamp__pb2` -> `as _timestamp_pb2`
        content = content.replace(
            " as google_dot_protobuf_dot_timestamp__pb2", " as _timestamp_pb2"
        )
        content = content.replace(
            "google_dot_protobuf_dot_timestamp__pb2.", "_timestamp_pb2."
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    print("Imports fixed.")


def main():
    if not shutil.which("uv"):
        print("uv not found. Please install uv.")
        # Attempt minimal fallback or fail?
        # The user instructions say uv is used.

    # Ensure dependencies are installed could be part of a larger setup,
    # but here we assume 'uv run' will handle env if we called it via uv run.
    # Since we call sys.executable, we assume we are running INSIDE the venv
    # or environment where grpcio-tools is installed.

    generate_protos()
    fix_imports()


if __name__ == "__main__":
    main()
