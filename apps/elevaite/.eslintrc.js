module.exports = {
  extends: ["@repo/eslint-config/next.js"],
  overrides: [
    {
      files: ['*.ts', "*.tsx"],
      rules: {
        'no-undef': 'off'
      }
    }
  ]
};
