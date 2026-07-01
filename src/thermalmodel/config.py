"""Zentrale Konfiguration der Thermik-Modellierung.

Stil analog zu terrainclearance/config.py: eine Dataclass mit dokumentierten Defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# --- Bodenbedeckungs-Klassen -------------------------------------------------
# Stabile Integer-IDs (für GeoTIFF / class_id-Raster).
LC_UNKNOWN = 0
LC_CONIFER = 1      # Nadelwald
LC_BROADLEAF = 2    # Laubwald
LC_MIXED = 3        # Mischwald
LC_GRASS = 4        # Wiese/Weide/Alpweide
LC_ROCK = 5         # Fels/Geröll/Schutt
LC_WATER = 6        # Wasser
LC_SNOW = 7         # Schnee/Gletscher
LC_URBAN = 8        # bebaut/versiegelt

LC_NAMES = {
    LC_UNKNOWN: "unbekannt", LC_CONIFER: "Nadelwald", LC_BROADLEAF: "Laubwald",
    LC_MIXED: "Mischwald", LC_GRASS: "Wiese", LC_ROCK: "Fels/Geröll",
    LC_WATER: "Wasser", LC_SNOW: "Schnee/Gletscher", LC_URBAN: "bebaut",
}

# Albedo (Anteil reflektiert) und f_H (fühlbarer Wärmeanteil, treibt Thermik).
# Quellen: MODIS-Albedo-Klimatologie + Bowen-Verhältnis-Literatur (Oke), per
# Web-Recherche plausibilisiert (Nachtlauf 2026-06-30, siehe docs/thermalmodel-journal ADR-0011).
# WICHTIG: f_H ist hier KEIN reiner Bowen-Anteil B/(1+B) bezogen auf die NETTOstrahlung R_n,
# sondern ein *effektiver fühlbarer Heizfaktor* bezogen auf die absorbierte Kurzwelle
# (1-albedo)·G — er schluckt implizit den langwelligen Netto-Verlust und den Bodenwärmestrom.
# Daher liegen die Absolutwerte (Wiese 0.50, Fels 0.75) bewusst über dem reinen Bowen-f_H.
# Wer Q_H als absoluten W/m² in die w*-Formel steckt, sollte ~0.55 (R_n/G) vorschalten.
# Colormap-Politik (projektweit): ausschliesslich perzeptuell-uniforme Sequential-Maps.
#   viridis = Standard (Wahrscheinlichkeit/Score/Validierung/kk7/XC),
#   inferno = Energie/Wärme (Q_H, Energieeintrag, Differenz; plotly "Inferno"),
#   cividis = Wind (Geschwindigkeit/Strömungstraces).
# (Hillshade-Relief bleibt Graustufen.) Werte sind in den Plot-Funktionen entsprechend gesetzt.
CMAP_DEFAULT = "viridis"
CMAP_ENERGY = "inferno"
CMAP_WIND = "cividis"


ALBEDO = {
    LC_UNKNOWN: 0.18, LC_CONIFER: 0.10, LC_BROADLEAF: 0.17, LC_MIXED: 0.13,
    LC_GRASS: 0.20, LC_ROCK: 0.28, LC_WATER: 0.06, LC_SNOW: 0.80, LC_URBAN: 0.15,
}
F_H = {  # effektiver fühlbarer Heizfaktor 0..1 (siehe Kommentar oben, NICHT reines Bowen)
    LC_UNKNOWN: 0.40, LC_CONIFER: 0.35, LC_BROADLEAF: 0.32, LC_MIXED: 0.34,
    LC_GRASS: 0.50, LC_ROCK: 0.75, LC_WATER: 0.10, LC_SNOW: 0.05, LC_URBAN: 0.60,
}
# Aerodynamische Rauhigkeitslänge z0 [m] je Klasse (für spätere LES/Talwind-Schritte).
Z0 = {
    LC_UNKNOWN: 0.1, LC_CONIFER: 1.0, LC_BROADLEAF: 0.8, LC_MIXED: 0.9,
    LC_GRASS: 0.05, LC_ROCK: 0.02, LC_WATER: 0.001, LC_SNOW: 0.005, LC_URBAN: 0.7,
}


@dataclass
class ThermalConfig:
    # --- Modellgebiet ---
    kml_path: str = "examples/data/domain_niesen_frutigen.kml"
    clip_to_polygon: bool = False
    """False: ganze Rechteck-Domäne (bbox des Polygons) rechnen/zeigen — nutzt alle
    geladenen Kacheln. True: nur das KML-Polygon-Innere (gezackter Rand)."""
    resolution_m: float = 20.0
    """Modellgitter-Auflösung (Cubes laufen hierauf, nicht in 0.5 m)."""
    dtm_resolution: float = 2.0
    """Auflösung der swissALTI3D-Kacheln fürs Höhen-Resampling (0.5 oder 2)."""
    horizon_margin_m: float = 4000.0
    """Wie weit der DEM über die Domäne hinaus geladen wird (Fernhorizont/Schatten)."""
    launch_sites: tuple = (
        ("Tschentenalp", 7.5453, 46.4989), ("Trutten", 7.6417, 46.5590),
        ("Grimer", 7.6832, 46.5536), ("Niesen", 7.6524, 46.6462),
    )
    """Startplätze (Name, lon, lat) — als Marker auf den Q_H-Karten (nur im Gebiet sichtbar)."""

    # --- Tag & Zeitachse (UTC-naiv in lokaler Zeit gerechnet) ---
    date: str = "2026-06-30"
    timezone: str = "Europe/Zurich"
    t_start_hour: int = 6
    t_end_hour: int = 20
    t_step_min: int = 30
    cumulative_hours: tuple = (11, 13, 15, 18)
    """Tageszeit-Cutoffs (lokal) für die kumulativen Energieeintrag-Panels."""

    # --- Horizont / Sky-View-Factor ---
    n_azimuth: int = 36
    horizon_step_m: float | None = None   # None -> = resolution_m
    horizon_max_steps: int = 600
    horizon_workers: int = 1
    """Parallel-Prozesse für die Horizontberechnung (über Azimute). 1 = seriell. Bei feiner
    Auflösung (z. B. 20 m Weit-Domäne) auf ~Kernzahl−2 setzen — Horizont ist der Flaschenhals."""

    # --- Solar / Klarhimmel ---
    linke_turbidity: float | None = None  # None -> pvlib Monatsklimatologie
    ground_albedo_reflect: float = 0.2    # für den Terrain-Reflexionsterm

    # --- Wolken / NWP (reales Wärmebild A5b) ---
    nwp_model: str = "meteoswiss_icon_ch1"  # Open-Meteo-Modell (GRIB-frei) für Strahlung/Wolken
    nwp_points: tuple = (5, 6)              # Stützpunkt-Raster (Ost × Nord) für τ(t,x,y)
    # Wind: meteoswiss_icon_ch1 liefert KEINE Druckniveau-Winde -> icon_seamless (ICON-CH1/D2/EU)
    wind_model: str = "icon_seamless"
    wind_levels_hpa: tuple = (925, 900, 850, 800, 700)  # ~870–3220 m AMSL (Grenzschicht über Gelände)
    wind_trace_height_m: float = 2500.0     # Höhe AMSL für die Wind-Partikeltraces

    # --- Hotspot-Erkennung ---
    hotspot_min_distance_m: float = 300.0
    hotspot_top_n: int = 60
    hotspot_slope_opt_deg: float = 25.0   # bevorzugtes Auslöse-Hangband
    hotspot_slope_width_deg: float = 15.0
    w_qh: float = 1.0      # Score-Gewicht Wärmestrom
    w_convex: float = 0.4  # Konvexität (Grate/Kanten)
    w_aspect: float = 0.3  # Ausrichtung zur Sonne
    w_slope: float = 0.2   # Hangband

    # --- D0: statisches Thermik-Quell-Proxy (buoyancy.py) ---
    # Heizbasis = Q_H-Tagesenergie (integriert Sonne/Aspekt korrekt) statt statischem Aspekt-Term.
    # Triggerlinien-Term (Q_H-Gradient/Kanten) per Recherche als wahrscheinlichster Mehrwert ergänzt.
    # Gewichte datengetrieben (Ablation/Suche gegen IGC+kk7, ADR-0013). Terrain dominiert;
    # heat klein gehalten (physikalisch sinnvoll, kostet ~0.008 AUC); edge=0 (kein Skill).
    d0_w_heat: float = 0.3    # Heizung (Q_H-Tagesenergie) — physikalisch nötig, schwacher Diskriminator
    d0_w_conv: float = 0.5    # Konvexität (Ablöse-Geometrie)
    d0_w_aspect: float = 0.4  # Ausrichtung zur Sonne (SSW) — empirisch prädiktiv
    d0_w_slope: float = 0.7   # Hangband — stärkster Einzelprädiktor (AUC ~0.67)
    d0_w_edge: float = 0.0    # Triggerlinien (Q_H-Gradient): Ablation AUC ~0.5 -> verworfen
    d0_aspect_pref_deg: float = 210.0
    d0_slope_opt_deg: float = 28.0
    d0_slope_width_deg: float = 16.0

    # --- D1: Ablöse-Modell (hangfolgender Aufstieg → Release) + Plume ---
    # Phase 1: Parzelle läuft hangaufwärts (anabatisch), bis sie sich an einer markanten
    # Geländeänderung ablöst (Konvexität/Grat/Abflachung). Dann Phase 2 = freier Plume.
    # Werte literatur-/recherchefundiert (Zardi&Whiteman, XC Mag "The Hunt"), ADR-0017.
    d1_release_curv_pct: float = 80.0     # Release ab oberstem Perzentil positiver Krümmung
    d1_slope_flatten_deg: float = 5.0     # Abflachung nach Steilhang → Release
    d1_u_slope_ms: float = 2.0            # hangparallele Aufstiegsgeschwindigkeit (Jet 1–5 m/s)
    d1_slope_step_m: float = 40.0         # Schrittweite des hangfolgenden Laufs
    d1_max_slope_steps: int = 50          # Kappung (~2 km Hangweg)
    d1_veg_edge_curv_factor: float = 0.4  # an Waldgrenzen löst schon schwächere Konvexität ab
    cumulative_hours_drift: tuple = (11, 13, 15, 18)  # Zeitpunkte der zeitaufgelösten Drifts
    drift_grid_spacing_m: float = 150.0   # Netz-Seed-Abstand 2D-Quiver (100 m wäre ~7500 Pfeile = unleserlich)
    plume3d_grid_spacing_m: float = 300.0  # gröberes Netz fürs 3D-Slider-HTML (4 Frames × Spuren handlich)

    # --- Bodenbedeckung ---
    landcover_source: str = "auto"  # 'auto'|'nfi'|'dlt'|'heuristic'
    chm_forest_min_m: float = 3.0   # CHM-Schwelle Wald
    use_chm: bool = False           # DSM (0.5 m, schwer) laden für CHM/Waldgate?

    # --- Wolken / Wind (Phase A5b / C, später) ---
    icon_collection: str = "ch.meteoschweiz.ogd-forecasting-icon-ch1"

    # --- Pfade ---
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    output_dir: Path = field(default_factory=lambda: Path("output/thermal"))

    # --- Visualisierung ---
    map_style: str = "open-street-map"

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        self.output_dir = Path(self.output_dir)
        if self.horizon_step_m is None:
            self.horizon_step_m = self.resolution_m
