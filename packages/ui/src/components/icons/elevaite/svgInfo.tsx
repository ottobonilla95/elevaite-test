import type { JSX } from "react";
import type { SVGProps } from "react";

function SVGInfoMain(props: SVGProps<SVGSVGElement> & { color: string; size?: number }): JSX.Element {
  return (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        height={props.size ? props.size : 16}
        width={props.size ? props.size : 16}
        fill="none"
        {...props}
    >
        <path
            d="M32 10c-12.15 0-22 9.85-22 22s9.85 22 22 22 22-9.85 22-22-9.85-22-22-22zm0 4c9.941 0 18 8.059 18 18s-8.059 18-18 18-18-8.059-18-18 8.059-18 18-18zm0 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm0 9a2 2 0 0 0-2 2v10a2 2 0 0 0 4 0V32a2 2 0 0 0-2-2z"
            fill={props.color}
        />
    </svg>
  );
}

function SVGInfoAlt(props: SVGProps<SVGSVGElement> & { color: string; size?: number }): JSX.Element {
    return (
        <svg
            fill="none"
            height={props.size ? props.size : 12}
            viewBox="0 0 12 12"
            width={props.size ? props.size : 12}
            xmlns="http://www.w3.org/2000/svg"
            {...props}
        >
            <path
                fill={props.color}
                clipRule="evenodd"
                fillRule="evenodd"
                d="M6 .5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11Zm0 3a.5.5 0 0 0 0 1h.005a.5.5 0 0 0 0-1H6ZM6.5 6a.5.5 0 0 0-1 0v2a.5.5 0 0 0 1 0V6Z"
            />
        </svg>
    );
}

function SVGInfo(props: SVGProps<SVGSVGElement> & { type?: "main" | "alt"; size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    switch (props.type) {
        case "alt": return <SVGInfoAlt color={mainColor} size={props.size} />;
        default: return <SVGInfoMain color={mainColor} size={props.size} />;
    }
}

export default SVGInfo;
