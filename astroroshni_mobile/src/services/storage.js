import AsyncStorage from '@react-native-async-storage/async-storage';

export const storage = {
  // Auth
  setAuthToken: (token) => AsyncStorage.setItem('authToken', token),
  getAuthToken: () => AsyncStorage.getItem('authToken'),
  removeAuthToken: () => AsyncStorage.removeItem('authToken'),
  
  // User data
  setUserData: (userData) => AsyncStorage.setItem('userData', JSON.stringify(userData)),
  getUserData: async () => {
    const data = await AsyncStorage.getItem('userData');
    return data ? JSON.parse(data) : null;
  },
  
  // Birth details
  setBirthDetails: async (details) => {
    // console.log('💾 [DEBUG] Storage: setBirthDetails called with:', JSON.stringify(details, null, 2));
    // console.log('⚧️ [DEBUG] Storage: Gender being saved:', details?.gender);
    const result = await AsyncStorage.setItem('birthDetails', JSON.stringify(details));
    // console.log('✅ [DEBUG] Storage: setBirthDetails completed');
    return result;
  },
  getBirthDetails: async () => {
    // console.log('📂 [DEBUG] Storage: getBirthDetails called');
    const data = await AsyncStorage.getItem('birthDetails');
    const parsed = data ? JSON.parse(data) : null;
    // console.log('📂 [DEBUG] Storage: getBirthDetails returning:', JSON.stringify(parsed, null, 2));
    // console.log('⚧️ [DEBUG] Storage: Gender from storage:', parsed?.gender);
    return parsed;
  },
  
  // Birth data (alias for birth details)
  setBirthData: (data) => storage.setBirthDetails(data),
  getBirthData: () => storage.getBirthDetails(),
  
  // Language preference
  setLanguage: (language) => AsyncStorage.setItem('language', language),
  getLanguage: () => AsyncStorage.getItem('language'),
  
  // Chat history
  setChatHistory: (history) => AsyncStorage.setItem('chatHistory', JSON.stringify(history)),
  getChatHistory: async () => {
    const data = await AsyncStorage.getItem('chatHistory');
    return data ? JSON.parse(data) : [];
  },
  
  // Chart data
  setChartData: (chartData) => AsyncStorage.setItem('chartData', JSON.stringify(chartData)),
  getChartData: async () => {
    const data = await AsyncStorage.getItem('chartData');
    return data ? JSON.parse(data) : null;
  },
  clearChartData: () => AsyncStorage.removeItem('chartData'),
  
  // Clear birth details
  clearBirthDetails: () => AsyncStorage.removeItem('birthDetails'),
  
  // Birth profiles (multiple natives)
  setBirthProfiles: (profiles) => AsyncStorage.setItem('birthProfiles', JSON.stringify(profiles)),
  getBirthProfiles: async () => {
    const data = await AsyncStorage.getItem('birthProfiles');
    return data ? JSON.parse(data) : [];
  },
  addBirthProfile: async (profile) => {
    // console.log('📁 [DEBUG] Storage: addBirthProfile called with:', JSON.stringify(profile, null, 2));
    // console.log('⚧️ [DEBUG] Storage: Profile gender:', profile?.gender);
    const profiles = await storage.getBirthProfiles();
    const updatedProfiles = profiles.filter(p => p.name !== profile.name);
    updatedProfiles.push(profile);
    await storage.setBirthProfiles(updatedProfiles);
    // console.log('✅ [DEBUG] Storage: addBirthProfile completed');
  },
  removeBirthProfile: async (profileName) => {
    const profiles = await storage.getBirthProfiles();
    const updatedProfiles = profiles.filter(p => p.name !== profileName);
    await storage.setBirthProfiles(updatedProfiles);
  },
  
  // Favorites
  setFavorites: (favorites) => AsyncStorage.setItem('favorites', JSON.stringify(favorites)),
  getFavorites: async () => {
    const data = await AsyncStorage.getItem('favorites');
    return data ? JSON.parse(data) : [];
  },
  
  // Generic storage methods
  setItem: (key, value) => AsyncStorage.setItem(key, value),
  getItem: (key) => AsyncStorage.getItem(key),
  removeItem: (key) => AsyncStorage.removeItem(key),
  
  // Clear all data
  clearAll: () => AsyncStorage.clear(),
};