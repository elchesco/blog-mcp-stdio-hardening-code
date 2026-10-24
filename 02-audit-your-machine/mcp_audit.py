"""Round 2: inventory every MCP server your coding agents will start, and flag the risky ones.

A stdio MCP server is a command line that your agent runs as you. This script
reads the usual config locations, lists every server, and flags:

  STDIO        the server is a local process (runs with your user's rights)
  UNPINNED     npx/uvx/bunx package with no version, or @latest
  AUTO-YES     npx -y / --yes: installs without asking
  NOT-FOUND    the npm/PyPI package does not exist (typo or unclaimed scope:
               anyone can register it and your next session runs their code)
  ENV          env keys that change what the interpreter loads
               (LD_PRELOAD, DYLD_*, NODE_OPTIONS, PYTHONPATH, PATH, ...)
  PLAIN-HTTP   remote server over http://

Reads only. Makes one HTTPS GET per package to registry.npmjs.org / pypi.org.

Usage:
  python3 -I mcp_audit.py            # scan the default locations
  python3 -I mcp_audit.py --offline  # skip the registry lookups
"""

import argparse
import glob
import json
import os
import re
import urllib.error
import urllib.request

HOME = os.path.expanduser("~")
RISKY_ENV = re.compile(r"^(LD_|DYLD_)|^(NODE_OPTIONS|NODE_PATH|PYTHONPATH|PYTHONSTARTUP|PATH|BASH_ENV|ENV|PERL5OPT|RUBYOPT)$")
RUNNERS = {"npx": "npm", "bunx": "npm", "pnpm": "npm", "uvx": "pypi", "pipx": "pypi"}


def sources() -> list[tuple[str, dict]]:
    found = []
    claude_json = os.path.join(HOME, ".claude.json")
    if os.path.exists(claude_json):
        data = json.load(open(claude_json))
        if data.get("mcpServers"):
            found.append(("~/.claude.json (user scope)", data["mcpServers"]))
        for project, cfg in (data.get("projects") or {}).items():
            if cfg.get("mcpServers"):
                found.append((f"~/.claude.json (local scope: {short(project)})", cfg["mcpServers"]))
    patterns = [
        "~/*/.mcp.json",
        "~/*/*/.mcp.json",
        "~/.cursor/mcp.json",
        "~/.kiro/settings/mcp.json",
        "~/*/.kiro/settings/mcp.json",
        "~/*/*/.kiro/settings/mcp.json",
        "~/Library/Application Support/Claude/claude_desktop_config.json",
        "~/.config/Claude/claude_desktop_config.json",
    ]
    for pattern in patterns:
        for path in glob.glob(os.path.expanduser(pattern)):
            try:
                servers = json.load(open(path)).get("mcpServers")
            except (OSError, ValueError):
                continue
            if servers:
                found.append((short(path), servers))
    return found


def short(path: str) -> str:
    return path.replace(HOME, "~", 1)


def package_of(command: str, args: list[str]) -> tuple[str | None, str | None]:
    runner = os.path.basename(command)
    if runner not in RUNNERS:
        return None, None
    rest = [a for a in args if not a.startswith("-") and a not in ("dlx", "exec", "run")]
    return (rest[0], RUNNERS[runner]) if rest else (None, None)


def split_version(spec: str) -> tuple[str, str | None]:
    if spec.startswith("@"):
        name, _, version = spec[1:].partition("@")
        return "@" + name, version or None
    name, _, version = spec.partition("@")
    name, _, pyver = name.partition("==")
    return name, version or pyver or None


def exists(name: str, registry: str) -> bool | None:
    url = (
        f"https://registry.npmjs.org/{name.replace('/', '%2F')}"
        if registry == "npm"
        else f"https://pypi.org/pypi/{name}/json"
    )
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=10):
            return True
    except urllib.error.HTTPError as e:
        return False if e.code == 404 else None
    except urllib.error.URLError:
        return None


def audit(cfg: dict, offline: bool) -> list[str]:
    flags = []
    command = cfg.get("command", "")
    args = [str(a) for a in cfg.get("args", [])]
    kind = cfg.get("type") or ("stdio" if command else "http")
    if kind == "stdio":
        flags.append("STDIO")
        if any(a in ("-y", "--yes") for a in args):
            flags.append("AUTO-YES")
        spec, registry = package_of(command, args)
        if spec:
            name, version = split_version(spec)
            if version in (None, "latest"):
                flags.append("UNPINNED")
            if not offline and exists(name, registry) is False:
                flags.append(f"NOT-FOUND({registry}:{name})")
        risky = [k for k in (cfg.get("env") or {}) if RISKY_ENV.search(k)]
        if risky:
            flags.append("ENV(" + ",".join(risky) + ")")
    elif str(cfg.get("url", "")).startswith("http://"):
        flags.append("PLAIN-HTTP")
    return flags


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true")
    a = p.parse_args()

    total = stdio = flagged = 0
    for where, servers in sources():
        print(where)
        for name, cfg in servers.items():
            total += 1
            flags = audit(cfg, a.offline)
            stdio += "STDIO" in flags
            flagged += any(f != "STDIO" for f in flags)
            target = " ".join([cfg.get("command", "")] + [str(x) for x in cfg.get("args", [])]).strip() or cfg.get("url", "")
            print(f"  {name:<20} {target[:60]:<60} {' '.join(flags) or 'ok'}")
    print(f"\n{total} servers, {stdio} stdio, {flagged} with a finding beyond STDIO")


if __name__ == "__main__":
    main()
