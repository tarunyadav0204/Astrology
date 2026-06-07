/**
 * CRA + code-splitting: different chunk graphs can produce the same CSS in different
 * order; mini-css-extract-plugin warns ("Conflicting order"). With CI=true, CRA
 * fails the build. ignoreOrder is safe here because chunk CSS is scoped; order only
 * matters for truly global overrides across the same bundle.
 */
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      for (const plugin of webpackConfig.plugins || []) {
        if (plugin?.constructor?.name === 'MiniCssExtractPlugin' && plugin.options) {
          plugin.options.ignoreOrder = true;
        }
      }
      return webpackConfig;
    },
  },
};
