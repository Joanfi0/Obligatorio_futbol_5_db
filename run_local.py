"""Arranque local sin Docker para la aplicación; requiere MySQL inicializado."""

import os
from pathlib import Path

for raw in (
    Path(__file__).resolve().with_name(".env").read_text(encoding="utf-8").splitlines()
):
    if raw.strip() and not raw.lstrip().startswith("#"):
        k, v = raw.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from app.web import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
