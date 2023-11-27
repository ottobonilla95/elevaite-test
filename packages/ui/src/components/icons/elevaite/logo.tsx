import * as React from "react";
import { SVGProps } from "react";

// interface LogoProps

const Logo = (props: SVGProps<SVGSVGElement>) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={60} height={54} fill="none" {...props}>
    <ellipse cx={27.182} cy={35.646} fill="#011121" rx={14.536} ry={24.6} transform="rotate(-83.212 27.182 35.646)" />
    <ellipse cx={28.725} cy={31.238} fill="#595A5C" rx={14.536} ry={24.6} transform="rotate(-68.027 28.725 31.238)" />
    <ellipse cx={30.929} cy={26.83} fill="#747474" rx={14.536} ry={24.6} transform="rotate(-52.234 30.93 26.83)" />
    <path
      fill="url(#a)"
      d="M7.652 41.7c.064.192.185.36.344.478a.92.92 0 0 0 .547.181c4.65-1.748 8.546-6.61 10.564-11.152 1.753-3.945 2.833-7.385 2.833-11.443h4.318a.918.918 0 0 0 .519-.162.969.969 0 0 0 .347-.43 1.012 1.012 0 0 0-.185-1.06L19.532 7.789a.913.913 0 0 0-1.363 0l-7.406 10.323a1.012 1.012 0 0 0-.185 1.06.969.969 0 0 0 .347.43.918.918 0 0 0 .519.162h4.283c.065 2.63-.254 5.348-1.243 8.649-.989 3.3-3.776 10.026-6.522 12.198a.98.98 0 0 0-.323.493c-.056.195-.052.404.012.596h.001Z"
    />
    <g fill="#E75F33" filter="url(#b)">
      <path d="M35.46 36.339h-8.03l-1.33 3.73h-4.245l7.25-19.6h4.708l7.25 19.6H36.79l-1.329-3.73Zm-1.098-3.14-2.917-8.188-2.918 8.188h5.835ZM47.818 20.496v19.572h-4.044V20.496h4.044Z" />
    </g>
    <defs>
      <linearGradient id="a" x1={21.218} x2={-3.218} y1={13.468} y2={58.014} gradientUnits="userSpaceOnUse">
        <stop stopColor="#fff" />
        <stop offset={1} stopColor="#fff" stopOpacity={0} />
      </linearGradient>
      <filter
        id="b"
        width={33.964}
        height={27.6}
        x={17.855}
        y={20.468}
        colorInterpolationFilters="sRGB"
        filterUnits="userSpaceOnUse"
      >
        <feFlood floodOpacity={0} result="BackgroundImageFix" />
        <feColorMatrix in="SourceAlpha" result="hardAlpha" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" />
        <feOffset dy={4} />
        <feGaussianBlur stdDeviation={2} />
        <feComposite in2="hardAlpha" operator="out" />
        <feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0" />
        <feBlend in2="BackgroundImageFix" result="effect1_dropShadow_962_2" />
        <feBlend in="SourceGraphic" in2="effect1_dropShadow_962_2" result="shape" />
      </filter>
    </defs>
  </svg>
);
export default Logo;
