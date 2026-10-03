---
name: appfactory-app-register
description: Register and prepare Android apps using AppFactory metadata and protected build secrets. Use when creating an app record, preparing a signed Android build, or checking app registration status.
---

# AppFactory app registration

Use the `appfactory` MCP server for AppFactory operations. Treat Google Secret Manager as the only source for signing material.

## Security rules

- Never ask the user to paste a JKS, password, private key, token, or secret value into chat.
- Never return secret values, decoded keystore contents, or temporary secret file contents to the model.
- Pass only an app ID and approved operation parameters to the tools.
- Keep Firestore limited to app metadata and secret resource names.
- Use `prepare_android_build` or `build_signed_android` for signing; do not implement signing in the model.

## Available operations

- `get_app_status`: read safe metadata and provisioning state.
- `register_app`: create or update an app metadata record.
- `prepare_android_build`: validate that required secret references exist without returning their values.
- `build_signed_android`: run a controlled build using secrets internally and return artifact metadata only.

Before any external upload or deployment, show the target and artifact metadata and obtain approval when required by the host workflow.
