---
name: appfactory-app-register
description: Register and prepare Android apps using AppFactory metadata and protected build secrets. Use when creating an app record, preparing a signed Android build, or checking app registration status.
---

# AppFactory app registration

Use the `appfactory` MCP server for AppFactory operations. Secret Manager is the only source for signing material.

- Never ask for or return JKS files, passwords, private keys, tokens, or API keys.
- Store only app metadata and secret resource names in Firestore.
- Use `register_app`, `get_app_status`, `list_apps`, and `prepare_android_build` for metadata workflows.
- Use `build_signed_android` only through the controlled build worker; return artifact metadata, never secret contents.
- Obtain approval before external uploads or production deployment.
