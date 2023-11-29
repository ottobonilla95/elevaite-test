import React from "react";
import type { Preview } from "@storybook/react";
import { withThemeByClassName } from "@storybook/addon-themes";
import { ColorContext, EngineerTheme } from "@elevaite/ui";
import "../app/globals.css";
import "tailwindcss/tailwind.css";

const preview: Preview = {
  decorators: [
    (Story) => (
      <ColorContext.Provider value={EngineerTheme}>
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
