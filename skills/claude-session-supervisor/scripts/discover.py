"""Fase 0 - Discovery automation per la skill claude-session-supervisor.

Esegue dalla CWD del progetto target. Identifica:
- OS rilevato (informa la scelta del wrapper: wake_worker.ps1 vs .sh)
- CLAUDE.md presente
- Skill SKILL.md (formato Agent Skills)
- MCP server presenti (cartelle con run_server.py / server.py)
- Scripts esistenti (potenziali tool a disposizione del worker)
- Path "sensibili" (.env*, secrets/, config/) -> input per la denylist
- Suggerimenti di mission tipiche

Output: JSON stampato a stdout (anche salvato in ./.claude-session-supervisor-discovery.json
se --save).

Usage:
    python skills/claude-session-supervisor/scripts/discover.py
    python skills/claude-session-supervisor/scripts/discover.py --root /path/to/project --save
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path


# Forza UTF-8 su stdout (Windows console di default e' cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def detect_os() -> dict:
    sys_name = platform.system().lower()
    return {
        "platform": sys_name,
        "wrapper_recommended": "wake_worker.ps1" if "windows" in sys_name else "wake_worker.sh",
        "wrapper_both": True,  # scaffolda sempre entrambi per portabilita'
    }


def find_claude_md(root: Path) -> dict:
    candidates = [root / "CLAUDE.md", root / ".claude" / "CLAUDE.md"]
    for c in candidates:
        if c.exists():
            return {"present": True, "path": str(c.relative_to(root))}
    return {"present": False, "path": None}


def find_skills(root: Path) -> list[dict]:
    skills_dir = root / ".claude" / "skills"
    skills: list[dict] = []
    if not skills_dir.exists():
        return skills
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
            front = {}
            if m:
                # parsing semplice del frontmatter senza dipendenza da yaml
                for line in m.group(1).splitlines():
                    if ":" in line:
                        k, _, v = line.partition(":")
                        front[k.strip()] = v.strip().strip('"').strip("'")
            skills.append({
                "name": front.get("name", skill_md.parent.name),
                "description": front.get("description", "")[:200],
                "path": str(skill_md.parent.relative_to(root)),
            })
        except Exception:
            continue
    return skills


def find_mcp_servers(root: Path) -> list[dict]:
    """Cerca server MCP (cartelle con run_server.py o server.py + heuristic)."""
    servers: list[dict] = []
    mcp_config = root / ".mcp.json"
    if mcp_config.exists():
        try:
            data = json.loads(mcp_config.read_text(encoding="utf-8"))
            for name in (data.get("mcpServers") or {}).keys():
                servers.append({"name": name, "source": ".mcp.json"})
        except Exception:
            pass
    # Cerca anche cartelle locali col pattern run_server.py / server.py
    for candidate in root.glob("**/run_server.py"):
        if ".git" in candidate.parts or "node_modules" in candidate.parts:
            continue
        servers.append({
            "name": candidate.parent.name,
            "source": str(candidate.relative_to(root)),
        })
    for candidate in root.glob("**/server.py"):
        if ".git" in candidate.parts or "node_modules" in candidate.parts:
            continue
        # heuristica MCP: contiene "@mcp.tool" o "FastMCP" o "mcp.server"
        try:
            content = candidate.read_text(encoding="utf-8", errors="replace")[:5000]
            if re.search(r"(FastMCP|@mcp\.tool|mcp\.server)", content):
                servers.append({
                    "name": candidate.parent.name,
                    "source": str(candidate.relative_to(root)),
                })
        except Exception:
            continue
    # Dedup per source
    seen = set()
    unique = []
    for s in servers:
        key = s.get("source") or s.get("name")
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    return unique


def find_scripts(root: Path) -> list[str]:
    out: list[str] = []
    for d in ("scripts", "bin", "tools"):
        p = root / d
        if not p.is_dir():
            continue
        for f in sorted(p.rglob("*")):
            if f.is_file() and f.suffix in {".py", ".sh", ".ps1"}:
                out.append(str(f.relative_to(root)))
    return out


def find_sensitive_paths(root: Path) -> list[str]:
    """Path che dovrebbero finire in denylist (o comunque essere valutati)."""
    sensitive: list[str] = []
    # .env e varianti
    for env_file in root.glob(".env*"):
        if env_file.is_file():
            sensitive.append(str(env_file.relative_to(root)))
    # cartelle conventional
    for d in ("secrets", "config", "credentials", "keys", ".credentials"):
        p = root / d
        if p.is_dir():
            sensitive.append(str(p.relative_to(root)) + "/")
    # certs e PEM in giro
    for ext in ("pem", "key", "p12"):
        for f in root.rglob(f"*.{ext}"):
            if ".git" in f.parts or "node_modules" in f.parts:
                continue
            sensitive.append(str(f.relative_to(root)))
    return sensitive[:30]  # cap per evitare report enormi


def suggest_missions(skills: list[dict], scripts: list[str]) -> list[str]:
    suggestions: list[str] = []
    skill_names = {s["name"] for s in skills}
    if any(name.startswith(("analisi", "analyze", "report")) for name in skill_names):
        suggestions.append("Run di analisi periodica su tutte le persone/entita' del dominio")
    if any("estrai" in s.lower() or "extract" in s.lower() for s in scripts):
        suggestions.append("Estrazione dati schedulata (nightly refresh)")
    if any(name.startswith(("gamification", "challenge")) for name in skill_names):
        suggestions.append("Creazione/aggiornamento sfide a partire da insight di analisi")
    if not suggestions:
        suggestions.append("Hello world safe: lettura locale, conteggio, sintesi in docs/ops/LAST_RUN.md")
    return suggestions


def discover(root: Path) -> dict:
    return {
        "os": detect_os(),
        "claude_md": find_claude_md(root),
        "skills": find_skills(root),
        "mcp_servers": find_mcp_servers(root),
        "scripts": find_scripts(root),
        "sensitive_paths": find_sensitive_paths(root),
        "mission_suggestions": suggest_missions(find_skills(root), find_scripts(root)),
        "root": str(root),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--root", default=".", help="root del progetto target")
    p.add_argument("--save", action="store_true",
                   help="salva anche su .claude-session-supervisor-discovery.json")
    args = p.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.stderr.write(f"root non valido: {root}\n")
        sys.exit(1)

    report = discover(root)
    out_json = json.dumps(report, indent=2, ensure_ascii=False)
    print(out_json)

    if args.save:
        out_path = root / ".claude-session-supervisor-discovery.json"
        out_path.write_text(out_json, encoding="utf-8")
        sys.stderr.write(f"saved -> {out_path}\n")


if __name__ == "__main__":
    main()
