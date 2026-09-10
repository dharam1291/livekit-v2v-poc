#!/usr/bin/env python3
"""Generate Computer Use gRPC stubs into tools.computer_use_grpc.

Vendored proto lives next to the stubs so Agent X does not manually copy
from Machine Y at runtime — start_app.sh runs this automatically.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO_DIR = ROOT / "src" / "tools" / "computer_use_grpc"
PROTO = PROTO_DIR / "computer_use.proto"
OUT = PROTO_DIR


def main() -> int:
    if not PROTO.is_file():
        print(f"Missing proto: {PROTO}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "__init__.py").touch(exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"--proto_path={PROTO_DIR}",
        f"--python_out={OUT}",
        f"--grpc_python_out={OUT}",
        PROTO.name,
    ]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    grpc_file = OUT / "computer_use_pb2_grpc.py"
    text = grpc_file.read_text(encoding="utf-8")
    text = text.replace(
        "import computer_use_pb2 as computer__use__pb2",
        "from . import computer_use_pb2 as computer__use__pb2",
    )
    grpc_file.write_text(text, encoding="utf-8")
    print(f"Generated stubs in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
