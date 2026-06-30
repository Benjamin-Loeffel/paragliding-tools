#!/usr/bin/env python
"""Einstiegspunkt: solargetriebene Thermik-Modellierung (Niesen/Frutigen).

Phase A (ideal+real Wärmebild, D0-Quell-Proxy) → Validierung (eigene IGC + thermal.kk7.ch)
→ Phase B (z_i/w*/Ceiling aus Payerne-Sondierung) → D1 (Lagrange-Plume, driftende Thermik).

Beispiel:
    python thermal.py
    python thermal.py --skip-plume
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from thermalmodel.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
