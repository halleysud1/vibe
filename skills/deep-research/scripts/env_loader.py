"""Caricamento credenziali portabile per la skill deep-research.

Nessuna dipendenza esterna (niente python-dotenv): parser minimale che gestisce
`KEY=VALUE`, `export KEY=VALUE`, commenti, righe vuote e valori fra virgolette.

Precedenza (dalla piu' alta):
1. variabili d'ambiente del processo
2. `.env.local`  (override locale)
3. `.env`
4. `.env.txt`    (alcuni progetti Windows usano questa estensione)

I file vengono cercati risalendo dalla CWD verso la radice: si usa la **prima
directory** che contiene almeno uno dei tre nomi, cosi' un progetto annidato non
eredita per sbaglio le credenziali di un progetto padre.

REGOLA: mai stampare o loggare il valore di una chiave. Solo prefisso e lunghezza.

Check rapido:
    python scripts/env_loader.py
"""

from __future__ import annotations

import os
from pathlib import Path

# Ordine di applicazione: l'ultimo vince (quindi .env.local ha precedenza).
ENV_FILENAMES = (".env.txt", ".env", ".env.local")

# Chiavi mostrate dal check rapido (mascherate).
KNOWN_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "DEEPRESEARCH_AGENT", "GROUNDED_MODEL")


def find_env_dir(start: Path | None = None) -> Path | None:
    """Prima directory, risalendo da `start`, che contiene un file di env."""
    base = (start or Path.cwd()).resolve()
    for directory in [base, *base.parents]:
        if any((directory / name).is_file() for name in ENV_FILENAMES):
            return directory
    return None


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        # Commento a fine riga solo se il valore non e' quotato.
        if value[:1] not in ("'", '"') and " #" in value:
            value = value.split(" #", 1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def load_env(start: Path | None = None) -> dict[str, str]:
    """Valori dai file di env (le variabili di processo NON sono incluse qui:
    la precedenza e' applicata da `require`/`get`)."""
    directory = find_env_dir(start)
    values: dict[str, str] = {}
    if directory is None:
        return values
    for name in ENV_FILENAMES:
        path = directory / name
        if path.is_file():
            values.update(parse_env_file(path))
    return values


def get(env: dict[str, str], key: str, default: str | None = None) -> str | None:
    """Ambiente di processo > file di env > default."""
    return os.environ.get(key) or env.get(key) or default


def require(env: dict[str, str], key: str) -> str:
    value = get(env, key)
    if not value:
        directory = find_env_dir()
        where = f" (cercato in {directory})" if directory else " (nessun file .env trovato)"
        raise KeyError(
            f"Variabile {key} mancante: definiscila come variabile d'ambiente "
            f"oppure in uno fra {', '.join(ENV_FILENAMES)}{where}."
        )
    return value


def mask(value: str) -> str:
    return f"{value[:6]}... (len={len(value)})" if len(value) > 10 else "(valore corto)"


if __name__ == "__main__":
    directory = find_env_dir()
    env = load_env()
    print(f"File di env: {directory or 'nessuno trovato risalendo dalla CWD'}")
    for key in KNOWN_KEYS:
        value = get(env, key)
        source = "env-process" if os.environ.get(key) else ("file" if env.get(key) else "-")
        print(f"  {key:20s} {mask(value) if value else 'NON IMPOSTATA':30s} [{source}]")
    extra = sorted(k for k in env if k not in KNOWN_KEYS)
    if extra:
        print(f"Altre chiavi nel file ({len(extra)}): {', '.join(extra[:12])}")
