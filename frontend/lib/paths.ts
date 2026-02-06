export const APP_BASE_PATH = process.env.NEXT_PUBLIC_APP_BASE_PATH ?? "";

export function appPath(path: string) {
  if (!path.startsWith("/")) path = `/${path}`;
  return `${APP_BASE_PATH}${path}`;
}
