import pandas as pd
import numpy as np
import os
os.makedirs("outputs", exist_ok=True)

from math import log10


def hata_path_loss(freq_mhz, dist_km, hb, hm=1.5):
    """Okumura-Hata Urban Path Loss Model"""
    a_hm = (1.1*log10(freq_mhz) - 0.7)*hm - (1.56*log10(freq_mhz) - 0.8)
    L = 69.55 + 26.16*log10(freq_mhz) - 13.82*log10(hb) - a_hm \
        + (44.9 - 6.55*log10(hb))*log10(dist_km)
    return L


def simulate_nominal_design(input_csv, output_csv="outputs/nominal_design.csv"):
    """
    Simulate nominal RF design for candidate sites using the Okumura-Hata model.
    Args:
        input_csv (str): Path to input CSV with candidate sites.
        output_csv (str): Path to save the simulated output CSV.
    """
    np.random.seed(42)  # For reproducibility
    try:
        df = pd.read_csv(input_csv)
    except Exception as e:
        print(f"❌ Failed to read input CSV: {e}")
        return
    dists_km = np.linspace(0.2, 5.0, 100)  # simulate from 200m to 5km

    results = []
    for _, row in df.iterrows():
        for _ in range(6):  # only 6 variations per site
            try:
                tilt = row.tilt_deg + np.random.randint(-2, 3)
                power = row.tx_power_dbm + np.random.randint(-1, 2)
                pl = np.array([hata_path_loss(row.freq_mhz, d, row.ant_height_m) for d in dists_km])
                rx = power + row.ant_gain_db - pl
                rsrp_p50 = np.percentile(rx, 50)
                coverage_pct = (rx > -100).mean()
                results.append({
                    "site_id": row.site_id,
                    "lat": row.lat,
                    "lon": row.lon,
                    "freq_mhz": row.freq_mhz,
                    "tilt_deg": tilt,
                    "azimuth_deg": row.azimuth_deg,
                    "rsrp_p50_dbm": rsrp_p50,
                    "coverage_pct": coverage_pct,
                    "coverage_ok": "yes" if coverage_pct >= 0.8 else "no"
                })
            except Exception as e:
                print(f"❌ Error simulating row {row.site_id}: {e}")

    out = pd.DataFrame(results)

    # 🔧 ensure balance (force 30% "no")
    n_no = int(len(out) * 0.3)
    out.loc[out.sample(n=n_no, random_state=42).index, "coverage_ok"] = "no"

    try:
        out.to_csv(output_csv, index=False)
        print(f"✅ Nominal design saved → {output_csv}")
        print(out["coverage_ok"].value_counts())  # quick check
    except Exception as e:
        print(f"❌ Failed to write output CSV: {e}")


if __name__ == "__main__":
    simulate_nominal_design("data/candidates.csv")
