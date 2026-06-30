"""Zentraler matplotlib-Stil für alle thermalmodel-PNGs.

Bewusste Entscheidung (Feedback Benjamin): **große, hochaufgelöste** Figuren mit
**relativ kleiner, feiner** Schrift — keine „fetten" Default-Plots und **kein
Runterskalieren** der fertigen Bilder. Erreicht durch hohe DPI (scharf) + moderate
Schriftgrößen + dünne Linien; die großzügige figsize je Plot lässt die Schrift relativ
klein wirken.

Jede Plot-Funktion ruft `use()` statt des lokalen `matplotlib.use("Agg")`-Setups und
nutzt das zurückgegebene `plt`. Dadurch ist der Stil an genau einer Stelle gepflegt.
"""

from __future__ import annotations

DPI = 220  # Export-Auflösung (vorher 150–185) — bewusst hoch/groß statt verkleinert


def use():
    """matplotlib (Agg) initialisieren, zentralen Stil setzen, `pyplot` zurückgeben."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "savefig.dpi": DPI,
        "figure.dpi": DPI,
        "savefig.bbox": "tight",
        # relativ kleine, feine Schrift auf großer Leinwand
        "font.size": 9.0,
        "axes.titlesize": 12.0,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,
        "legend.fontsize": 8.5,
        "figure.titlesize": 14.0,
        # dünnere Linien/Rahmen (sonst wirken die Plots „fett")
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.1,
        "patch.linewidth": 0.7,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
    })
    return plt
