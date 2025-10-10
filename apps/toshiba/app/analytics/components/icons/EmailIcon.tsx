import type { JSX } from "react";

interface EmailIconProps {
  width?: number;
  height?: number;
  className?: string;
}

export function EmailIcon({
  width = 48,
  height = 48,
  className = "",
}: EmailIconProps): JSX.Element {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect
        width="47.68"
        height="47.68"
        rx="23.84"
        fill="var(--ev-colors-highlight)"
        fillOpacity="0.2"
      />
      <path
        d="M36.38 31.7573L27.6114 23.8373M20.0686 23.8373L11.3001 31.7573M10.64 17.2373L21.4177 24.7817C22.2905 25.3927 22.7268 25.6981 23.2015 25.8164C23.6208 25.9209 24.0593 25.9209 24.4785 25.8164C24.9532 25.6981 25.3896 25.3927 26.2623 24.7817L37.04 17.2373M16.976 34.3973H30.704C32.9218 34.3973 34.0307 34.3973 34.8778 33.9657C35.6229 33.5861 36.2287 32.9803 36.6084 32.2351C37.04 31.3881 37.04 30.2792 37.04 28.0613V19.6133C37.04 17.3955 37.04 16.2866 36.6084 15.4395C36.2287 14.6944 35.6229 14.0886 34.8778 13.709C34.0307 13.2773 32.9218 13.2773 30.704 13.2773H16.976C14.7582 13.2773 13.6493 13.2773 12.8022 13.709C12.0571 14.0886 11.4513 14.6944 11.0716 15.4395C10.64 16.2866 10.64 17.3955 10.64 19.6133V28.0613C10.64 30.2792 10.64 31.3881 11.0716 32.2351C11.4513 32.9803 12.0571 33.5861 12.8022 33.9657C13.6493 34.3973 14.7582 34.3973 16.976 34.3973Z"
        stroke="var(--ev-colors-highlight)"
        strokeWidth="2.64"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
