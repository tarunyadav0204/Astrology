import { NativeEventEmitter, NativeModules, Platform } from 'react-native';

const nativeModule = Platform.OS === 'android' ? NativeModules.PlayInAppUpdate : null;

export function isPlayInAppUpdateAvailable() {
  return Boolean(nativeModule);
}

export function checkPlayUpdate() {
  if (!nativeModule) return Promise.resolve(null);
  return nativeModule.check();
}

export function startPlayUpdate(mode) {
  if (!nativeModule) return Promise.resolve('unavailable');
  return nativeModule.start(mode === 'immediate' ? 'immediate' : 'flexible');
}

export function completePlayUpdate() {
  if (!nativeModule) return Promise.resolve();
  return nativeModule.completeUpdate();
}

export function subscribePlayUpdate(listener) {
  if (!nativeModule) return () => {};
  const emitter = new NativeEventEmitter(nativeModule);
  const subscription = emitter.addListener('PlayInAppUpdateStatus', listener);
  return () => subscription.remove();
}
