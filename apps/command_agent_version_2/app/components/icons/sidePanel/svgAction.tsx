import type { SVGProps, JSX } from "react";


function SVGCategoryAction(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
            <g clipPath="url(#clip0_49_1455)">
                <path
                    stroke="white"
                    strokeWidth={1.4}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.3994 5.79669L7.16479 13.2782C6.92062 13.5712 6.79854 13.7177 6.79667 13.8414C6.79505 13.949 6.84298 14.0513 6.92665 14.1189C7.02289 14.1967 7.21359 14.1967 7.59499 14.1967H12.6994L11.9994 19.7967L18.2339 12.3152C18.4781 12.0222 18.6002 11.8757 18.6021 11.752C18.6037 11.6444 18.5558 11.5421 18.4721 11.4745C18.3758 11.3967 18.1851 11.3967 17.8037 11.3967H12.6994L13.3994 5.79669Z"
                />
            </g>
            <defs>
                <clipPath id="clip0_49_1455">
                    <rect width="17.2066" height="17.2066" fill="white" transform="translate(3.79663 3.79669)" />
                </clipPath>
            </defs>
        </svg>
    );
}

function SVGCommonAction(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 11"
            width={props.size ? props.size * (12 / 11) : 12}
            height={props.size ?? 11}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.11615 0.560013L0.869854 5.31086C0.664393 5.49692 0.561662 5.58995 0.560092 5.66851C0.558727 5.73682 0.599059 5.8018 0.669464 5.84473C0.750452 5.89412 0.910922 5.89412 1.23186 5.89412H5.52711L4.93807 9.45019L10.1844 4.69934C10.3898 4.51329 10.4926 4.42026 10.4941 4.34169C10.4955 4.27339 10.4552 4.20841 10.3848 4.16547C10.3038 4.11608 10.1433 4.11608 9.82236 4.11608H5.52711L6.11615 0.560013Z"
            />
        </svg>
    );
}

export default function SVGAction(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryAction {...rest} />; }
    return <SVGCommonAction {...rest} />;
}
