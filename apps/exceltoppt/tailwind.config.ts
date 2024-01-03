import type { Config } from "tailwindcss";
import sharedConfig from "@repo/tailwind-config";

const config: Pick<Config, "content" | "presets" | "plugins"> = {
  content: ["./app/**/*.tsx"],
  presets: [sharedConfig],
  plugins: [require("@headlessui/tailwindcss")],
};
export default config;
