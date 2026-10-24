"""Round 1: start stdio MCP servers from an allowlist, never from user input.

The fix is not "validate the command string". Any command is code execution;
a perfect parser only proves the attacker typed a valid one. The fix is:

  1. Users pick a server by ID. They never send a command.
  2. Each ID maps to an exact, pinned argv, reviewed like a dependency.
  3. No shell: argv goes straight to execve.
  4. The child gets a minimal environment built from an allowlist, never the
     caller's env merged with user input.
  5. Registering a new ID is an admin change with an audit record.

Process isolation (separate OS user, container, no egress) is the next layer
and lives outside this file.

Usage:
  python3 safe_spawn.py
"""

import os
import shutil
import subprocess
from dataclasses import dataclass, field

ENV_ALLOWLIST = {"HOME", "LANG", "TZ"}
SAFE_PATH = "/usr/local/bin:/usr/bin:/bin"


@dataclass(frozen=True)
class ServerSpec:
    argv: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)  # fixed values, set by admins


REGISTRY: dict[str, ServerSpec] = {
    # @playwright/mcp@0.0.83, installed into the image at build time. npx is
    # not on the request path at all, so nothing is fetched at start.
    "playwright": ServerSpec(argv=("/usr/local/bin/playwright-mcp", "--headless")),
    "echo-demo": ServerSpec(argv=("/bin/echo", "mcp-server-started")),
}


class NotAllowed(Exception):
    pass


def child_env(spec: ServerSpec) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k in ENV_ALLOWLIST}
    env["PATH"] = SAFE_PATH
    env.update(spec.env)
    return env


def start_stdio_server(server_id: str, user_args: list[str] | None = None) -> str:
    spec = REGISTRY.get(server_id)
    if spec is None:
        raise NotAllowed(f"unknown MCP server id: {server_id!r}")
    if user_args:
        raise NotAllowed("arguments are part of the reviewed spec, not the request")
    if not os.path.isabs(spec.argv[0]) or shutil.which(spec.argv[0]) is None:
        raise NotAllowed(f"binary not installed: {spec.argv[0]}")
    out = subprocess.run(list(spec.argv), env=child_env(spec), shell=False, capture_output=True, text=True, timeout=5)
    return out.stdout.strip()


if __name__ == "__main__":
    print("1:", start_stdio_server("echo-demo"))
    for attempt in (
        ("bash -c 'echo pwned'", None),
        ("echo-demo", ["$(echo substitution)"]),
        ("playwright", None),
    ):
        try:
            start_stdio_server(*attempt)
        except NotAllowed as e:
            print("refused:", e)
