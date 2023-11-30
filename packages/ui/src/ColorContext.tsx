"use client";
import { createContext } from "react";

export interface ColorScheme {
  primary?: string;
  secondary?: string;
  tertiary?: string;
  highlight?: string;
  text?: string;
  secondaryText?: string;
  icon?: string;
  iconBorder?: string;
  hoverColor?: string;
  borderColor?: string;
  background?: string;
}

export const ColorContext = createContext<ColorScheme>({});
