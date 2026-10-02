// Exercise the actual PWA/mobile bubble with native host components stubbed.
// Run from the repo root: node astroroshni_mobile/scripts/test-instant-render.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const babel = require('@babel/core');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const host = tag => ({ children }) => React.createElement(tag, null, children);
const View = host('div');
const Text = host('span');
const empty = () => null;
const mocks = {
  react: React,
  'react-native': {
    View, Text, TouchableOpacity: View, ScrollView: View, Modal: empty, Image: empty,
    ActivityIndicator: empty, StyleSheet: { create: x => x, absoluteFillObject: {} },
    Animated: { Value: class { constructor(value) { this.value = value; } }, View },
    Dimensions: { get: () => ({width: 400, height: 800}) }, Platform: { OS: 'web', select: x => x.web || x.default },
  },
  '@react-navigation/native': { useFocusEffect: () => {}, useNavigation: () => ({}) },
  'react-i18next': { useTranslation: () => ({t: (key, fallback) => typeof fallback === 'string' ? fallback : key, i18n: {language:'en'}}) },
  '../../context/ThemeContext': { useTheme: () => ({theme:'light', colors: {}}) },
  '../../credits/CreditContext': { useCredits: () => ({credits:100, pricing:{}}) },
  '../../auth/AuthGateContext': { useAuthGate: () => ({}) },
  '../../theme/tokens': { chatSentimentColors: () => ({}) },
  '../../utils/constants': { COLORS: {}, getEndpoint: x => x },
};
const files = new Map();
function load(file) {
  if (files.has(file)) return files.get(file);
  const code = babel.transformSync(fs.readFileSync(file, 'utf8'), {
    filename:file, babelrc:false, configFile:false,
    presets:[require.resolve('@babel/preset-react')],
    plugins:[require.resolve('@babel/plugin-transform-modules-commonjs')],
  }).code;
  const module = {exports:{}};
  const localRequire = name => {
    if (mocks[name]) return mocks[name];
    if (['./InstantChartContext','../../utils/useInstantChartRows','../../utils/instantProgress'].includes(name)) {
      return load(path.resolve(path.dirname(file), `${name}.js`));
    }
    return new Proxy({__esModule:true, default:empty}, {get:(obj,key) => key in obj ? obj[key] : empty});
  };
  new Function('require','module','exports','__DEV__',code)(localRequire,module,module.exports,false);
  files.set(file,module.exports);
  return module.exports;
}
const root = path.resolve(__dirname, '..');
const Bubble = load(path.join(root,'src/components/Chat/MessageBubble.js')).default;
const {applyInstantProgress,buildImmediateChartPreview} = load(path.join(root,'src/utils/instantProgress.js'));
const render = message => renderToStaticMarkup(React.createElement(Bubble,{message}));
const pending = {id:'test', role:'assistant', chatTier:'instant', content:'', isTyping:true};
const context = applyInstantProgress(pending,{preview:buildImmediateChartPreview({ascendant:0,planets:{Moon:{longitude:35},Sun:{longitude:70}}})});
assert.equal(context.isTyping,true);
assert.equal(context.instantStreaming,undefined);
assert.equal(context.content,'');
assert.equal(context.instantPreview.rows.length,3);
const first = render(context);
assert.equal(first,'');
assert.equal(render(pending),'');
const partial = applyInstantProgress(context,{content:'The first LLM sentence.'});
assert.equal(partial.isTyping,false);
assert.equal(partial.instantStreaming,true);
assert.match(render(partial),/The first LLM sentence/);
assert.equal(partial.content,'The first LLM sentence.');
const restored = { ...pending, isTyping:false, gate_metadata:{instant_preview:context.instantPreview} };
assert.doesNotMatch(render(restored),/Selected chart/);
console.log('PASS: PWA preserves typing while chart metadata arrives, then streams only real LLM text.');
