export async function GET() {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const start = Date.now();
  try {
    const response = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    const latency = Date.now() - start;
    const data = await response.json();
    return new Response(JSON.stringify({ status: data.status, latency }), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return new Response(JSON.stringify({ status: "offline", latency: null }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}
