import React from "react";
import "./loading.css";

interface LoadingProps {
  color?: string;
}

export function Loading({ color, ...props }: LoadingProps) {
  return (
    <div className="dot-pulse">
      <style data-jsx>{`
        .dot-pulse {
          color: ${color ? color : "#f46f22"};
        }
      `}</style>
    </div>
  );
}
