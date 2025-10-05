import pandas as pd

df = pd.read_csv("outputs/nominal_design.csv")
df["coverage_ok"] = df["coverage_ok"].map({1: "yes", 0: "no"})
df.to_csv("outputs/nominal_design_fixed.csv", index=False)

print("✅ Fixed CSV saved → outputs/nominal_design_fixed.csv")
