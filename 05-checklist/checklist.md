# MCP hardening checklist

Round 5 of the post. Two halves: what to check on every developer machine
today, and what a platform that lets users add MCP servers must enforce.

## On your machine, today

| # | Check | How |
|---|---|---|
| 1 | Every stdio server you have | `python3 -I 02-audit-your-machine/mcp_audit.py` |
| 2 | No package that does not exist | `NOT-FOUND` in the audit. Remove it now: `claude mcp remove <name>` from that project directory. |
| 3 | No `@latest` or unversioned `npx`/`uvx` | `UNPINNED`. Pin an exact version that is at least two weeks old. |
| 4 | No interpreter-changing env | `ENV(...)`: `LD_PRELOAD`, `DYLD_*`, `NODE_OPTIONS`, `PYTHONPATH`, `PATH`. |
| 5 | Project `.mcp.json` from cloned repos | Approval prompts happen only in interactive sessions. Check `disabledMcpjsonServers` for anything you run with `claude -p`. |
| 6 | Langflow | Upgrade to a release that includes the 1.9.0 fix (1.10.3 or later covers both readings of the advisory). |

## On a platform that runs MCP servers for users

| # | Control | Why |
|---|---|---|
| 1 | Users pick a server ID; admins own the argv | Any user-supplied command is code execution. Validation does not fix that. |
| 2 | No shell between config and process | `bash -c` turns a field into shell source. `exec` stops `;` chaining but not `$(...)`. |
| 3 | Environment built from an allowlist | A safe binary name plus `PATH` or `LD_PRELOAD` from the request runs something else. |
| 4 | Registration is an admin action with an audit record | In the Langflow bug, any authenticated user could register; the config persisted in project settings that flow reviews did not cover. |
| 5 | Remote transport by default | An HTTP server runs in its own process, as its own identity, behind auth you can revoke. stdio runs as whoever started the agent. |
| 6 | One identity per tool, least privilege, explicit denies | See `04-aws-tool-role/`. |
| 7 | Read-only by default | Azure MCP Server 3.0 ships `--read-only`, exact-match `--tool` filtering, and marks its PostgreSQL and MySQL query tools destructive instead of filtering SQL verbs. |
| 8 | Egress allowlist | A read-only tool that can call any URL can still exfiltrate what it read. |
| 9 | Fleet policy for coding agents | `03-managed-policy/`: `allowManagedMcpServersOnly` + exact `serverCommand` entries. |
| 10 | Log which servers and tools actually run | Claude Code: `OTEL_LOG_TOOL_DETAILS=1` adds MCP server and tool names to telemetry. |
