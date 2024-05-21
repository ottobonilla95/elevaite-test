

export interface ColorScheme {
  type?: "dark" | "light";
  primary?: string;
  secondary?: string;
  tertiary?: string;
  highlight?: string;
  text?: string;
  secondaryText?: string;
  tertiaryText?: string;
  icon?: string;
  iconBorder?: string;
  hoverColor?: string;
  borderColor?: string;
  background?: string;
  backgroundSecondary?: string;
  backgroundHighContrast?: string;
  navbarLogo?: string,
  navbarBackground?: string,
  success?: string,
  danger?: string,
  tagBorder?: string,
}


// Dark
export const DarkTheme: ColorScheme = {
  type: "dark",
  primary: "#282828",
  secondary: "#424242",
  tertiary: "#4e332a",
  highlight: "#e75f33",
  text: "#FFFFFF",
  secondaryText: "#808080",
  tertiaryText: "#A3A3A3",
  icon: "#93939380",
  hoverColor: "#363636",
  borderColor: "#FFFFFF1F",
  iconBorder: "#282828",
  background: "#161616",
  backgroundHighContrast: "#000000",
  navbarLogo: "#FFFFFF",
  navbarBackground: "#282828",
  success: "#D8FC77",
  danger: "#DC143C",
  tagBorder: "#71570D",
};

// Light
export const LightTheme: ColorScheme = {
  type: "light",
  primary: "#FFFFFF",
  secondary: "#F1F5F9",
  tertiary: "#E75F3333",
  highlight: "#e75f33",
  text: "#0F172A",
  secondaryText: "#c3c3c3",
  tertiaryText: "#A3A3A3",
  icon: "#64748B",
  hoverColor: "#f5f5f5",
  borderColor: "#CBD5E1",
  iconBorder: "#64748B",
  background: "#F9FAFB",
  backgroundHighContrast: "#FFFFFF",
  navbarLogo: "#0F172A",
  navbarBackground: "#CBD5E1",
  success: "#D8FC77",
  danger: "#DC143C",
  tagBorder: "#71570D",
};
