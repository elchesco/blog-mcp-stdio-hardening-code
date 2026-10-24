# Code companion: an MCP stdio server is a shell command


| Folder | Post section | What it is |
|---|---|---|
| `00-the-bug/` | Round 0: the bug | `vulnerable_spawn.py`: the CVE-2026-105740 pattern reduced to its two lines, with harmless payloads. Kept as a DEAD END on purpose. |
| `01-safe-spawn/` | Round 1: the fix | `safe_spawn.py`: server IDs mapped to pinned argv, no shell, env from an allowlist. |
| `02-audit-your-machine/` | Round 2: measure | `mcp_audit.py`: every MCP server your agents will start, flagged STDIO / UNPINNED / AUTO-YES / NOT-FOUND / ENV / PLAIN-HTTP. |
| `03-managed-policy/` | Round 3: fleet policy | Claude Code managed settings: exact `serverCommand` allowlist, locked to managed scope. |
| `04-aws-tool-role/` | Round 4: identity | IAM role for a tool that runs on AWS: one log group, explicit denies, confused-deputy-safe trust policy. |
| `05-checklist/` | Round 5 | What to check on your machine today, and what a platform must enforce. |

## Suggested reading order

Run `02` first; it takes ten seconds and is the only file here that can find
a live problem on your own machine. Then `00` and `01` side by side.

## Run

```bash
python3 -I 02-audit-your-machine/mcp_audit.py
python3 00-the-bug/vulnerable_spawn.py && rm -rf /tmp/mcp-demo-bin
python3 01-safe-spawn/safe_spawn.py
```

## Pin versions used in the post

| Thing | Version |
|---|---|
| Langflow | vulnerable: before 1.9.0; advisory lists 1.8.3 affected, 1.9.0 patched |
| Azure MCP Server | 3.0 (stable 12 October 2026) |
| Claude Code | 2.1.280 |
| @playwright/mcp (example pin) | 0.0.83 |
| Python | 3.10+ (stdlib only) |
