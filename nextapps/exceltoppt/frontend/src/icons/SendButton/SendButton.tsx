/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import React from "react";

interface Props {
  className: any;
}

export const SendButton = ({ className }: Props): JSX.Element => {
  return (
    <svg
      className={`send-button ${className}`}
      fill="none"
      height="40"
      viewBox="0 0 40 40"
      width="40"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect className="rect" fill="#F46F22" height="40" rx="6" width="40" />
      <path
        className="path"
        d="M23.8325 16.1746L18.109 21.9592L11.5994 17.8877C10.6668 17.3041 10.8608 15.8874 11.9157 15.5789L27.3712 11.0528C28.3373 10.7696 29.2326 11.6728 28.9456 12.642L24.3731 28.0868C24.0598 29.1432 22.6512 29.332 22.0732 28.3953L18.106 21.9602"
        stroke="white"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
};
