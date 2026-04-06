import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    
    // We pass the formData containing the files exactly as received
    const response = await fetch(`${backendUrl}/ingest`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
      },
    });

  } catch (error) {
    console.error("Ingest API Error:", error);
    return new Response(JSON.stringify({ detail: "Internal Server Error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
