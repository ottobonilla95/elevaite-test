import type { SVGProps, JSX } from "react";


export default function SVGAudio(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 16"
            width={props.size ? props.size * (12 / 16) : 12}
            height={props.size ?? 16}
            fill="none"
            {...props}
        >
            <path
                fill={mainColor}
                fillRule="evenodd"
                clipRule="evenodd"
                d="M5.6 0C4.0536 0 2.8 1.2536 2.8 2.8V7.7C2.8 9.2464 4.0536 10.5 5.6 10.5C7.1464 10.5 8.4 9.2464 8.4 7.7V2.8C8.4 1.2536 7.1464 0 5.6 0Z"
            />
            <path
                fill={mainColor}
                d="M1.4 6.3C1.4 5.9134 1.0866 5.6 0.7 5.6C0.313401 5.6 0 5.9134 0 6.3V7.7C0 10.5562 2.13826 12.913 4.90131 13.2568C4.90044 13.2711 4.9 13.2855 4.9 13.3V14H2.8C2.4134 14 2.1 14.3134 2.1 14.7C2.1 15.0866 2.4134 15.4 2.8 15.4H8.4C8.7866 15.4 9.1 15.0866 9.1 14.7C9.1 14.3134 8.7866 14 8.4 14H6.3V13.3C6.3 13.2855 6.29956 13.2711 6.29869 13.2568C9.06174 12.913 11.2 10.5562 11.2 7.7V6.3C11.2 5.9134 10.8866 5.6 10.5 5.6C10.1134 5.6 9.8 5.9134 9.8 6.3V7.7C9.8 10.0196 7.9196 11.9 5.6 11.9C3.2804 11.9 1.4 10.0196 1.4 7.7V6.3Z"
            />
        </svg>
    );
}
