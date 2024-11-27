import type { Config } from "tailwindcss";
import sharedConfig from "@repo/tailwind-config";

const config: Pick<Config, "prefix" | "presets" | "content"> = {
  content: [
    // app content
    `src/**/*.{js,ts,jsx,tsx}`,
    // include packages if not transpiling
    "../../packages/contracts-ui/src/**/*.{js,ts,jsx,tsx}",
  ],
  prefix: "ui-",
  presets: [sharedConfig],
};

export default config;
