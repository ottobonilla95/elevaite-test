import type { SVGProps, JSX } from "react";


function SVGCategoryPrompt(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                d="M9.6001 10.65H12.4001M9.6001 13.1H14.5001M12.4001 18.7C15.8795 18.7 18.7001 15.8794 18.7001 12.4C18.7001 8.92061 15.8795 6.10001 12.4001 6.10001C8.9207 6.10001 6.1001 8.92061 6.1001 12.4C6.1001 13.238 6.26371 14.0378 6.56074 14.7692C6.61759 14.9091 6.64601 14.9791 6.65869 15.0357C6.6711 15.091 6.67564 15.132 6.67564 15.1887C6.67565 15.2467 6.66512 15.3098 6.64407 15.4362L6.22899 17.9267C6.18552 18.1875 6.16379 18.3179 6.20423 18.4122C6.23963 18.4947 6.3054 18.5605 6.38793 18.5959C6.48222 18.6363 6.61263 18.6146 6.87343 18.5711L9.36395 18.156C9.49026 18.135 9.55341 18.1245 9.61139 18.1245C9.66811 18.1245 9.70906 18.129 9.7644 18.1414C9.82098 18.1541 9.89097 18.1825 10.0309 18.2394C10.7623 18.5364 11.5621 18.7 12.4001 18.7Z"
            />
        </svg>
    );
}

function SVGCommonPrompt(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 13 10"
            width={props.size ? props.size * (13 / 10) : 13}
            height={props.size ?? 10}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.71643 3.65925H6.12961M3.71643 5.25269H7.9395M6.12961 8.89484C9.12833 8.89484 11.5593 7.06036 11.5593 4.79742C11.5593 2.53449 9.12833 0.700012 6.12961 0.700012C3.13089 0.700012 0.699951 2.53449 0.699951 4.79742C0.699951 5.34245 0.840963 5.86261 1.09696 6.33828C1.14595 6.42932 1.17045 6.47484 1.18138 6.51164C1.19207 6.54763 1.19598 6.57427 1.19598 6.61115C1.19599 6.64886 1.18692 6.68993 1.16878 6.77208L0.811034 8.39187C0.773572 8.5615 0.75484 8.64631 0.789698 8.70764C0.820206 8.76131 0.876887 8.80409 0.948017 8.82711C1.02929 8.85341 1.14167 8.83928 1.36645 8.81101L3.51291 8.54104C3.62176 8.52735 3.67619 8.52051 3.72616 8.52051C3.77504 8.52052 3.81034 8.52347 3.85803 8.53153C3.90679 8.53978 3.96711 8.55827 4.08775 8.59524C4.71808 8.78842 5.40738 8.89484 6.12961 8.89484Z"
            />
        </svg>
    );
}

export default function SVGPrompt(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryPrompt {...rest} />; }
    return <SVGCommonPrompt {...rest} />;
}
