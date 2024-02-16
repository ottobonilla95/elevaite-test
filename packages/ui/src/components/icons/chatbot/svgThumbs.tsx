import type { SVGProps } from "react"



function ThumbsUp({mainColor, ...props}: SVGProps<SVGSVGElement> & { mainColor: string, size?: number }): JSX.Element {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 15 16"
            width={props.size ? props.size : 15}
            height={props.size ? props.size * (16/15) : 16}
            fill="none"
            {...props}
        >
            <path
                fill={mainColor}
                d="M7.69.666c-.48 0-.914.283-1.11.721L4.34 6.428a4.55 4.55 0 0 1-.106.23l-.002.004h-.004c-.05.004-.12.004-.253.004h-.533c-.351 0-.654 0-.904.02-.264.022-.526.07-.778.198a2 2 0 0 0-.874.874 2.036 2.036 0 0 0-.198.778c-.02.25-.02.553-.02.904v3.118c0 .352 0 .655.02.905.022.263.07.525.198.778a2 2 0 0 0 .874.874c.252.128.514.176.778.197.25.02.553.02.904.02a.56.56 0 0 0 .56-.558V9.333a.667.667 0 0 1 1.333 0v4.933c0 .373 0 .56.072.703a.667.667 0 0 0 .292.291c.142.073.329.073.702.073h4.213c.466 0 .853 0 1.171-.024.332-.026.639-.08.934-.214.463-.21.856-.547 1.133-.972.178-.272.278-.566.353-.89.073-.312.131-.694.202-1.154l.357-2.321c.094-.61.171-1.11.198-1.518.028-.421.01-.814-.134-1.191a2.666 2.666 0 0 0-1.173-1.368c-.35-.199-.736-.277-1.156-.313-.408-.035-.914-.035-1.531-.035H10.4c-.197 0-.306 0-.383-.007h-.01v-.01a5.42 5.42 0 0 1-.007-.383V2.977A2.31 2.31 0 0 0 7.691.666Z"
            />
        </svg>
    );
}

function ThumbsDown({mainColor, ...props}: SVGProps<SVGSVGElement> & { mainColor: string, size?: number }): JSX.Element {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 15 16"
            width={props.size ? props.size : 15}
            height={props.size ? props.size * (16/15) : 16}
            fill="none"
            {...props}
        >
            <path
                fill={mainColor}
                d="M7.69 15.334c-.48 0-.914-.283-1.11-.721L4.34 9.572a4.55 4.55 0 0 0-.106-.23l-.002-.004h-.004a4.547 4.547 0 0 0-.253-.004h-.533c-.351 0-.654 0-.904-.02a2.036 2.036 0 0 1-.778-.198 2 2 0 0 1-.874-.874 2.036 2.036 0 0 1-.198-.778c-.02-.25-.02-.553-.02-.904V3.442c0-.352 0-.655.02-.905.022-.263.07-.525.198-.778A2 2 0 0 1 1.76.885c.252-.128.514-.176.778-.197.25-.02.553-.02.904-.02.309 0 .56.25.56.558v5.441a.667.667 0 0 0 1.333 0V1.734c0-.373 0-.56.072-.703A.667.667 0 0 1 5.7.74C5.84.667 6.028.667 6.4.667h4.213c.466 0 .853 0 1.171.025.332.025.639.08.934.213.463.21.856.547 1.133.972.178.272.278.566.353.89.073.312.131.694.202 1.154l.357 2.321c.094.61.171 1.11.198 1.518.028.421.01.814-.134 1.191a2.667 2.667 0 0 1-1.173 1.368c-.35.199-.736.277-1.156.313-.408.035-.914.035-1.531.035H10.4c-.197 0-.306 0-.383.007l-.01.001v.009a5.423 5.423 0 0 0-.007.383v1.956a2.31 2.31 0 0 1-2.31 2.311Z"
            />
         </svg>
    );
}

function SVGThumbs(props: SVGProps<SVGSVGElement> & { size?: number, type?: "up" | "down"}): JSX.Element {
    let mainColor = "currentColor";
    if (props.color) mainColor = props.color;


    switch(props.type) {
        case "up": return <ThumbsUp mainColor={mainColor} />;
        case "down": return <ThumbsDown mainColor={mainColor} />;
        default: return <ThumbsUp mainColor={mainColor} />;
    }
}
     
export default SVGThumbs;
