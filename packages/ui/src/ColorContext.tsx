"use client";
import { createContext } from "react";

interface ColorScheme {
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
}

export const ColorContext = createContext<ColorScheme>({});

export const EngineerTheme: ColorScheme = {
  primary: "#282828",
  secondary: "#424242",
  tertiary: "#4e332a",
  highlight: "#e75f33",
  text: "#FFFFFF",
  secondaryText: "#c3c3c3",
  icon: "#93939380",
  hoverColor: "#363636",
  borderColor: "#FFFFFF1F",
  iconBorder: "#282828",
};

export const AppDrawerTheme: ColorScheme = {
  primary: "#FFFFFF",
  secondary: "#F1F5F9",
  tertiary: "#E75F3333",
  highlight: "#e75f33",
  text: "#0F172A",
  secondaryText: "#c3c3c3",
  icon: "#64748B",
  hoverColor: "#444",
  borderColor: "#EBEBEB",
  iconBorder: "#64748B",
};
