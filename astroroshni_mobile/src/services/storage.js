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
    console.log('💾 [CRITICAL] setBirthDetails called with:', details.name, 'ID:', details.id);
    const result = await AsyncStorage.setItem('birthDetails', JSON.stringify(details));
    return result;
  },
  getBirthDetails: async () => {
    const data = await AsyncStorage.getItem('birthDetails');
    const parsed = data ? JSON.parse(data) : null;
    console.log('📂 [DEBUG] Storage: getBirthDetails returning:', parsed ? { name: parsed.name, id: parsed.id } : null);
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
  setBirthProfiles: (profiles) => {
    console.log('💾 [DEBUG] Storage: setBirthProfiles called with count:', profiles.length);
    console.log('💾 [DEBUG] Storage: setBirthProfiles profiles:', profiles.map(p => ({ name: p.name, id: p.id })));
    return AsyncStorage.setItem('birthProfiles', JSON.stringify(profiles));
  },
  getBirthProfiles: async () => {
    const data = await AsyncStorage.getItem('birthProfiles');
    const profiles = data ? JSON.parse(data) : [];
    console.log('📂 [DEBUG] Storage: getBirthProfiles returning count:', profiles.length);
    console.log('📂 [DEBUG] Storage: getBirthProfiles profiles:', profiles.map(p => ({ name: p.name, id: p.id })));
    return profiles;
  },
  addBirthProfile: async (profile) => {
    console.log('📁 [DEBUG] Storage: addBirthProfile called with:', JSON.stringify({ name: profile.name, id: profile.id }, null, 2));
    const profiles = await storage.getBirthProfiles();
    console.log('📋 [DEBUG] Storage: Current profiles before filter:', profiles.map(p => ({ name: p.name, id: p.id })));
    const updatedProfiles = profiles.filter(p => p.id !== profile.id);
    console.log('📋 [DEBUG] Storage: Profiles after filter:', updatedProfiles.map(p => ({ name: p.name, id: p.id })));
    updatedProfiles.push(profile);
    console.log('📋 [DEBUG] Storage: Final profiles list:', updatedProfiles.map(p => ({ name: p.name, id: p.id })));
    await storage.setBirthProfiles(updatedProfiles);
    console.log('✅ [DEBUG] Storage: addBirthProfile completed');
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