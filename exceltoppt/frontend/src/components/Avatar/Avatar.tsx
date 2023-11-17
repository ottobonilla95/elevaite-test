/*
We're constantly improving the code you see. 
Please share your feedback here: https://form.asana.com/?k=uvp-HPgd3_hyoXRBw1IcNg&d=1152665201300829
*/

import PropTypes from "prop-types";
import React from "react";
import { Personfilled5 } from "@/icons/Personfilled5";


interface Props {
  variant: "rounded" | "circular" | "square";
  badge: boolean;
  icon: boolean;
  image: boolean;
  darkMode: boolean;
  className: any;
  text: string;
}

export const Avatar = ({ variant, badge, icon, image, darkMode, className, text = "OP" }: Props): JSX.Element => {
  return (
    <div className={`avatar badge-${badge} image-${image} icon-${icon} ${variant} dark-mode-${darkMode} ${className}`}>
      {(badge || !image) && (
        <div className="icon">
          {!badge && icon && <Personfilled5 className="person-filled" color={darkMode ? "#121212" : "white"} />}

          {!icon && !badge && <>{text}</>}

          {badge && (
            <div className="overlap-group">
              {(!image || variant === "rounded") && (
                <div className="div">
                  {!image && (
                    <div className="OP">
                      {!icon && <>{text}</>}

                      {icon && <Personfilled5 className="person-filled" color={darkMode ? "#121212" : "white"} />}
                    </div>
                  )}
                </div>
              )}

              <div className="border">
                {(variant === "circular" || variant === "rounded" || (!image && variant === "square")) && (
                  <div className="badge" />
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

Avatar.propTypes = {
  variant: PropTypes.oneOf(["rounded", "circular", "square"]),
  badge: PropTypes.bool,
  icon: PropTypes.bool,
  image: PropTypes.bool,
  darkMode: PropTypes.bool,
  text: PropTypes.string,
};
