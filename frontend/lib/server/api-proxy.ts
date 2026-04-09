import { NextRequest, NextResponse } from "next/server";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
]);

function _getApiBaseUrl(): string {
  const raw =
    (process.env.API_BASE_URL || "").trim() ||
    (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  if (!raw) {
    throw new Error("Missing API base URL. Set API_BASE_URL (recommended) or NEXT_PUBLIC_API_BASE_URL on the frontend service.");
  }
  // Basic safety: require absolute http(s) URL.
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error(`Invalid API base URL: ${raw}`);
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`Invalid API base URL protocol: ${parsed.protocol}`);
  }
  return parsed.toString().replace(/\/$/, "");
}

function _toUpstreamUrl(req: NextRequest, upstreamPathname: string): string {
  const base = _getApiBaseUrl();
  const url = new URL(req.url);
  const upstream = new URL(`${base}${upstreamPathname}${url.search}`);
  return upstream.toString();
}

function _forwardHeaders(req: NextRequest): Headers {
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    const lowered = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowered)) {
      return;
    }
    headers.set(key, value);
  });
  return headers;
}

function _responseHeaders(resp: Response): Headers {
  const headers = new Headers();
  resp.headers.forEach((value, key) => {
    const lowered = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowered)) {
      return;
    }
    headers.set(key, value);
  });
  return headers;
}

export async function proxyApiRequest(req: NextRequest, upstreamPathname: string): Promise<NextResponse> {
  const upstreamUrl = _toUpstreamUrl(req, upstreamPathname);
  const method = req.method.toUpperCase();

  const headers = _forwardHeaders(req);

  const hasBody = !["GET", "HEAD"].includes(method);
  const body = hasBody ? await req.arrayBuffer() : undefined;

  const upstreamResp = await fetch(upstreamUrl, {
    method,
    headers,
    body,
    redirect: "manual",
  });

  const respHeaders = _responseHeaders(upstreamResp);
  const bytes = await upstreamResp.arrayBuffer();
  return new NextResponse(bytes, {
    status: upstreamResp.status,
    headers: respHeaders,
  });
}

