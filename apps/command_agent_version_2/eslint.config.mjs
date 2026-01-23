import { defineConfig } from "eslint/config";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default defineConfig([{
    extends: [...compat.extends("@repo/eslint-config/next.js")],

    rules: {
        "no-alert": "warn",
        "@typescript-eslint/no-floating-promises": "warn",
        "@typescript-eslint/no-confusing-void-expression": "warn",
        "@typescript-eslint/explicit-function-return-type": "warn",
        "@typescript-eslint/no-unused-vars": "warn",
        "@typescript-eslint/no-shadow": "warn",
        "jsx-a11y/click-events-have-key-events": "warn",
        "jsx-a11y/no-static-element-interactions": "warn",
        "@typescript-eslint/prefer-nullish-coalescing": "off",
    },
}]);