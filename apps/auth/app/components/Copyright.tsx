import type { JSX } from "react";

export function Copyright(): JSX.Element {
  return (
    <p className="copyright">
      Copyright 2023 -{" "}
      <a
        href="https://www.iopex.com/"
        target="_blank"
        rel="noopener noreferrer"
      >
        iOPEX Technologies
      </a>
    </p>
  );
}
