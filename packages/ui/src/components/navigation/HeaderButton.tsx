"use client";
import type { JSX } from "react";
import React from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

interface HeaderButtonProps {
  label: string;
  link: string;
}

export function HeaderButton({ label, link }: HeaderButtonProps): JSX.Element {
  const pathname = usePathname();
  return (
    <Link
      className={`ui-flex ui-py-2 ui-px-4 ui-rounded ui-items-center ui-line-clamp-1 ui-text-white hover:ui-bg-[#F46F22] ${
        pathname.startsWith(link) ? "ui-bg-[#F46F22]" : "ui-bg-black"
      }`}
      href={link}
    >
      {label}
    </Link>
  );
}
