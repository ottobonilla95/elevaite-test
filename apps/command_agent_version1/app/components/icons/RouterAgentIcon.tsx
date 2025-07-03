import type { SVGProps } from "react";

interface RouterAgentIconProps extends SVGProps<SVGSVGElement> {
	size?: number;
}

function RouterAgentIcon({ size = 22, ...props }: RouterAgentIconProps): JSX.Element {
	return (
		<svg 
			width={size} 
			height={size} 
			viewBox="0 0 22 22" 
			fill="none" 
			xmlns="http://www.w3.org/2000/svg"
			{...props}
		>
			<path 
				d="M1.25879 15.3295V6.67058C1.25879 3.68174 3.68174 1.25879 6.67058 1.25879H15.3295C18.3183 1.25879 20.7412 3.68174 20.7412 6.67058V15.3295C20.7412 18.3183 18.3183 20.7412 15.3295 20.7412H6.67058C3.68174 20.7412 1.25879 18.3183 1.25879 15.3295Z" 
				stroke="#FE854B" 
				strokeWidth="1.62354" 
			/>
			<path 
				d="M15.8706 13.7061C15.8706 13.7061 14.2471 15.8708 11 15.8708C7.75293 15.8708 6.12939 13.7061 6.12939 13.7061" 
				stroke="#FE854B" 
				strokeWidth="1.62354" 
				strokeLinecap="round" 
				strokeLinejoin="round" 
			/>
			<path 
				d="M7.21159 8.83529C6.91271 8.83529 6.67041 8.59299 6.67041 8.29411C6.67041 7.99523 6.91271 7.75293 7.21159 7.75293C7.51047 7.75293 7.75277 7.99523 7.75277 8.29411C7.75277 8.59299 7.51047 8.83529 7.21159 8.83529Z" 
				fill="#FE854B" 
				stroke="#FE854B" 
				strokeWidth="1.62354" 
				strokeLinecap="round" 
				strokeLinejoin="round" 
			/>
			<path 
				d="M14.7882 8.83529C14.4894 8.83529 14.2471 8.59299 14.2471 8.29411C14.2471 7.99523 14.4894 7.75293 14.7882 7.75293C15.0871 7.75293 15.3294 7.99523 15.3294 8.29411C15.3294 8.59299 15.0871 8.83529 14.7882 8.83529Z" 
				fill="#FE854B" 
				stroke="#FE854B" 
				strokeWidth="1.62354" 
				strokeLinecap="round" 
				strokeLinejoin="round" 
			/>
		</svg>
	);
}

export default RouterAgentIcon;
