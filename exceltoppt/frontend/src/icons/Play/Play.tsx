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

export const Play = ({ color = "white", className }: Props): JSX.Element => {
  return (
    <svg
      className={`play ${className}`}
      fill="none"
      height="24"
      viewBox="0 0 24 24"
      width="24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        className="path"
        clipRule="evenodd"
        d="M8.00624 2.80231C8.0182 2.81028 8.03019 2.81828 8.04222 2.8263L18.591 9.85878C18.8962 10.0622 19.1792 10.2509 19.3965 10.4261C19.6234 10.6091 19.8908 10.8628 20.0447 11.2339C20.2481 11.7244 20.2481 12.2756 20.0447 12.7661C19.8908 13.1372 19.6234 13.3909 19.3965 13.5739C19.1792 13.7491 18.8962 13.9378 18.591 14.1412L8.00628 21.1977C7.63319 21.4464 7.29771 21.6701 7.01305 21.8244C6.72818 21.9788 6.33717 22.1552 5.8808 22.1279C5.29704 22.0931 4.75779 21.8045 4.40498 21.3381C4.12916 20.9735 4.05905 20.5503 4.02948 20.2276C3.99994 19.9052 3.99997 19.502 4 19.0536L4 4.98963C4 4.97517 4 4.96075 4 4.94638C3.99997 4.49799 3.99994 4.09479 4.02948 3.77237C4.05905 3.44971 4.12916 3.02652 4.40498 2.66191C4.75779 2.19553 5.29704 1.90693 5.8808 1.87207C6.33717 1.84482 6.72818 2.02123 7.01305 2.17561C7.2977 2.32988 7.63317 2.55356 8.00624 2.80231Z"
        fill={color}
        fillRule="evenodd"
      />
    </svg>
  );
};

Play.propTypes = {
  color: PropTypes.string,
};
