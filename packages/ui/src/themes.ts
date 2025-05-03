export type ColorScheme = ColorSchemeBase & ColorSchemeUI & ColorSchemeSpecial;

interface ColorSchemeBase {
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
  success?: string;
  danger?: string;
  tagBorder?: string;
  markdownHeading?: string;
  markdownParagraph?: string;
  markdownTableBg?: string;
  markdownTableBorder?: string;
  markdownTableHeaderBg?: string;
  markdownTableHeaderBorder?: string;
}

interface ColorSchemeUI {
  uiPrimary?: string;
  uiSecondary?: string;
  uiIcon?: string;
  uiHover?: string;
  uiHighlight?: string;
  uiText?: string;
  uiTextSecondary?: string;
  uiBackground?: string;
  uiBorder?: string;
}

interface ColorSchemeSpecial {
  specialCardBorder?: string;
  specialCardBorderTop?: string;
  specialCardButtonBackground?: string;
  specialCardButtonBorder?: string;
  specialSeparator?: string;
  specialTabBackground?: string;
  specialTabHighlight?: string;
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
  success: "#D8FC77",
  danger: "#DC143C",
  tagBorder: "#71570D",
  //Markdown Colors
  markdownHeading: "#FFFFFF",
  markdownParagraph: "#e2e2e2",
  markdownTableBg: "#282828",
  markdownTableBorder: "#464646",
  markdownTableHeaderBg: "#3a3a3a",
  markdownTableHeaderBorder: "#FFFFFF1F",

  // UI colors
  uiPrimary: "#282828",
  uiSecondary: "#424242",
  uiIcon: "#93939380",
  uiHover: "#363636",
  uiHighlight: "#e75f33",
  uiText: "#FFFFFF",
  uiTextSecondary: "#808080",
  uiBackground: "#161616",
  uiBorder: "#FFFFFF1F",
  // Special cases
  specialCardBorder: "#FFFFFF1F",
  specialCardBorderTop: "#e75f33",
  specialCardButtonBackground: "#282828",
  specialCardButtonBorder: "#FFFFFF1F",
  specialSeparator: "#FFFFFF1F",
  specialTabBackground: "transparent",
  specialTabHighlight: "#e75f33",

};

// Light
export const LightTheme: ColorScheme = {
  type: "light",
  primary: "#F8FAFC",
  secondary: "F1F5F9",
  tertiary: "#E75F3333",
  highlight: "#e75f33",
  text: "#212124",
  secondaryText: "#212124",
  tertiaryText: "#212124",
  icon: "#64748B",
  hoverColor: "#f5f5f5",
  borderColor: "#E2E8ED",
  iconBorder: "#64748B",
  background: "#FFFFFF",
  backgroundHighContrast: "#FFFFFF",
  success: "#D8FC77",
  danger: "#DC143C",
  tagBorder: "#71570D",

  // Light theme
  markdownHeading: "#000000",
  markdownParagraph: "#1b2027",
  markdownTableBg: "#FFFFFF",
  markdownTableBorder: "#EEEEEE",
  markdownTableHeaderBg: "#F5F5F5",
  markdownTableHeaderBorder: "#D9D9D9",

  // Obsolete - No idea why we would have a dark bar on a bright theme.
  // UI colors -- Navigation UI is the same between the two themes.
  // uiPrimary: DarkTheme.uiPrimary,
  // uiSecondary: DarkTheme.uiSecondary,
  // uiIcon: DarkTheme.uiIcon,
  // uiHover: DarkTheme.uiHover,
  // uiHighlight: DarkTheme.uiHighlight,
  // uiText: DarkTheme.uiText,
  // uiBackground: DarkTheme.uiBackground,
  // uiBorder: DarkTheme.uiBorder,

  uiPrimary: "#FFFFFF",
  uiSecondary: "#F1F5F9",
  uiIcon: "#64748B",
  uiHover: "#f5f5f5",
  uiHighlight: "#e75f33",
  uiText: "#0F172A",
  uiTextSecondary: "#c3c3c3",
  uiBackground: "#F7F6F1",
  uiBorder: "#CBD5E1",

  // Special cases
  specialCardBorder: "transparent",
  specialCardBorderTop: "transparent",
  specialCardButtonBackground: "#e75f33",
  specialCardButtonBorder: "transparent",
  specialSeparator: "#282828",
  specialTabBackground: "#FFFFFF",
  specialTabHighlight: "#0F172A",
};