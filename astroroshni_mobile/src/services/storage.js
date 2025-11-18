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
  setBirthDetails: (details) => AsyncStorage.setItem('birthDetails', JSON.stringify(details)),
  getBirthDetails: async () => {
    const data = await AsyncStorage.getItem('birthDetails');
    return data ? JSON.parse(data) : null;
  },
  
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
  
  // Clear all data
  clearAll: () => AsyncStorage.clear(),
};