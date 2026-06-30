# thermalmodel — solar-driven thermal modelling (Niesen/Frutigen)

Models the real solar irradiance on the 3D topography over the day → sensible heat flux → hotspots,
boundary layer (w\*/z_i) and drifting thermal columns; validated against own IGC climbs and thermal.kk7.ch.

**Full, illustrated walkthrough (canonical, EN/DE):**
[Thermals, step by step](https://benjamin-loeffel.github.io/paragliding-tools/thermal-step-by-step/)
· source: [`docs/thermal-step-by-step.md`](../../docs/thermal-step-by-step.md).

Run: `python thermal.py` (see the repo [README](../../README.md)). Decisions, rationale and rejected
approaches: the German ADR journal [`docs/thermalmodel-journal.md`](../../docs/thermalmodel-journal.md).
