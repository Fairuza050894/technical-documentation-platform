import type { SVGProps } from "react";

export type IconName =
  | "activity"
  | "alert"
  | "arrow-right"
  | "catalog"
  | "changes"
  | "check"
  | "chevron-down"
  | "clock"
  | "documents"
  | "folder"
  | "overview"
  | "projects"
  | "refresh"
  | "review"
  | "server"
  | "settings"
  | "source"
  | "sync"
  | "upload";

interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 18, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
      {...props}
    >
      <g
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.75"
      >
        {renderIcon(name)}
      </g>
    </svg>
  );
}

function renderIcon(name: IconName) {
  switch (name) {
    case "overview":
      return (
        <>
          <rect height="7" rx="1" width="7" x="3" y="3" />
          <rect height="7" rx="1" width="7" x="14" y="3" />
          <rect height="7" rx="1" width="7" x="3" y="14" />
          <rect height="7" rx="1" width="7" x="14" y="14" />
        </>
      );
    case "projects":
    case "folder":
      return (
        <>
          <path d="M3.5 7.5h6l1.8 2H20.5v8.75a1.75 1.75 0 0 1-1.75 1.75H5.25A1.75 1.75 0 0 1 3.5 18.25Z" />
          <path d="M3.5 7.5V5.75A1.75 1.75 0 0 1 5.25 4h4l2 2h7.5a1.75 1.75 0 0 1 1.75 1.75V9.5" />
        </>
      );
    case "source":
      return (
        <>
          <path d="M6.5 3.5h7l4 4v13h-11a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
          <path d="M13.5 3.5v4h4" />
          <path d="m9.5 12-2 2 2 2" />
          <path d="m12.5 12 2 2-2 2" />
        </>
      );
    case "catalog":
      return (
        <>
          <rect height="4" rx="1" width="6" x="9" y="3" />
          <rect height="4" rx="1" width="6" x="3" y="17" />
          <rect height="4" rx="1" width="6" x="15" y="17" />
          <path d="M12 7v4M6 17v-2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2" />
        </>
      );
    case "changes":
      return (
        <>
          <path d="M4 7h12" />
          <path d="m13 4 3 3-3 3" />
          <path d="M20 17H8" />
          <path d="m11 14-3 3 3 3" />
        </>
      );
    case "documents":
      return (
        <>
          <path d="M6.5 3.5h7l4 4v13h-11a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
          <path d="M13.5 3.5v4h4M8 12h6M8 16h6" />
        </>
      );
    case "server":
      return (
        <>
          <rect height="6" rx="1.5" width="17" x="3.5" y="3.5" />
          <rect height="6" rx="1.5" width="17" x="3.5" y="14.5" />
          <path d="M7 6.5h.01M7 17.5h.01M10 6.5h7M10 17.5h7" />
        </>
      );
    case "settings":
      return (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
        </>
      );
    case "activity":
      return <path d="M3 12h4l2.3-6 4.2 12 2.2-6H21" />;
    case "alert":
      return (
        <>
          <path d="M10.3 4.1 2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z" />
          <path d="M12 9v4M12 17h.01" />
        </>
      );
    case "check":
      return (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="m8 12 2.6 2.6L16.5 9" />
        </>
      );
    case "arrow-right":
      return (
        <>
          <path d="M5 12h14M14 7l5 5-5 5" />
        </>
      );
    case "chevron-down":
      return <path d="m7 9.5 5 5 5-5" />;
    case "clock":
      return (
        <>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v5l3 2" />
        </>
      );
    case "refresh":
    case "sync":
      return (
        <>
          <path d="M20 7v5h-5" />
          <path d="M4 17v-5h5" />
          <path d="M6.1 8.2A7 7 0 0 1 18.6 7L20 12" />
          <path d="M17.9 15.8A7 7 0 0 1 5.4 17L4 12" />
        </>
      );
    case "review":
      return (
        <>
          <path d="M6.5 3.5h7l4 4v13h-11a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
          <path d="M13.5 3.5v4h4M8 13l2 2 4-4" />
        </>
      );
    case "upload":
      return (
        <>
          <path d="M12 16V4M7.5 8.5 12 4l4.5 4.5" />
          <path d="M5 14v5h14v-5" />
        </>
      );
  }
}
