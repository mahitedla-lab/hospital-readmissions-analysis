"""SYNTHETIC CMS-shaped CSVs for offline smoke tests and CI. This is NOT real CMS data.

The column names match the real Provider Data Catalog files. Known effects are planted
(for-profit and small hospitals have higher excess readmission ratios) so the tests can prove
the hypothesis-test code detects an effect that exists. Never quote results from this data.
"""
from pathlib import Path

import numpy as np
import pandas as pd

STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
          "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY").split()
OWNERSHIP = {
    "Government - Federal": 0.02, "Government - Hospital District or Authority": 0.07,
    "Government - Local": 0.05, "Government - State": 0.03, "Proprietary": 0.20,
    "Voluntary non-profit - Church": 0.08, "Voluntary non-profit - Other": 0.10,
    "Voluntary non-profit - Private": 0.40, "Physician": 0.03, "Tribal": 0.02,
}
MEASURES = ["READM-30-AMI-HRRP", "READM-30-CABG-HRRP", "READM-30-COPD-HRRP",
            "READM-30-HF-HRRP", "READM-30-HIP-KNEE-HRRP", "READM-30-PN-HRRP"]


def make_synthetic(out_dir, n_hospitals: int = 1500, seed: int = 7) -> tuple[Path, Path]:
    rng = np.random.default_rng(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = [f"{100000 + i * 7:06d}" for i in range(n_hospitals)]
    own = rng.choice(list(OWNERSHIP), n_hospitals, p=np.array(list(OWNERSHIP.values())) / sum(OWNERSHIP.values()))
    state = rng.choice(STATES, n_hospitals)
    size = rng.lognormal(5.2, 0.9, n_hospitals)             # latent hospital volume
    info = pd.DataFrame({
        "Facility ID": [i.lstrip("0") if k % 50 == 0 else i for k, i in enumerate(ids)],  # some lose leading zeros
        "Facility Name": [f"SYNTHETIC HOSPITAL {i}" for i in ids],
        "State": state, "Hospital Type": "Acute Care Hospitals", "Hospital Ownership": own,
    })
    drop_info = rng.random(n_hospitals) < 0.02              # some HRRP hospitals missing from General Info
    info = info[~drop_info]

    rows = []
    for k in range(n_hospitals):
        for m in MEASURES:
            if rng.random() < 0.12:                         # hospital does not report this measure
                continue
            discharges = max(int(size[k] * rng.uniform(0.3, 1.2)), 5)
            effect = (0.03 if "Proprietary" in own[k] else 0.0) + (0.025 if size[k] < 120 else 0.0)
            err = float(np.clip(rng.normal(1.0 + effect, 0.06), 0.6, 1.6))
            pred = round(rng.uniform(12, 24), 4)
            suppressed = discharges < 25 and rng.random() < 0.6
            rows.append({
                "Facility Name": f"SYNTHETIC HOSPITAL {ids[k]}", "Facility ID": ids[k], "State": state[k],
                "Measure Name": m,
                "Number of Discharges": "Too Few to Report" if suppressed else f"{discharges:,}",
                "Footnote": "1" if suppressed else "",
                "Excess Readmission Ratio": "N/A" if suppressed else round(err, 4),
                "Predicted Readmission Rate": "N/A" if suppressed else pred,
                "Expected Readmission Rate": "N/A" if suppressed else round(pred / err, 4),
                "Number of Readmissions": "N/A" if suppressed else int(discharges * pred / 100),
                "Start Date": "07/01/2020", "End Date": "06/30/2023",
            })
    hrrp = pd.DataFrame(rows)
    hrrp_path, info_path = out_dir / "hrrp.csv", out_dir / "hospital_general_information.csv"
    hrrp.to_csv(hrrp_path, index=False)
    info.to_csv(info_path, index=False)
    return hrrp_path, info_path
