import type { SVGProps, JSX } from "react";


function SVGCategoryKnowledgeBase(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth={1.2}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M18.7001 7.50002C18.7001 8.65982 15.8795 9.60002 12.4001 9.60002C8.9207 9.60002 6.1001 8.65982 6.1001 7.50002M18.7001 7.50002C18.7001 6.34023 15.8795 5.40002 12.4001 5.40002C8.9207 5.40002 6.1001 6.34023 6.1001 7.50002M18.7001 7.50002V17.3C18.7001 18.462 15.9001 19.4 12.4001 19.4C8.9001 19.4 6.1001 18.462 6.1001 17.3V7.50002M18.7001 10.8042C18.7001 11.9662 15.9001 12.9042 12.4001 12.9042C8.9001 12.9042 6.1001 11.9662 6.1001 10.8042M18.7001 14.108C18.7001 15.27 15.9001 16.208 12.4001 16.208C8.9001 16.208 6.1001 15.27 6.1001 14.108"
            />
        </svg>
    );
}

function SVGCommonKnowledgeBase(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 12 14"
            width={props.size ? props.size * (12 / 14) : 12}
            height={props.size ?? 14}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={1.12}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.4194 2.36988C11.4194 3.36946 8.98844 4.17977 5.98972 4.17977C2.991 4.17977 0.560059 3.36946 0.560059 2.36988M11.4194 2.36988C11.4194 1.37031 8.98844 0.559998 5.98972 0.559998C2.991 0.559998 0.560059 1.37031 0.560059 2.36988M11.4194 2.36988V10.816C11.4194 11.8175 9.00619 12.6259 5.98972 12.6259C2.97324 12.6259 0.560059 11.8175 0.560059 10.816V2.36988M11.4194 5.21757C11.4194 6.21904 9.00619 7.02745 5.98972 7.02745C2.97324 7.02745 0.560059 6.21904 0.560059 5.21757M11.4194 8.06499C11.4194 9.06646 9.00619 9.87488 5.98972 9.87488C2.97324 9.87488 0.560059 9.06646 0.560059 8.06499"
            />
        </svg>
    );
}

export default function SVGKnowledgeBase(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryKnowledgeBase {...rest} />; }
    return <SVGCommonKnowledgeBase {...rest} />;
}
