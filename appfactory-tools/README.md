# AppFactory tools

This package contains the local MCP server and the AppFactory skill. The server stores only non-secret app metadata in a local registry during development. Production deployment should replace that registry with Firestore and use Google Secret Manager for signing material.

## Local use

The Codex host starts `server.py` from `.mcp.json`; it is not a long-running web server that needs a separate manual start command. The server exposes metadata operations and secret-reference checks. It never returns JKS bytes or secret values.

## Git safety

The `.gitignore` excludes JKS files, keystores, APK/AAB artifacts, Firebase client configuration, local properties, registries, and environment files. Commit source, skill instructions, MCP configuration, deployment manifests, and `.env.example`; keep credentials in Secret Manager.

## Production path

1. Give a dedicated service account only the required Firestore and Secret Manager roles.
2. Replace the local registry with Firestore reads and writes.
3. Implement the build worker using Gradle and temporary secret files.
4. Delete temporary signing material after each build.
5. Return artifact metadata and logs, never secret contents.
