"""PreToolUse hook: refuse direct edits to generated artifacts under exports/."""
import json
import os
import sys

payload = json.load(sys.stdin)
path = payload.get("tool_input", {}).get("file_path", "")
exports = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()), "exports") + os.sep
if os.path.abspath(path).startswith(exports):
    print(
        "exports/ holds generated artifacts. Edit the source (CadQuery, docs/status/, bom/bom.csv) "
        "and regenerate with the bin/ build commands.",
        file=sys.stderr,
    )
    sys.exit(2)
