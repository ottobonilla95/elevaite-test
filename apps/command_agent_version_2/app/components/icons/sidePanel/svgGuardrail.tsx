import type { SVGProps, JSX } from "react";


function SVGCategoryGuardrail(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M12.3999 19.4C16.2659 19.4 19.3999 16.266 19.3999 12.4C19.3999 8.534 16.2659 5.39999 12.3999 5.39999C8.53391 5.39999 5.3999 8.534 5.3999 12.4C5.3999 16.266 8.53391 19.4 12.3999 19.4Z"
            />
            <path
                fillRule="evenodd"
                clipRule="evenodd"
                stroke="white"
                strokeWidth={1.4}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12.3975 10.3475C11.6977 9.52943 10.5308 9.30937 9.65405 10.0585C8.77728 10.8076 8.65384 12.0601 9.34237 12.9461C9.78338 13.5136 10.9128 14.566 11.6679 15.2492C11.9188 15.4763 12.0442 15.5898 12.1945 15.6354C12.3237 15.6745 12.4713 15.6745 12.6005 15.6354C12.7508 15.5898 12.8762 15.4763 13.1271 15.2492C13.8822 14.566 15.0116 13.5136 15.4526 12.9461C16.1412 12.0601 16.0328 10.7997 15.141 10.0585C14.2491 9.31725 13.0973 9.52943 12.3975 10.3475Z"
            />
        </svg>
    );
}

function SVGCommonGuardrail(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 13"
            width={props.size ?? 13}
            height={props.size ?? 13}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.16006 11.76C9.25285 11.76 11.7601 9.25279 11.7601 6.16C11.7601 3.0672 9.25285 0.559998 6.16006 0.559998C3.06726 0.559998 0.560059 3.0672 0.560059 6.16C0.560059 9.25279 3.06726 11.76 6.16006 11.76Z"
            />
            <path
                fillRule="evenodd"
                clipRule="evenodd"
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.15814 4.51803C5.59832 3.86355 4.66479 3.6875 3.96337 4.2868C3.26196 4.8861 3.16321 5.88811 3.71403 6.59691C4.06684 7.0509 4.97039 7.89277 5.57443 8.4394C5.77516 8.62105 5.87553 8.71188 5.99575 8.7483C6.09909 8.77962 6.21719 8.77962 6.32054 8.7483C6.44075 8.71188 6.54112 8.62105 6.74185 8.4394C7.3459 7.89277 8.24944 7.0509 8.60225 6.59691C9.15307 5.88811 9.06638 4.8798 8.35291 4.2868C7.63944 3.6938 6.71796 3.86355 6.15814 4.51803Z"
            />
        </svg>
    );
}

export default function SVGGuardrail(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryGuardrail {...rest} />; }
    return <SVGCommonGuardrail {...rest} />;
}
