# n8n workflow specs, not exported JSON

These are specifications to build in the n8n editor, not importable
`.json` files. Hand-authoring valid n8n JSON without a running instance
to test against risks giving you a broken import -- node type/version
strings drift between n8n releases, and a spec you can actually read
and reason about is more reliable to build from than a JSON blob
neither of us can verify. Each spec takes 15-30 minutes to build once
in the editor.
