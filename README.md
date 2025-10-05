# Orchestrate an End-to-End RF Design Pipeline

This project provides a complete pipeline for RF (Radio Frequency) design, including candidate site management, simulation, model training, and cloud integration.

## Project Structure

```text
Orchestrate an end-to-end RF design pipeline/
│
├── data/
│   └── candidates.csv           # Input candidate sites
│
├── outputs/
│   └── (generated CSV + maps)   # Simulation and result outputs
│
├── simulate.py                  # RF simulation logic
├── pipeline.py                  # Orchestrates the full pipeline
├── gcs_utils.py                 # Google Cloud Storage helpers
├── sklearn_train.py             # Local sklearn trainer (RandomForest)
├── serve.py                     # FastAPI app to serve predictions
├── Dockerfile                   # Container for serving on Vertex AI / Cloud Run
├── vertex_train.py              # (Optional) Vertex training helpers
├── requirements.txt             # Python dependencies
├── ui/                          # Next.js Web UI (port 3000)
│   ├── pages/
│   │   ├── index.tsx            # Frontend app
│   │   └── api/predict.ts       # API route that proxies to backend/Vertex
│   ├── package.json             # UI scripts and deps
│   └── next.config.js           # Next.js config
└── README.md                    # Project documentation
```

## Purpose of the App

This app simulates and trains a radio frequency (RF) coverage prediction model using a synthetic dataset and a machine learning pipeline. It serves as an end-to-end automated RF optimization workflow that mimics a telecom AI planning tool.

### In other words

- Simulate cell-site coverage
- Train a predictive model
- Deploy it to the cloud
- Use it for instant RF design decisions

## Pipeline Breakdown

### Simulation Step (`simulate_nominal_design`)

- Uses the Okumura–Hata propagation model to estimate path loss and coverage.
- Reads candidate site parameters (lat, lon, azimuth, frequency, tilt, etc.) from `data/candidates.csv`.
- Produces `outputs/nominal_design.csv` with:
  - Predicted RSRP (signal strength)
  - Estimated coverage percentage
  - Binary label `coverage_ok` (yes/no)

### Upload Step

- Uploads the CSV to your GCS bucket (e.g., `gs://rf-demo-bucket/`).

### Machine Learning Step

- Default (local): trains a scikit-learn `RandomForestClassifier` via `sklearn_train.py` and saves `outputs/rf_model.pkl`.
- Optional (Vertex AutoML): uses `vertex_train.py` to create a Vertex AI Tabular Dataset and train an AutoML classification model to predict `coverage_ok`.

### Deployment Step

- Fast path (recommended for quick testing): containerized FastAPI app on Cloud Run.
- Optional: deploy the container as a Vertex AI Endpoint for managed online prediction in Vertex AI.

## Setup Instructions

1. **Install Python dependencies:**

```sh
pip install -r requirements.txt
```

2. **Google Cloud Setup:**
   - Create a Google Cloud service account with access to your GCS bucket.
   - Download the service account key JSON file.
   - Set the environment variable:

```sh
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\service-account-key.json
```

3. **Prepare Data:**
   - Place your candidate site data in `data/candidates.csv`.

4. **Web UI (Next.js) Setup:**

```sh
cd ui
npm install
npm run dev
# UI runs on http://localhost:3000
```

### Required Environment Variables

- Backend (FastAPI/Cloud Run):
  - `GOOGLE_APPLICATION_CREDENTIALS` (for local dev only; not needed in production if using Workload Identity)

- UI (Next.js):
  - For local FastAPI: `NEXT_PUBLIC_BACKEND_URL` (e.g., `http://127.0.0.1:8080`)
  - For Cloud Run: `CLOUD_RUN_URL` (e.g., `https://your-cloud-run-url.a.run.app`)
    - If your Cloud Run service is private, also set `GCP_SA_EMAIL` and `GCP_SA_PRIVATE_KEY` (not needed for public or Vertex AI endpoints)
  - For Vertex AI Endpoint (recommended for production):
    - `VERTEX_PROJECT_ID` (e.g., `rf-demo-vertex`)
    - `VERTEX_REGION` (e.g., `us-central1`)
    - `VERTEX_ENDPOINT_ID` (your endpoint ID from Vertex AI)

> **Do not commit secrets.** Provide values via your shell or `.env.local` in `ui/` (gitignored). For Vertex AI, you do NOT need to set `GCP_SA_PRIVATE_KEY` or `GCP_SA_EMAIL` if using Workload Identity (recommended for production).

## Usage

- **Simulation:**
  - Run `simulate.py` to perform RF simulations on candidate sites.
    ```sh
    python simulate.py
    ```

- **Pipeline Orchestration (simulate + upload + local train):**
  - Use `pipeline.py` to run simulation, upload to GCS, and train a local model.
    ```sh
    python pipeline.py
    ```

- **Local Model Training (standalone):**
  - Train a RandomForest on the simulated CSV and save `outputs/rf_model.pkl`.
    ```sh
    python -c "from sklearn_train import train_local_model; train_local_model('outputs/nominal_design.csv')"
    ```

- **Serve Locally (FastAPI):**
  - Start the API on port 8080:
    ```sh
    uvicorn serve:app --reload --port 8080
    ```
  - Test from PowerShell:
    ```powershell
    $payload = @{ site_id = "S1"; lat = 32.7; lon = -96.8; freq_mhz = 1900; tilt_deg = 2; azimuth_deg = 90; rsrp_p50_dbm = -91; coverage_pct = 0.9 } | ConvertTo-Json
    Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8080/predict -ContentType 'application/json' -Body $payload
    ```

