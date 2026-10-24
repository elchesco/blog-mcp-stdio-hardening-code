# Round 3: a fleet-wide allowlist for Claude Code

`managed-settings.json` goes where your MDM or config management puts Claude
Code managed settings (for example `/Library/Application Support/ClaudeCode/`
on macOS, `/etc/claude-code/` on Linux), or into server-managed settings.

What each line does:

- `allowManagedMcpServersOnly: true`: user, project and local allowlists are
  ignored, so nobody widens the list from `~/.claude/settings.json`.
- The first `serverUrl` entry means every remote server must match a URL
  pattern; a `serverName` alone no longer gets one through.
- The first `serverCommand` entry does the same for stdio: the command and
  every argument must match exactly, in order. Pin the version in the entry,
  and an unpinned or typo'd `npx` line simply does not load.
- `deniedMcpServers` always wins and merges from every scope.

Three non-obvious details from the docs:

1. **`serverName` is not a security control.** It is the label the user typed
   in `claude mcp add`. Anyone can call any server `github`.
2. **`serverCommand` does not compare `env`.** "Some environment variables
   change what `node` loads at startup." If env matters, define the server
   yourself in `managed-mcp.json`, where you also set its env.
3. **Project `.mcp.json` approval is interactive only.** In `claude -p`, Agent
   SDK sessions and some cloud sessions, project-scoped servers load without
   the prompt. Use `disabledMcpjsonServers` or the allowlist above for those.

Verify on a managed machine:

```bash
claude mcp list
claude mcp add --transport http test https://example.org/mcp
# Cannot add MCP server "test": not allowed by enterprise policy
```
