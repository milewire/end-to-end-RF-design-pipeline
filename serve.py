import joblib
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

# Load the trained model artifact
artifact = joblib.load("outputs/rf_model.pkl")
if isinstance(artifact, dict) and "model" in artifact and "feature_names" in artifact:
    model = artifact["model"]
    feature_names = artifact["feature_names"]
else:
    # Fallback for legacy plain-model artifact; assume features except target and non-numeric
    model = artifact
    feature_names = [
        "lat",
        "lon",
        "freq_mhz",
        "tilt_deg",
        "azimuth_deg",
        "rsrp_p50_dbm",
        "coverage_pct",
    ]

# Define input schema (match your CSV columns except target)
class RFInput(BaseModel):
    site_id: str
    lat: float
    lon: float
    freq_mhz: float
    tilt_deg: float
    azimuth_deg: float
    rsrp_p50_dbm: float
    coverage_pct: float

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/v1/endpoints/{endpoint_id}/deployedModels/{deployed_model_id}")
def vertex_readiness(endpoint_id: str, deployed_model_id: str):
    # Vertex AI issues readiness probes against this path.
    # Returning 200 signals the container is healthy and ready.
    return {"status": "ready", "endpoint": endpoint_id, "deployed_model": deployed_model_id}

@app.post("/ingest")
async def ingest_csv(file: UploadFile = File(...)):
    """Ingest a CSV of candidate sites and save to data/candidates.csv."""
    import os
    contents = await file.read()
    os.makedirs("data", exist_ok=True)
    path = "data/candidates.csv"
    with open(path, "wb") as f:
        f.write(contents)
    return {"saved_to": path, "bytes": len(contents)}

@app.post("/simulate-run")
def simulate_run():
    """Run simulation on the current candidates CSV and return quick stats."""
    from simulate import simulate_nominal_design
    import os
    output_path = "outputs/nominal_design.csv"
    simulate_nominal_design("data/candidates.csv", output_path)
    try:
        df = pd.read_csv(output_path)
        counts = df["coverage_ok"].value_counts().to_dict()
    except Exception:
        counts = {}
    return {"output_csv": output_path, "label_counts": counts}

def _predict(records: List[Dict[str, Any]]):
    df = pd.DataFrame.from_records(records)
    df = df[feature_names]
    preds = model.predict(df)
    labels = ["yes" if int(p) == 1 else "no" for p in preds]
    prob_yes = None
    if hasattr(model, "predict_proba"):
        try:
            prob = model.predict_proba(df)
            # probability of class 1 ("yes")
            prob_yes = prob[:, 1].tolist()
        except Exception:
            prob_yes = None
    return labels, prob_yes

@app.post("/predict")
def predict(payload: Dict[str, Any]):
    # Support Vertex AI style payload: {"instances": [ {..}, {..} ]}
    if isinstance(payload, dict) and "instances" in payload:
        instances = payload.get("instances", [])
        if isinstance(instances, dict):
            instances = [instances]
        labels, prob_yes = _predict(instances)
        resp: Dict[str, Any] = {"predictions": labels}
        if prob_yes is not None:
            resp["prob_yes"] = prob_yes
        return resp

    # Backward-compatible single-object payload
    if isinstance(payload, dict):
        labels, prob_yes = _predict([payload])
        resp: Dict[str, Any] = {"prediction": labels[0]}
        if prob_yes is not None:
            resp["prob_yes"] = prob_yes[0]
        return resp

    # Fallback for unexpected payloads
    return {"error": "Invalid payload"}


