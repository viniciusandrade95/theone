import { NextRequest, NextResponse } from "next/server";

const PROXY_HOP_HEADER = "x-beauty-proxy-hop";

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
  // We want to control compression to avoid mismatches when proxying.
  "accept-encoding",
]);

const RESPONSE_STRIP_HEADERS = new Set([
  // When proxying, Node fetch may transparently decompress upstream responses, but headers can still advertise encoding.
  // Stripping prevents the browser from attempting to decode/combine with an incorrect content-length.
  "content-encoding",
  "content-length",
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
  // Avoid upstream sending compressed responses that can be mismatched when proxying.
  headers.set("accept-encoding", "identity");
  return headers;
}

function _responseHeaders(resp: Response): Headers {
  const headers = new Headers();
  resp.headers.forEach((value, key) => {
    const lowered = key.toLowerCase();
    if (HOP_BY_HOP_HEADERS.has(lowered)) {
      return;
    }
    if (RESPONSE_STRIP_HEADERS.has(lowered)) {
      return;
    }
    headers.set(key, value);
  });
  return headers;
}

export async function proxyApiRequest(req: NextRequest, upstreamPathname: string): Promise<NextResponse> {
  try {
    if (req.headers.get(PROXY_HOP_HEADER) === "1") {
      return NextResponse.json(
        {
          error: "API_PROXY_LOOP",
          details: {
            message:
              "Proxy loop detected. Your frontend is forwarding requests back to itself. Check the frontend env var API_BASE_URL and ensure it points to the API service URL (not the frontend URL).",
          },
        },
        { status: 500 },
      );
    }

    const upstreamUrl = _toUpstreamUrl(req, upstreamPathname);
    const upstreamHost = new URL(upstreamUrl).host;
    const requestHost = new URL(req.url).host;
    if (upstreamHost === requestHost) {
      return NextResponse.json(
        {
          error: "API_PROXY_LOOP",
          details: {
            message:
              "API_BASE_URL resolves to the same host as the frontend. Set API_BASE_URL to your API service URL (a different Render service/domain).",
            upstreamHost,
            requestHost,
          },
        },
        { status: 500 },
      );
    }

    const method = req.method.toUpperCase();

    const headers = _forwardHeaders(req);
    headers.set(PROXY_HOP_HEADER, "1");

    const hasBody = !["GET", "HEAD"].includes(method);
    const body = hasBody ? await req.arrayBuffer() : undefined;

    const upstreamResp = await fetch(upstreamUrl, {
      method,
      headers,
      body,
      // Follow redirects server-side (e.g. http->https), so the browser never has to follow a cross-origin redirect.
      redirect: "follow",
    });

    const respHeaders = _responseHeaders(upstreamResp);
    const bytes = await upstreamResp.arrayBuffer();
    return new NextResponse(bytes, {
      status: upstreamResp.status,
      headers: respHeaders,
    });
  } catch (err) {
    const message = err instanceof Error && err.message ? err.message : "Unknown proxy error.";
    return NextResponse.json(
      {
        error: "API_PROXY_ERROR",
        details: {
          message: `Failed to reach API from frontend. ${message}`,
          hint: "Check frontend env var API_BASE_URL and confirm the API service is reachable.",
        },
      },
      { status: 502 },
    );
  }
}
