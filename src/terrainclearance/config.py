"""Zentrale Konfiguration der Geländeabstand-Analyse.

Alle einstellbaren Parameter an einem Ort. Die Defaults entsprechen dem
genehmigten Plan (0.5 m Auflösung, echter 3D-Abstand, Boden-Kalibrierung).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # --- Höhenmodelle / Auflösung ---
    resolution: float = 0.5
    """Gewünschte Rasterauflösung in Metern (0.5 = höchste verfügbare)."""

    # --- 3D-Abstands-Algorithmus ---
    r_cap_m: float = 300.0
    """Maximaler horizontaler Suchradius. Über diesem Bodenabstand ist der
    Abstand nicht mehr 'kritisch'; Punkte darüber werden als ``clipped`` markiert."""
    margin_m: float = 5.0
    """Sicherheitszuschlag zum Suchradius (deckt diagonal nächste Zelle + DTM-Rauschen)."""
    max_patch_dim: int = 700
    """Ziel-Obergrenze der Patch-Kantenlänge in Zellen. Grössere Patches (hohe,
    unkritische Punkte) werden grob abgetastet; kleine bleiben voll aufgelöst."""

    # --- Kritische Schwellen (Meter) auf dem 3D-Abstand ---
    # Reihenfolge: (Achtung, Warnung, Gefahr)
    crit_terrain_m: tuple[float, float, float] = (50.0, 30.0, 15.0)
    """Schwellen für den 3D-Abstand zum nackten Gelände (DTM)."""
    crit_surface_m: tuple[float, float, float] = (30.0, 15.0, 5.0)
    """Schwellen für den 3D-Abstand zur Oberfläche/Baumkrone (DSM)."""

    # --- Höhen-Kalibrierung ---
    calibration: str = "auto"
    """Höhenquelle: 'auto' (GNSS bevorzugt), 'gnss', 'pressure' oder 'none'."""
    v_ground_thresh: float = 1.5
    """Bodengeschwindigkeit (m/s) unter der ein Fix als 'am Boden' gilt."""
    vario_ground_thresh: float = 1.5
    """Maximales |Vario| (m/s) für einen Boden-Fix. >1 wegen 1-m-Quantisierung im Stand."""
    ground_smooth_window: int = 5
    """Fenstergrösse (Fixes) für den Rolling-Median von Speed/Vario (Jitter-robust)."""
    ground_min_seconds: float = 12.0
    """Mindestdauer eines Boden-Segments, damit es zur Kalibrierung zählt."""
    antenna_height_m: float = 0.0
    """Antennen-/Gerätehöhe über Boden bei der Kalibrierung (wird abgezogen)."""
    max_plausible_offset_m: float = 200.0
    """Warnschwelle: |Kalibrier-Offset| darüber gilt als verdächtig."""

    # --- Kritische-Momente / Events ---
    event_min_separation_s: float = 20.0
    """Mindestabstand zwischen zwei Events (Debounce einer Annäherung)."""
    event_edge_buffer_s: float = 15.0
    """Sekunden nach Start / vor Landung, in denen keine Events gezählt werden
    (Bodenkontakt bei Start/Landung ist kein kritischer Flugmoment)."""
    landing_climb_threshold_m: float = 20.0
    """Steigt der Pilot nach einem Event bis zur Landung nicht mehr um diesen Wert
    UND ist er nahe der Landeplatzhöhe, gilt das Event als 'Landeanflug'."""
    landing_approach_height_m: float = 150.0
    """Höhe über Landeplatz, unter der ein Endabstieg als 'Landeanflug' gilt."""

    # --- Datenqualität ---
    max_speed_mps: float = 35.0
    """Fixe mit höherer Horizontalgeschwindigkeit gelten als GPS-Spike."""
    max_vario_mps: float = 20.0
    """Fixe mit höherem |Vario| gelten als GPS-Spike."""

    # --- Monte-Carlo-Unsicherheit (GPS-Positionsrauschen) ---
    uncertainty: bool = True
    """Unsicherheitsband des Hangabstands per Monte Carlo schätzen."""
    gps_sigma_h_m: float = 3.0
    """1σ horizontaler GPS-Fehler (m). u-blox ~3, Handy eher 5+."""
    gps_sigma_v_m: float = 5.0
    """1σ vertikaler GPS-Fehler (m), nach Kalibrierung (Rest-Rauschen)."""
    mc_samples: int = 80
    """Anzahl Monte-Carlo-Stichproben pro Punkt."""
    mc_full_below_m: float = 80.0
    """Nur unter diesem Abstand volles MC; darüber analytische Bandnäherung."""
    mc_max_dim: int = 220
    """Max. Patch-Kantenlänge fürs MC (gröber als die Punktberechnung reicht)."""
    mc_seed: int = 12345
    """Seed für reproduzierbare Monte-Carlo-Stichproben."""

    # --- Verteilungs-/KDE-Plots ---
    kde_max_m: float = 250.0
    """Obergrenze der x-Achse (Hangabstand) im KDE-Plot."""
    kde_points: int = 256
    """Auflösung des KDE-Gitters."""

    # --- swisstopo STAC ---
    stac_base: str = "https://data.geo.admin.ch/api/stac/v0.9"
    dtm_collection: str = "ch.swisstopo.swissalti3d"
    dsm_collection: str = "ch.swisstopo.swisssurface3d-raster"
    prefer_year: int | None = None
    """Falls gesetzt: diesen Jahrgang bevorzugen statt 'neuester'."""

    # --- Koordinatentransformation ---
    use_proj_network: bool = True
    """PROJ-Netzwerk aktivieren, um das CHENYX06-Grid (cm-genau) zu nutzen."""

    # --- Mosaik / Speicher ---
    max_mosaic_cells: int = 1_200_000_000
    """Sicherheitslimit für die Mosaikgrösse pro Modell (~4.8 GB float32)."""

    # --- Visualisierung ---
    map_style: str = "open-street-map"
    color_max_m: float = 100.0
    """Obergrenze der Farbskala für den Abstand (darüber = sicher/grün)."""
    surface3d: bool = True
    """Zusätzlich einen interaktiven 3D-Plot (Relief + Flugspur) erzeugen."""
    export_png: bool = False
    """Zusätzlich statische PNGs (3D-Karte, Aggregat-KDE, Risiko) exportieren (braucht kaleido)."""
    surface3d_model: str = "dsm"
    """Welches Modell als 3D-Oberfläche: 'dsm' (inkl. Wald/Gebäude) oder 'dtm' (nackt)."""
    surface3d_colorscale: str = "hillshade"
    """3D-Gelände: 'hillshade' (matte Schummerung, empfohlen), 'gray' oder 'earth' (Höhentönung)."""
    surface3d_max_dim: int = 700
    """Max. Kantenlänge des 3D-Oberflächengitters. Höher = feiner, aber grössere HTML
    (volle 0.5 m über einen ganzen Flug sprengt den Browser)."""
    surface3d_darkness: float = 0.7
    """0..1: wie dunkel die Schummerung gesamthaft ist (höher = dunkler)."""
    surface3d_color_by: str = "clearance"
    """Einfärbung der 3D-Spur: 'clearance' (Schätzwert, wie Karte), 'p05' (konservativ,
    MC-Untergrenze) oder 'mean' (MC-Mittel). p05/mean brauchen aktiviertes MC."""
    surface3d_margin_m: float = 120.0
    """Rand um die Flugspur, der im 3D-Plot mitgezeigt wird."""
    timezone: str = "Europe/Zurich"
    """Zeitzone für die Barogramm-Achse ('UTC' für Rohzeit)."""

    # --- Pfade ---
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    output_dir: Path = field(default_factory=lambda: Path("output"))

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.output_dir = Path(self.output_dir)
