import type { SVGProps, JSX } from "react";


export default function SVGPlay(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 10 13"
            width={props.size ? props.size * (10 / 13) : 10}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                fill={mainColor}
                fillRule="evenodd"
                clipRule="evenodd"
                d="m2.404.56.021.014 6.33 4.22c.183.122.353.235.483.34.136.11.296.262.389.485a1.2 1.2 0 0 1 0 .92 1.241 1.241 0 0 1-.39.484c-.13.105-.3.218-.482.34l-6.351 4.234a8.38 8.38 0 0 1-.596.376c-.171.093-.406.198-.68.182a1.2 1.2 0 0 1-.885-.474c-.166-.218-.208-.472-.225-.666C0 10.822 0 10.58 0 10.311V1.846c0-.269 0-.51.018-.704C.035.948.078.694.243.476a1.2 1.2 0 0 1 .885-.474c.274-.017.509.09.68.182.17.092.372.227.596.376Z"
            />
        </svg>
    );
}