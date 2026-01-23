import type { SVGProps, JSX } from "react";


function SVGCategoryCondition(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M6.1001 6.10004V13.24C6.1001 14.4161 6.1001 15.0042 6.32898 15.4534C6.53032 15.8486 6.85158 16.1698 7.24672 16.3712C7.69593 16.6 8.28399 16.6 9.4601 16.6H14.5001M14.5001 16.6C14.5001 17.7598 15.4403 18.7 16.6001 18.7C17.7599 18.7 18.7001 17.7598 18.7001 16.6C18.7001 15.4402 17.7599 14.5 16.6001 14.5C15.4403 14.5 14.5001 15.4402 14.5001 16.6ZM6.1001 9.60004L14.5001 9.60004M14.5001 9.60004C14.5001 10.7598 15.4403 11.7 16.6001 11.7C17.7599 11.7 18.7001 10.7598 18.7001 9.60004C18.7001 8.44024 17.7599 7.50004 16.6001 7.50004C15.4403 7.50004 14.5001 8.44024 14.5001 9.60004Z"
            />
        </svg>
    );
}

function SVGCommonCondition(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M0.560059 0.559998V6.71361C0.560059 7.72724 0.560059 8.23406 0.757324 8.62121C0.930844 8.96177 1.20772 9.23864 1.54827 9.41216C1.93543 9.60943 2.44225 9.60943 3.45588 9.60943H7.7996M7.7996 9.60943C7.7996 10.609 8.60992 11.4193 9.60949 11.4193C10.6091 11.4193 11.4194 10.609 11.4194 9.60943C11.4194 8.60986 10.6091 7.79954 9.60949 7.79954C8.60992 7.79954 7.7996 8.60986 7.7996 9.60943ZM0.560059 3.57647L7.7996 3.57648M7.7996 3.57648C7.7996 4.57605 8.60992 5.38636 9.60949 5.38636C10.6091 5.38636 11.4194 4.57605 11.4194 3.57647C11.4194 2.5769 10.6091 1.76659 9.60949 1.76659C8.60992 1.76659 7.7996 2.5769 7.7996 3.57648Z"
            />
        </svg>
    );
}

export default function SVGCondition(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryCondition {...rest} />; }
    return <SVGCommonCondition {...rest} />;
}
