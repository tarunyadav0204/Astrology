const fs = require('fs');
const path = require('path');

function withIosIconBackground(config) {
  return {
    ...config,
    plugins: [
      ...(config.plugins || []),
      [
        'withDangerousMod',
        {
          platform: 'ios',
          mod: async (config) => {
            const projectRoot = config.modRequest.projectRoot;
            const iconIos = path.join(projectRoot, 'assets', 'icon-ios.png');
            const appIconSet = path.join(
              config.modRequest.platformProjectRoot,
              'AstroRoshni',
              'Images.xcassets',
              'AppIcon.appiconset',
              'App-Icon-1024x1024@1x.png'
            );
            if (fs.existsSync(iconIos) && fs.existsSync(path.dirname(appIconSet))) {
              fs.copyFileSync(iconIos, appIconSet);
            }
            return config;
          },
        },
      ],
    ],
  };
}

module.exports = withIosIconBackground;
