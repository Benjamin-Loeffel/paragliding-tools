# meteo — Payerne radiosounding (emagram + indices)

Fetches the MeteoSwiss radiosounding **Payerne (WMO 06610)**, draws an emagram/Skew-T and computes
thermodynamic indices (CAPE, CIN, LI, LCL, LFC, PWAT, freezing level). Feeds phase B (z_i/w*) of `thermalmodel`.

**Full page (canonical, EN/DE), incl. the data-availability research:**
[Payerne sounding](https://benjamin-loeffel.github.io/paragliding-tools/payerne/)
· source: [`docs/payerne.md`](../docs/payerne.md).

```bash
python meteo/radiosonde_payerne.py latest     # current sounding → emagram + indices
python meteo/radiosonde_payerne.py download   # official MeteoSwiss emagram PDFs
```

Install: `pip install -e .[meteo]`. Data: MeteoSwiss Open Government Data (credit "MeteoSchweiz").
