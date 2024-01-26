import Link from "next/link";
import React from "react";
import "./Breadcrumbs.scss";

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export interface BreadcrumbItem {
  label: string;
  link?: string;
}

export function Breadcrumbs({ ...props }: BreadcrumbsProps): JSX.Element {
  return (
    <div className="breadcrumbs">
      {/* <svg
        color={colors.text}
        fill="none"
        height="20"
        viewBox="0 0 20 20"
        width="20"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          clipRule="evenodd"
          d="M6.67179 2.33524C6.68175 2.34189 6.69175 2.34855 6.70177 2.35523L15.4924 8.21564C15.7467 8.38518 15.9826 8.54237 16.1637 8.68844C16.3527 8.84089 16.5756 9.05228 16.7038 9.36154C16.8733 9.77029 16.8733 10.2297 16.7038 10.6384C16.5756 10.9477 16.3527 11.1591 16.1637 11.3115C15.9826 11.4576 15.7468 11.6148 15.4924 11.7843L6.67182 17.6647C6.36091 17.872 6.08135 18.0584 5.84413 18.187C5.60674 18.3156 5.2809 18.4626 4.90059 18.4399C4.41412 18.4109 3.96475 18.1704 3.67074 17.7817C3.44089 17.4779 3.38246 17.1252 3.35782 16.8563C3.33321 16.5877 3.33323 16.2517 3.33325 15.878L3.33326 4.15801C3.33326 4.14596 3.33325 4.13395 3.33325 4.12197C3.33323 3.74831 3.33321 3.41231 3.35782 3.14363C3.38246 2.87475 3.44089 2.52208 3.67074 2.21824C3.96475 1.82959 4.41412 1.58909 4.90059 1.56005C5.2809 1.53734 5.60674 1.68435 5.84413 1.813C6.08134 1.94155 6.3609 2.12795 6.67179 2.33524Z"
          fill="currentColor"
          fillRule="evenodd"
        />
      </svg> */}
      {props.items.map((item, index) => (
        <React.Fragment key={item.label}>
          {item.link ? (
            <Link className="breadcrumbItem" href={item.link}>
              <span>{item.label}</span>
            </Link>
          ) : (
            <span>{item.label}</span>
          )}
          {index === props.items.length - 1 ? undefined : <div className="separator">|</div>}
        </React.Fragment>
      ))}
    </div>
  );
}
