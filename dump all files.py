

import os

# Extensions to include
#".html", ".js", ".css", ".py", ".md"
extensions = ["app.py", "forgot_password.html", "reset_password.html"]
output_file = "NEUROAID_dump.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for root, _, files in os.walk("."):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, ".").replace("\\", "/")
                ext = os.path.splitext(file)[1].lstrip(".")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    content = f"[Error reading file: {e}]"

                out.write(f"# File: {rel_path}\n")
                out.write(f"```{ext}\n{content}\n```\n\n")

print(f" Combined content saved to: {output_file}")
