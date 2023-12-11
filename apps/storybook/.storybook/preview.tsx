import React from "react";
import type { Preview } from "@storybook/react";
import { withThemeByClassName } from "@storybook/addon-themes";
import { ColorContext, ColorScheme } from "@repo/ui/components";
import "../app/globals.css";
import "tailwindcss/tailwind.css";
import "@repo/ui/styles.css";

export const AppDrawerTheme: ColorScheme = {
  primary: "#FFFFFF",
  secondary: "#F1F5F9",
  tertiary: "#E75F3333",
  highlight: "#e75f33",
  text: "#0F172A",
  secondaryText: "#c3c3c3",
  icon: "#64748B",
  hoverColor: "#444",
  borderColor: "#CBD5E1",
  iconBorder: "#64748B",
  background: "#F9FAFB",
};

const preview: Preview = {
  decorators: [
    (Story) => (
      <ColorContext.Provider value={AppDrawerTheme}>
        <Story />
      </ColorContext.Provider>
    ),
  ],
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
export const decorators = [
  withThemeByClassName({
    themes: {
      light: "light",
      dark: "dark",
    },
    defaultTheme: "light",
  }),
];
