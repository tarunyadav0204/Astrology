/**
 * App entry (replaces default expo/AppEntry.js import of ../../App) so Metro always
 * resolves the root component from this package. Run `npx expo start` from this folder.
 */
import registerRootComponent from 'expo/src/launch/registerRootComponent';
import App from './App';

registerRootComponent(App);
