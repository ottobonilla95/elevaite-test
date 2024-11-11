module.exports = {
  extends: ["@repo/eslint-config/react.js"],
  rules: {
    "@typescript-eslint/naming-convention": "off",
    // FIXME Remove on prod ?
    "@typescript-eslint/no-unsafe-member-access": "off",
    "@typescript-eslint/no-unsafe-assignment": "off",
    "@typescript-eslint/no-unsafe-call": "off",
    "@typescript-eslint/no-unsafe-argument": "off",
    "@typescript-eslint/no-unsafe-return": "off",
    "@typescript-eslint/restrict-template-expressions": "off",
    //
    "no-nested-ternary": "off",
  },
};
