import type { NextApiRequest, NextApiResponse } from 'next';
import { GoogleAuth } from 'google-auth-library';

const CLOUD_RUN_URL = process.env.CLOUD_RUN_URL as string;
const VERTEX_PROJECT_ID = process.env.VERTEX_PROJECT_ID as string | undefined;
const VERTEX_REGION = process.env.VERTEX_REGION as string | undefined;
const VERTEX_ENDPOINT_ID = process.env.VERTEX_ENDPOINT_ID as string | undefined;

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    // 1) Vertex AI Endpoint (if configured)
    if (VERTEX_PROJECT_ID && VERTEX_REGION && VERTEX_ENDPOINT_ID) {
      const vertexUrl = `https://${VERTEX_REGION}-aiplatform.googleapis.com/v1/projects/${VERTEX_PROJECT_ID}/locations/${VERTEX_REGION}/endpoints/${VERTEX_ENDPOINT_ID}:predict`;
      const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] });
      const client = await auth.getClient();
      const headers = await client.getRequestHeaders();

      const body = { instances: [req.body] };
      const resp = await fetch(vertexUrl, {
        method: 'POST',
        headers: { 'content-type': 'application/json', ...headers },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      res.status(resp.ok ? 200 : resp.status).json(data);
      return;
    }

    if (!CLOUD_RUN_URL) {
      res.status(500).json({ error: 'Set either VERTEX_* envs or CLOUD_RUN_URL' });
      return;
    }

    // If pointing to local dev (no auth needed), call directly
    const isLocal = CLOUD_RUN_URL.startsWith('http://localhost') || CLOUD_RUN_URL.startsWith('http://127.0.0.1');
    if (isLocal) {
      const resp = await fetch(`${CLOUD_RUN_URL}/predict`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(req.body),
      });
      const data = await resp.json();
      res.status(200).json(data);
      return;
    }

    // 2) Cloud Run (auth required)
    const auth = new GoogleAuth({
      credentials: {
        client_email: process.env.GCP_SA_EMAIL,
        private_key: (process.env.GCP_SA_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
      },
    });
    const client = await auth.getIdTokenClient(CLOUD_RUN_URL);
    const resp = await client.request({
      url: `${CLOUD_RUN_URL}/predict`,
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      data: req.body,
    });
    res.status(200).json(resp.data);
  } catch (error: any) {
    res.status(500).json({ error: error?.message ?? 'proxy error' });
  }
}


