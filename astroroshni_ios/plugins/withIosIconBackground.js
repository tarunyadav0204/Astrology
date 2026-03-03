const fs = require('fs');
const path = require('path');

/**
 * If assets/icon-ios.png exists, use it for the iOS app icon so the icon
 * is visible on the home screen (solid background). Use this when your
 * main icon has transparency and appears white on iOS.
 */
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
