import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    
    const response = await fetch(`${backendUrl}/chat`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
        const errorText = await response.text();
        return new Response(errorText, { status: response.status });
    }

    // Proxy the response straight back, preserving headers like content-type if streaming
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
      },
    });

  } catch (error) {
    console.error("Chat API Error:", error);
    return new Response(JSON.stringify({ detail: "Internal Server Error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
