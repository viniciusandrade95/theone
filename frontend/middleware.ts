import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

function join(base: string, path: string) {
  if (!base) return path;
  return `${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const tenantId = request.cookies.get("tenant_id")?.value;

  if ((!token || !tenantId) && !request.nextUrl.pathname.startsWith(join(request.nextUrl.basePath ?? "", "/login"))) {
    const url = request.nextUrl.clone();
    url.pathname = join(request.nextUrl.basePath ?? "", "/login");
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
