import AsyncStorage from '@react-native-async-storage/async-storage';

export const cleanupStorage = async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    // console.log(`Found ${keys.length} storage keys`);
    
    // Remove old chat history and temporary data (but keep analysis results)
    const keysToRemove = keys.filter(key => 
      key.startsWith('chat_') || 
      key.startsWith('temp_') ||
      key.includes('_old') ||
      key.includes('_backup')
    );
    
    if (keysToRemove.length > 0) {
      await AsyncStorage.multiRemove(keysToRemove);
      // console.log(`Cleaned up ${keysToRemove.length} storage keys`);
    }
    
    return true;
  } catch (error) {
    console.error('Storage cleanup error:', error);
    return false;
  }
};

export const getStorageSize = async () => {
  try {
    const keys = await AsyncStorage.getAllKeys();
    let totalSize = 0;
    
    for (const key of keys) {
      const value = await AsyncStorage.getItem(key);
      if (value) {
        totalSize += value.length;
      }
    }
    
    return { keys: keys.length, size: totalSize };
  } catch (error) {
    console.error('Storage size check error:', error);
    return { keys: 0, size: 0 };
  }
};