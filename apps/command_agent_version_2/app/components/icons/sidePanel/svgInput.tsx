import type { SVGProps, JSX } from "react";


function SVGCategoryInput(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M8.19985 15.9C8.19985 16.551 8.19985 16.8765 8.27141 17.1436C8.46559 17.8683 9.03164 18.4343 9.75633 18.6285C10.0234 18.7 10.3489 18.7 10.9999 18.7H15.3399C16.516 18.7 17.104 18.7 17.5532 18.4712C17.9484 18.2698 18.2696 17.9486 18.471 17.5534C18.6999 17.1042 18.6999 16.5161 18.6999 15.34V9.46004C18.6999 8.28393 18.6999 7.69587 18.471 7.24666C18.2696 6.85152 17.9484 6.53026 17.5532 6.32892C17.104 6.10004 16.516 6.10004 15.3399 6.10004H10.9999C10.3489 6.10004 10.0234 6.10004 9.75633 6.17159C9.03164 6.36577 8.46559 6.93182 8.27141 7.65652C8.19985 7.92357 8.19985 8.24906 8.19985 8.90004M12.3999 9.60004L15.1999 12.4M15.1999 12.4L12.3999 15.2M15.1999 12.4H6.09985"
            />
        </svg>
    );
}

function SVGCommonInput(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 12"
            width={props.size ?? 12}
            height={props.size ?? 12}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.24006 8.40006C2.24006 8.92084 2.24006 9.18124 2.2973 9.39488C2.45265 9.97463 2.90549 10.4275 3.48524 10.5828C3.69888 10.6401 3.95927 10.6401 4.48006 10.6401H7.95206C8.89295 10.6401 9.36339 10.6401 9.72276 10.457C10.0389 10.2959 10.2959 10.0389 10.457 9.72276C10.6401 9.36339 10.6401 8.89295 10.6401 7.95206V3.24806C10.6401 2.30717 10.6401 1.83673 10.457 1.47735C10.2959 1.16124 10.0389 0.904235 9.72276 0.743168C9.36339 0.560059 8.89295 0.560059 7.95206 0.560059H4.48006C3.95927 0.560059 3.69888 0.560059 3.48524 0.617303C2.90549 0.772648 2.45265 1.22549 2.2973 1.80524C2.24006 2.01888 2.24006 2.27927 2.24006 2.80006M5.60006 3.36006L7.84006 5.60006M7.84006 5.60006L5.60006 7.84006M7.84006 5.60006H0.560059"
            />
        </svg>
    );
}

export default function SVGInput(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryInput {...rest} />; }
    return <SVGCommonInput {...rest} />;
}
