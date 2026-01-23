import type { SVGProps } from "react";

/**
 * React 19 compatible SVG component props.
 * React 19 changed the ref types in SVGProps, making string refs incompatible.
 * This type omits the ref prop to avoid type conflicts when spreading props.
 */
export type SVGComponentProps<T extends SVGElement = SVGSVGElement> = Omit<
  SVGProps<T>,
  "ref"
>;

