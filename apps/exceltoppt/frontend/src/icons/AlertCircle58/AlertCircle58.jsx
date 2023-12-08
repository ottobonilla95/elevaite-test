/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import PropTypes from "prop-types";
import React from "react";

export const AlertCircle58 = ({ color = "white", className }) => {
  return (
    <svg
      className={`alert-circle-58 ${className}`}
      fill="none"
      height="20"
      viewBox="0 0 20 20"
      width="20"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g className="g" clipPath="url(#clip0_2_2013)">
        <path
          className="path"
          d="M10 6.66669V10M10 13.3334H10.0083M18.3333 10C18.3333 14.6024 14.6024 18.3334 10 18.3334C5.39762 18.3334 1.66666 14.6024 1.66666 10C1.66666 5.39765 5.39762 1.66669 10 1.66669C14.6024 1.66669 18.3333 5.39765 18.3333 10Z"
          stroke={color}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.66667"
        />
      </g>
      <defs className="defs">
        <clipPath className="clip-path" id="clip0_2_2013">
          <rect className="rect" fill="white" height="20" width="20" />
        </clipPath>
      </defs>
    </svg>
  );
};

AlertCircle58.propTypes = {
  color: PropTypes.string,
};
