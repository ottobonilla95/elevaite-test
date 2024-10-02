import type { SVGProps } from "react"


function SVGZoomOut(props: SVGProps<SVGSVGElement> & { color: string, size?: number }): JSX.Element {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 212 212"
            height={props.size ? props.size : 24}
            width={props.size ? props.size : 24}
            fill="none"
            {...props}
        >
            <path
                fill={props.color}
                fillRule="evenodd"
                d="M86.599 153.953c37.199 0 67.354-30.155 67.354-67.354 0-37.2-30.155-67.355-67.354-67.355-37.2 0-67.355 30.156-67.355 67.355 0 37.199 30.156 67.354 67.355 67.354Zm0 19.244c20.447 0 39.239-7.085 54.053-18.938l54.607 54.609c3.758 3.757 9.851 3.757 13.609 0 3.757-3.758 3.757-9.851 0-13.609l-54.609-54.607c11.853-14.814 18.938-33.606 18.938-54.053C173.197 38.772 134.426 0 86.599 0S0 38.772 0 86.599c0 47.827 38.772 86.598 86.599 86.598ZM52.92 76.977c-5.314 0-9.622 4.308-9.622 9.622s4.308 9.622 9.622 9.622h67.355c5.314 0 9.622-4.308 9.622-9.622s-4.308-9.622-9.622-9.622H52.921Z"
                clipRule="evenodd"
            />
        </svg>
    );
}

function SVGZoomIn(props: SVGProps<SVGSVGElement> & { color: string, size?: number }): JSX.Element {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 212 212"
            height={props.size ? props.size : 24}
            width={props.size ? props.size : 24}
            fill="none"
            {...props}
        >
            <path
                fill={props.color}
                fillRule="evenodd"
                d="M153.953 86.599c0 37.199-30.155 67.354-67.354 67.354-37.2 0-67.355-30.155-67.355-67.354 0-37.2 30.156-67.355 67.355-67.355 37.199 0 67.354 30.156 67.354 67.355Zm-13.301 67.66c-14.814 11.853-33.606 18.938-54.053 18.938C38.772 173.197 0 134.426 0 86.599S38.772 0 86.599 0c47.827 0 86.598 38.772 86.598 86.599 0 20.447-7.085 39.239-18.938 54.053l54.609 54.607c3.757 3.758 3.757 9.851 0 13.609-3.758 3.757-9.851 3.757-13.609 0l-54.607-54.609Zm-97.353-67.66c0-5.314 4.308-9.622 9.622-9.622h24.056V52.92c0-5.314 4.308-9.622 9.622-9.622s9.622 4.308 9.622 9.622v24.056h24.055c5.314 0 9.622 4.308 9.622 9.622s-4.308 9.622-9.622 9.622H96.221v24.055c0 5.314-4.308 9.622-9.622 9.622s-9.622-4.308-9.622-9.622V96.221H52.92c-5.314 0-9.622-4.308-9.622-9.622Z"
                clipRule="evenodd"
            />
        </svg>
    );
}



function SVGZoom(props: SVGProps<SVGSVGElement> & {type?: "in" | "out", size?: number}): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;


    switch(props.type) {
        case "out": return <SVGZoomOut color={mainColor} size={props.size} />;
        default: return <SVGZoomIn color={mainColor} size={props.size} />;
    }
}
 
export default SVGZoom;
