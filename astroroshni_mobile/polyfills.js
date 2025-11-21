// Force disable bridgeless mode
global.__turboModuleProxy = null;
global.RN$Bridgeless = false;

// Mock missing modules
const mockModule = {
  getConstants: () => ({
    isTesting: false,
    reactNativeVersion: { major: 0, minor: 73, patch: 6 },
    Version: 17,
    Release: '17.0',
    Model: 'iPhone',
    Brand: 'Apple'
  })
};

// Override registry completely
global.TurboModuleRegistry = {
  get: () => mockModule,
  getEnforcing: () => mockModule
};