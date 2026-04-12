import * as React from "react";

type IconProps = React.SVGProps<SVGSVGElement> & { title?: string };

export function IconMenu({ title = "Menu", ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden={props["aria-label"] ? undefined : true}
      role={props["aria-label"] ? "img" : "presentation"}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function IconX({ title = "Close", ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden={props["aria-label"] ? undefined : true}
      role={props["aria-label"] ? "img" : "presentation"}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <path
        d="M6 6l12 12M18 6l-12 12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function IconLogout({ title = "Logout", ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden={props["aria-label"] ? undefined : true}
      role={props["aria-label"] ? "img" : "presentation"}
      {...props}
    >
      {title ? <title>{title}</title> : null}
      <path
        d="M10 7V6a2 2 0 012-2h6a2 2 0 012 2v12a2 2 0 01-2 2h-6a2 2 0 01-2-2v-1"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M15 12H3m0 0l3-3M3 12l3 3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

