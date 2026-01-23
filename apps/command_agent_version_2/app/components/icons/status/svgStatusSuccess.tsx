import type { SVGProps, JSX } from "react";


export default function SVGStatusSuccess(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 10 10"
            width={props.size ?? 10}
            height={props.size ?? 10}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                fillRule="evenodd"
                clipRule="evenodd"
                d="M4.928 0C2.20634 0 0 2.20634 0 4.928C0 7.64966 2.20634 9.856 4.928 9.856C7.64966 9.856 9.856 7.64966 9.856 4.928C9.856 2.20634 7.64966 0 4.928 0ZM7.26079 3.90078C7.43574 3.72583 7.43574 3.44217 7.26079 3.26722C7.08583 3.09226 6.80217 3.09226 6.62722 3.26722L4.256 5.63843L3.22878 4.61122C3.05383 4.43626 2.77017 4.43626 2.59522 4.61122C2.42026 4.78617 2.42026 5.06983 2.59522 5.24478L3.93922 6.58878C4.11417 6.76374 4.39783 6.76374 4.57278 6.58878L7.26079 3.90078Z"
            />
        </svg>
    );
}
