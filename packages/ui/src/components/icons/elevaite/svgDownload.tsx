import type { SVGProps } from "react"


function SVGDownload(props: SVGProps<SVGSVGElement> & { size?: number }): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;

    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 20 20"
            width={props.size ? props.size : 20}
            height={props.size ? props.size : 20}
            {...props}
        >
            <path
                fill={mainColor}
                d="M11 1a1 1 0 1 0-2 0v9.586L5.707 7.293a1 1 0 0 0-1.414 1.414l5 5a1 1 0 0 0 1.414 0l5-5a1 1 0 0 0-1.414-1.414L11 10.586V1Z"
            />
            <path
                fill={mainColor}
                d="M1 12a1 1 0 0 1 1 1v1.2c0 .857 0 1.439.038 1.889.035.438.1.663.18.819a2 2 0 0 0 .874.874c.156.08.38.145.819.18C4.361 18 4.943 18 5.8 18h8.4c.857 0 1.439 0 1.889-.038.438-.035.663-.1.819-.18a2 2 0 0 0 .874-.874c.08-.156.145-.38.18-.819.037-.45.038-1.032.038-1.889V13a1 1 0 1 1 2 0v1.241c0 .805 0 1.47-.044 2.01-.046.563-.145 1.08-.392 1.565a4 4 0 0 1-1.748 1.748c-.485.247-1.002.346-1.564.392-.541.044-1.206.044-2.01.044H5.758c-.805 0-1.47 0-2.01-.044-.563-.046-1.08-.145-1.565-.392a4 4 0 0 1-1.748-1.748c-.247-.485-.346-1.002-.392-1.564C0 15.71 0 15.046 0 14.242V13a1 1 0 0 1 1-1Z"
            />
        </svg>
    );
}
 
export default SVGDownload;
