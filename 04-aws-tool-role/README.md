# Round 4: the identity a tool runs as

A stdio server on a laptop runs as the developer, with every credential in
`~/.aws`, the keychain and the shell. The same server in a shared platform
should run as its own IAM role with the smallest read set the tool needs.

| File | What it is |
|---|---|
| `tool-role-policy.json` | Read one log group and metrics. Explicit deny on IAM, role chaining, secrets and decryption, so a later `Allow` added by mistake cannot widen it. |
| `trust-policy.json` | Only ECS tasks in this account can assume the role (`aws:SourceAccount` + `aws:SourceArn`), which blocks confused-deputy use from another account. |

Non-obvious detail: CloudWatch `GetMetricData` has no resource-level
scoping, so it stays `"Resource": "*"`. If metric names are sensitive, put the
tool in its own account rather than trying to narrow that statement.

What the role does not solve: egress. A tool that can read logs and also make
arbitrary HTTPS calls can exfiltrate what it reads. Run it in a subnet or
security group that only reaches the AWS endpoints it needs (VPC endpoints,
no default route).
