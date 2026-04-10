import { NextRequest } from "next/server";
import { proxyApiRequest } from "@/lib/server/api-proxy";

export const dynamic = "force-dynamic";

function upstreamPath(pathParts?: string[]) {
  const tail = (pathParts || []).map((p) => encodeURIComponent(p)).join("/");
  return `/api/chatbot/${tail}`;
}

export async function POST(req: NextRequest, ctx: { params: { path?: string[] } }) {
  return proxyApiRequest(req, upstreamPath(ctx.params.path));
}

