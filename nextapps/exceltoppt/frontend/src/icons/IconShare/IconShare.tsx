/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import PropTypes from "prop-types";
import React from "react";

interface Props {
  color: string;
  className: any;
}

export const IconShare = ({ color = "#686A70", className }: Props): JSX.Element => {
  return (
    <svg
      className={`icon-share ${className}`}
      fill="none"
      height="22"
      viewBox="0 0 22 22"
      width="22"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        className="path"
        d="M14.8325 7.17463L9.10904 12.9592L2.59944 8.88767C1.66675 8.30414 1.86077 6.88744 2.91572 6.57893L18.3712 2.05277C19.3373 1.76963 20.2326 2.67283 19.9456 3.642L15.3731 19.0868C15.0598 20.1432 13.6512 20.332 13.0732 19.3953L9.10601 12.9602"
        stroke={color}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
};

IconShare.propTypes = {
  color: PropTypes.string,
};
