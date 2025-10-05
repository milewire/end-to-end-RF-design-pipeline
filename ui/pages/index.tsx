// pages/index.tsx
import { useState } from 'react';

export default function Home() {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [batchMsg, setBatchMsg] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = {
        site_id: 'S1',
        lat: 32.7,
        lon: -96.8,
        freq_mhz: 1900,
        tilt_deg: 2,
        azimuth_deg: 90,
        rsrp_p50_dbm: -91,
        coverage_pct: 0.9,
      };
      const resp = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await resp.json();
      setResult(json);
    } catch (err: any) {
      setError(err?.message ?? 'request failed');
    } finally {
      setLoading(false);
    }
  }

  const decision = result?.prediction ?? result?.predictions?.[0] ?? undefined;
  const probYes = typeof result?.prob_yes === 'number' ? result?.prob_yes : (Array.isArray(result?.prob_yes) ? result?.prob_yes?.[0] : undefined);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadMsg(null);
    setError(null);
    try {
      const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8080';
      const form = new FormData();
      form.append('file', file);
      const resp = await fetch(`${backend}/ingest`, { method: 'POST', body: form });
      const json = await resp.json();
      if (!resp.ok) throw new Error(json?.error || 'upload failed');
      setUploadMsg(`Uploaded ${file.name} → ${json.saved_to}`);
    } catch (err: any) {
      setError(err?.message ?? 'upload failed');
    }
  }

  async function onSimulate() {
    setUploadMsg(null);
    setError(null);
    try {
      const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8080';
      const resp = await fetch(`${backend}/simulate-run`, { method: 'POST' });
      const json = await resp.json();
      if (!resp.ok) throw new Error(json?.error || 'simulate failed');
      setUploadMsg(`Simulation complete. Output: ${json.output_csv} (labels: ${JSON.stringify(json.label_counts)})`);
    } catch (err: any) {
      setError(err?.message ?? 'simulate failed');
    }
  }

  function csvToObjects(text: string) {
    const lines = text.split(/\r?\n/).filter(Boolean);
    if (lines.length === 0) return [] as any[];
    const headers = lines[0].split(',').map(h => h.trim());
    return lines.slice(1).map(line => {
      const cols = line.split(',');
      const obj: Record<string, any> = {};
      headers.forEach((h, i) => {
        const v = (cols[i] ?? '').trim();
        const num = Number(v);
        obj[h] = isNaN(num) ? v : num;
      });
      return obj;
    });
  }

  async function onBatchPredict(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBatchMsg(null);
    setError(null);
    try {
      const text = await file.text();
      const records = csvToObjects(text);
      if (records.length === 0) throw new Error('empty CSV');
      // expect headers matching model features plus site_id
      const resp = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ instances: records }),
      });
      const json = await resp.json();
      if (!resp.ok) throw new Error(json?.error || 'batch predict failed');
      const n = Array.isArray(json?.predictions) ? json.predictions.length : 0;
      setBatchMsg(`Predicted ${n} rows. Example: ${JSON.stringify({ prediction: json?.predictions?.[0], prob_yes: json?.prob_yes?.[0] }, null, 0)}`);
    } catch (err: any) {
      setError(err?.message ?? 'batch predict failed');
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: 'system-ui, sans-serif', lineHeight: 1.45, background: '#0b0b0b', color: '#f5f5f5', minHeight: '100vh' }}>
      <h1 style={{ margin: 0, color: '#ff7a00' }}>RF Coverage Predictor</h1>
      <p style={{ marginTop: 8, color: '#d7d7d7' }}>
        Enter RF site parameters and get a fast yes/no coverage decision. This demo uses a trained
        RandomForest model; coming soon: probability details and feature importance.
      </p>

      <section style={{ background: '#151515', border: '1px solid #ff7a00', padding: 16, borderRadius: 8, margin: '16px 0' }}>
        <h3 style={{ marginTop: 0 }}>What to expect</h3>
        <ul style={{ margin: '8px 0 0 20px' }}>
          <li>Immediate yes/no classification under Results.</li>
          <li>If available, a probability for the "yes" outcome.</li>
          <li>You can review the exact request we send and the raw response.</li>
        </ul>
      </section>

      <form onSubmit={onSubmit}>
        <button
          type="submit"
          disabled={loading}
          style={{
            background: '#ff7a00',
            color: '#0b0b0b',
            border: 'none',
            padding: '10px 16px',
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 600
          }}
        >
          {loading ? 'Predicting…' : 'Predict example'}
        </button>
      </form>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {uploadMsg && <p style={{ color: '#ffae66' }}>{uploadMsg}</p>}

      <section style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>Ingest and simulate</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <input type="file" accept=".csv" onChange={onUpload} />
          <button onClick={onSimulate} style={{ background: '#ff7a00', color: '#0b0b0b', border: 'none', padding: '8px 12px', borderRadius: 6, cursor: 'pointer', fontWeight: 600 }}>Run simulate</button>
        </div>
        <p style={{ marginTop: 8, color: '#d7d7d7' }}>Upload candidate sites CSV and run the RF simulation. The output CSV will be generated on the backend.</p>
      </section>

      <section style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>Batch predict (CSV → predictions)</h3>
        <input type="file" accept=".csv" onChange={onBatchPredict} />
        <p style={{ marginTop: 8, color: '#d7d7d7' }}>
          Provide a CSV with headers matching the model features
          (lat, lon, freq_mhz, tilt_deg, azimuth_deg, rsrp_p50_dbm, coverage_pct, site_id optional).
          We send rows directly to the prediction API.
        </p>
        {batchMsg && <p style={{ color: '#ffae66' }}>{batchMsg}</p>}
      </section>

      <section style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 8 }}>Sample request</h3>
        <pre style={{ background: '#0f0f0f', padding: 16, borderRadius: 8, border: '1px solid #222', color: '#f0f0f0' }}>
{`{
  site_id: "S1",
  lat: 32.7,
  lon: -96.8,
  freq_mhz: 1900,
  tilt_deg: 2,
  azimuth_deg: 90,
  rsrp_p50_dbm: -91,
  coverage_pct: 0.9
}`}
        </pre>
      </section>

      {result && (
        <section style={{ marginTop: 16 }}>
          <h3 style={{ marginBottom: 8 }}>Results</h3>
          <div style={{ background: '#151515', padding: 16, borderRadius: 8, border: '1px solid #ff7a00' }}>
            <p style={{ marginTop: 0 }}>Decision: <strong>{String(decision)}</strong></p>
            {typeof probYes === 'number' && (
              <p>Probability (yes): {(probYes * 100).toFixed(1)}%</p>
            )}
            <p style={{ marginTop: 8 }} title="yes = predicted to meet coverage target (≥80% area above −100 dBm)">
              What this means: <em>"yes"</em> indicates the configuration is predicted to meet the
              coverage target (≥80% of area above −100 dBm). <em>"no"</em> indicates it likely falls short.
            </p>
            {String(decision) === 'no' && (
              <p style={{ color: '#ffae66' }}>
                Next steps: try adjusting <code>tilt_deg</code> (+1–2), refine <code>azimuth_deg</code>,
                or target higher <code>rsrp_p50_dbm</code> (+2 dB). Re-run to compare.
              </p>
            )}
            <details>
              <summary>Raw response</summary>
              <pre style={{ background: '#0f0f0f', padding: 16, borderRadius: 8, overflowX: 'auto', border: '1px solid #222', color: '#f0f0f0' }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        </section>
      )}
    </main>
  );
}