- **Docker (local test):**
  - Build image and run container mapped to 8081:
    ```sh
    docker build -t rf-model:local .
    docker run -d -p 8081:8080 --name rf-model rf-model:local
    ```
  - Health check and predict:
    ```powershell
    Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8081/
    $payload = @{ site_id = "S1"; lat = 32.7; lon = -96.8; freq_mhz = 1900; tilt_deg = 2; azimuth_deg = 90; rsrp_p50_dbm = -91; coverage_pct = 0.9 } | ConvertTo-Json
    Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8081/predict -ContentType 'application/json' -Body $payload
    ```

- **Run Web UI (local):**
  - In a separate terminal:
    ```sh
    cd ui
    npm run dev
    # open http://localhost:3000
    ```
  - By default, the UI calls the Next.js API route at `/api/predict` which forwards to either Vertex AI or Cloud Run based on envs. For local FastAPI, set:
    ```sh
    # in ui/.env.local
    NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8080
    ```
  - Typical local dev workflow:
    1. Terminal A: `uvicorn serve:app --reload --port 8080`
    2. Terminal B: `cd ui && npm run dev`
    3. Open the UI at `http://localhost:3000` and use the example predict, upload your CSV, and run simulate.

- **Deploy to Vertex AI (container):**
  - Replace placeholders and run:
    ```sh
    gcloud auth configure-docker
    docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/rf-model:latest .
    docker push us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/rf-model:latest

    gcloud ai models upload \
      --region=us-central1 \
      --display-name=rf-model \
      --container-image-uri=us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/rf-model:latest

    gcloud ai endpoints create --region=us-central1 --display-name=rf-endpoint

    gcloud ai endpoints deploy-model <ENDPOINT_ID> \
      --region=us-central1 \
      --model=<MODEL_ID> \
      --machine-type=n1-standard-2
    ```

- **Cloud Run (recommended managed serving):**
  - Build and deploy:
    ```sh
    gcloud run deploy rf-model \
      --source . \
      --region us-central1 \
      --allow-unauthenticated \
      --port 8080
    ```
  - Set in the UI environment:
    ```sh
    CLOUD_RUN_URL=https://<your-cloud-run-url>
    # optional SA creds for signed requests if service is private
    GCP_SA_EMAIL=service-account@project.iam.gserviceaccount.com
    GCP_SA_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
    ```
  - The Next.js API route `ui/pages/api/predict.ts` will detect whether to call Vertex AI or Cloud Run based on which envs you provide. For private Cloud Run services, the service account credentials above are used to mint an ID token.

## API Endpoints (backend)

- `GET /` — health check → `{ status: "ok" }`
- `POST /ingest` — upload CSV (form-data `file`) → saves to `data/candidates.csv`
- `POST /simulate-run` — runs simulation and returns label counts
- `POST /predict` — accepts either a single JSON object payload or `{ instances: [...] }`

Example single predict:
```bash
curl -s -X POST http://127.0.0.1:8080/predict \
  -H 'content-type: application/json' \
  -d '{
    "site_id": "S1",
    "lat": 32.7,
    "lon": -96.8,
    "freq_mhz": 1900,
    "tilt_deg": 2,
    "azimuth_deg": 90,
    "rsrp_p50_dbm": -91,
    "coverage_pct": 0.9
  }'
```

Example batch predict:
```bash
curl -s -X POST http://127.0.0.1:8080/predict \
  -H 'content-type: application/json' \
  -d '{
    "instances": [
      {"site_id":"S1","lat":32.7,"lon":-96.8,"freq_mhz":1900,"tilt_deg":2,"azimuth_deg":90,"rsrp_p50_dbm":-91,"coverage_pct":0.9},
      {"site_id":"S2","lat":32.8,"lon":-96.7,"freq_mhz":1900,"tilt_deg":3,"azimuth_deg":180,"rsrp_p50_dbm":-95,"coverage_pct":0.85}
    ]
  }'
```

## Troubleshooting

- **Missing dependencies:**
  - Ensure you have run `pip install -r requirements.txt`.
- **Google Cloud authentication errors:**
  - Check that your `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly and points to a valid service account JSON file.
- **File not found errors:**
  - Make sure your input files are in the correct locations (e.g., `data/candidates.csv`).

## Contributing

Contributions are welcome! To contribute:
- Fork the repository
- Create a new branch for your feature or bugfix
- Make your changes with clear commit messages
- Submit a pull request describing your changes

## Requirements
- Python 3.11+
- numpy
- pandas
- scikit-learn
- joblib
- fastapi
- uvicorn
- google-cloud-storage
- google-cloud-aiplatform

## License

This project is intended for educational and research purposes.

## Deploying Backend to Google Cloud Run

To deploy the backend (FastAPI app) to Google Cloud Run:

1. **Authenticate and set your project:**
   ```sh
   gcloud auth login
   gcloud config set project rf-demo-vertex
   ```
2. **Enable required APIs:**
   ```sh
   gcloud services enable serviceusage.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```
3. **Build and push Docker image:**
   ```sh
   docker build -t gcr.io/rf-demo-vertex/my-backend .
   gcloud auth configure-docker
   docker push gcr.io/rf-demo-vertex/my-backend
   ```
4. **Deploy to Cloud Run:**
   ```sh
   gcloud run deploy my-backend --image gcr.io/rf-demo-vertex/my-backend --platform managed --region us-central1 --allow-unauthenticated
   ```
5. **Copy the Cloud Run URL** and use it as your backend endpoint in the frontend (see environment variable setup below).

---

## .gitignore Best Practices

- The root `.gitignore` covers Python, data, logs, outputs, and environment files.
- The `ui/.gitignore` covers Node.js/Next.js build artifacts and environment files for the frontend.
- **Never commit any `.env`, `.env.local`, or secret files.**
- Both backend and frontend ignore their respective environment and build files.

---
