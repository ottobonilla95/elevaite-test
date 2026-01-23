import type { SVGProps, JSX } from "react";


function SVGCategoryTrigger(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 25 25"
            width={props.size ?? 25}
            height={props.size ?? 25}
            fill="none"
            {...props}
        >
            <rect width="24.8" height="24.8" rx="6" fill={mainColor} />
            <path
                stroke="white"
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12.4 6.79999V18M16.6 8.19999L8.20005 16.6M18 12.4H6.80005M16.6 16.6L8.20005 8.19999"
            />
        </svg>
    );
}

function SVGCommonTrigger(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 11 11"
            width={props.size ?? 11}
            height={props.size ?? 11}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5.04006 0.559998V9.52M8.40006 1.68L1.68006 8.4M9.52006 5.04H0.560059M8.40006 8.4L1.68006 1.68"
            />
        </svg>
    );
}

export default function SVGTrigger(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryTrigger {...rest} />; }
    return <SVGCommonTrigger {...rest} />;
}
