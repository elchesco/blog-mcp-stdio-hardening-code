"""Round 0: the shape of CVE-2026-105740, reduced to the two lines that matter.

DEAD END on purpose. Kept to show why "validate the command" is the wrong fix.

Langflow before 1.9.0 accepted an MCP server config (command, args, env) from
any authenticated user and later started it like this (from the advisory,
src/lfx/src/lfx/base/mcp/util.py):

    args=["-c", f"exec {command_str} || echo 'Command failed...'"]

and merged the user's `env` dict into the child's environment. So:
  - the command string is shell source, not an argv;
  - env can set LD_PRELOAD or PATH, which changes what any binary loads;
  - it runs when the server list is fetched, not when someone "runs" it.

This demo runs only harmless commands on your own machine.

Usage:
  python3 vulnerable_spawn.py
"""

import os
import subprocess


def start_stdio_server(command_str: str, env: dict[str, str]) -> str:
    out = subprocess.run(
        ["bash", "-c", f"exec {command_str} || echo 'Command failed...'"],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=5,
    )
    return out.stdout.strip()


if __name__ == "__main__":
    # What the form expects: one program.
    print("1:", start_stdio_server("echo mcp-server-started", {}))
    # `exec` replaces the shell, so `; second-command` never runs. That looks
    # like a mitigation and is not one: command substitution runs first.
    print("2:", start_stdio_server("echo mcp-server-started; echo chained", {}))
    print("3:", start_stdio_server("echo mcp-server-started $(echo substitution-ran-before-exec)", {}))
    # A "safe" binary name plus a PATH override still picks the attacker's binary.
    os.makedirs("/tmp/mcp-demo-bin", exist_ok=True)
    with open("/tmp/mcp-demo-bin/node", "w") as f:
        f.write("#!/bin/sh\necho 'not node: PATH from the env field won'\n")
    os.chmod("/tmp/mcp-demo-bin/node", 0o755)
    print("4:", start_stdio_server("node --version", {"PATH": "/tmp/mcp-demo-bin:/usr/bin:/bin"}))
