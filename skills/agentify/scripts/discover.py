"""Fase 0 — Discovery automation per la skill agentify.

Esegue dalla CWD del progetto target. Inventaria:
- skill SKILL.md (formato Agent Skills)
- MCP servers (cartelle con run_server.py o server.py)
- config YAML
- scripts Python
- deps Python
- domain hints (da CLAUDE.md)

Output: JSON stampato a stdout (anche salvato in ./.agentify_discovery.json se --save).

Usage:
    python .claude/skills/agentify/scripts/discover.py
    python .claude/skills/agentify/scripts/discover.py --root /path/to/project --save
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# Forza UTF-8 su stdout (Windows console di default è cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def find_skills(skills_dir: Path) -> list[dict]:
    skills: list[dict] = []
    if not skills_dir.exists():
        return skills
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
            if not m:
                continue
            front = yaml.safe_load(m.group(1)) or {}
            skills.append({
                "name": front.get("name", skill_md.parent.name),
                "description": front.get("description", "")[:200],
                "path": str(skill_md.parent.name),
                "body_chars": len(m.group(2)),
            })
        except Exception:
            continue
    return skills


def find_mcp_servers(root: Path) -> list[dict]:
    """Cerca cartelle con run_server.py o server.py + heuristic MCP."""
    servers: list[dict] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        for entry_name in ("run_server.py", "server.py"):
            entry = d / entry_name
            if not entry.exists():
                # Cerca un livello in basso (es. mcp-odoo/src/.../server.py)
                matches = list(d.glob(f"**/{entry_name}"))
                if not matches:
                    continue
                entry = matches[0]
            try:
                content = entry.read_text(encoding="utf-8", errors="ignore")[:3000]
            except Exception:
                continue
            if "mcp" in content.lower() or "FastMCP" in content or "stdio_server" in content:
                servers.append({
                    "name": d.name,
                    "command": f"python {entry.relative_to(root).as_posix()}",
                    "entry": str(entry.relative_to(root)),
                })
                break
    return servers


def find_config_yamls(root: Path) -> list[dict]:
    configs: list[dict] = []
    config_dir = root / "config"
    if not config_dir.exists():
        return configs
    for f in list(sorted(config_dir.glob("*.yaml"))) + list(sorted(config_dir.glob("*.yml"))):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            top_keys = list(data.keys()) if isinstance(data, dict) else []
            configs.append({
                "name": f.stem,
                "path": str(f.relative_to(root)),
                "top_keys": top_keys[:10],
            })
        except Exception:
            pass
    return configs


def find_scripts(root: Path) -> list[dict]:
    scripts: list[dict] = []
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return scripts
    for f in sorted(scripts_dir.glob("*.py")):
        doc = ""
        try:
            content = f.read_text(encoding="utf-8")[:1000]
            m = re.search(r'"""(.+?)"""', content, re.DOTALL)
            if m:
                doc = m.group(1).strip()[:200]
        except Exception:
            pass
        scripts.append({"name": f.stem, "path": str(f.relative_to(root)), "doc": doc})
    return scripts


def find_python_deps(root: Path) -> list[str]:
    req = root / "requirements.txt"
    if not req.exists():
        return []
    deps: list[str] = []
    for line in req.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            base = line.split("==")[0].split(">=")[0].split("[")[0].strip()
            if base:
                deps.append(base)
    return deps


def extract_domain_hints(root: Path) -> dict:
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return {}
    text = claude_md.read_text(encoding="utf-8")
    headings = re.findall(r"^#+\s+(.+)$", text[:8000], re.MULTILINE)
    # Prendi i primi paragrafi non vuoti come "intro"
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("#")]
    intro = paragraphs[0][:400] if paragraphs else ""
    return {
        "headings": headings[:20],
        "intro": intro,
    }


def discover(root: Path) -> dict:
    return {
        "project_root": str(root.resolve()),
        "skills": find_skills(root / ".claude" / "skills"),
        "mcp_servers": find_mcp_servers(root),
        "config_files": find_config_yamls(root),
        "existing_scripts": find_scripts(root),
        "python_deps": find_python_deps(root),
        "domain_hints": extract_domain_hints(root),
    }


def main():
    parser = argparse.ArgumentParser(description="Fase 0 Discovery per skill agentify")
    parser.add_argument("--root", default=".", help="root del progetto (default: cwd)")
    parser.add_argument("--save", action="store_true",
                        help="salva output in .agentify_discovery.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    inventory = discover(root)

    print(json.dumps(inventory, indent=2, ensure_ascii=False))

    if args.save:
        out = root / ".agentify_discovery.json"
        out.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n# Saved to {out}")


if __name__ == "__main__":
    main()
