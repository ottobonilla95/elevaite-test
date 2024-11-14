module.exports = {
  extends: ["@repo/eslint-config/react.js"],
  parserOptions: {
    project: "tsconfig.json",
    tsconfigRootDir: __dirname,
    sourceType: "module",
  },
  rules: {
    "no-nested-ternary": "off",
    "@typescript-eslint/prefer-nullish-coalescing": "off",
  }
};
