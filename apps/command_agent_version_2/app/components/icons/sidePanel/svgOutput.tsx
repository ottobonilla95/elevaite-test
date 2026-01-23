import type { SVGProps, JSX } from "react";


function SVGCategoryOutput(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
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
                strokeWidth={1.6}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.2001 15.8999L18.7001 12.3999M18.7001 12.3999L15.2001 8.89992M18.7001 12.3999H10.3001M12.4001 15.8999C12.4001 16.1068 12.4001 16.2103 12.3924 16.2999C12.3125 17.2313 11.6265 17.9977 10.7096 18.18C10.6214 18.1976 10.5185 18.209 10.3129 18.2318L9.59796 18.3113C8.52383 18.4306 7.98674 18.4903 7.56006 18.3538C6.99115 18.1717 6.52669 17.756 6.28292 17.2107C6.1001 16.8017 6.1001 16.2613 6.1001 15.1805V9.61931C6.1001 8.53856 6.1001 7.99818 6.28292 7.58918C6.52669 7.04386 6.99115 6.62814 7.56006 6.44609C7.98675 6.30955 8.52382 6.36922 9.59796 6.48857L10.3129 6.56802C10.5186 6.59086 10.6214 6.60229 10.7096 6.61983C11.6265 6.80213 12.3125 7.56855 12.3924 8.49995C12.4001 8.58956 12.4001 8.69302 12.4001 8.89992"
            />
        </svg>
    );
}

function SVGCommonOutput(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 9 9"
            width={props.size ?? 9}
            height={props.size ?? 9}
            fill="none"
            {...props}
        >
            <path
                stroke={mainColor}
                strokeWidth={0.96}
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5.91571 6.33391L8.00638 4.24324M8.00638 4.24324L5.91571 2.15257M8.00638 4.24324H2.98878M4.24318 6.33391C4.24318 6.72276 4.24318 6.91719 4.20044 7.0767C4.08445 7.50959 3.74633 7.84771 3.31344 7.9637C3.15393 8.00644 2.9595 8.00644 2.57065 8.00644H2.36158C1.7771 8.00644 1.48486 8.00644 1.25434 7.91096C0.946979 7.78364 0.70278 7.53944 0.575466 7.23208C0.47998 7.00156 0.47998 6.70932 0.47998 6.12484V2.36164C0.47998 1.77716 0.47998 1.48493 0.575466 1.2544C0.70278 0.94704 0.94698 0.702841 1.25434 0.575527C1.48487 0.480042 1.7771 0.480042 2.36158 0.480042H2.57065C2.9595 0.480042 3.15393 0.480042 3.31344 0.522784C3.74633 0.638775 4.08445 0.976895 4.20044 1.40978C4.24318 1.5693 4.24318 1.76372 4.24318 2.15257"
            />
        </svg>
    );
}

export default function SVGOutput(props: SVGProps<SVGSVGElement> & { size?: number; isCategory?: boolean }): JSX.Element {
    const { isCategory, ...rest } = props;

    if (isCategory) { return <SVGCategoryOutput {...rest} />; }
    return <SVGCommonOutput {...rest} />;
}
