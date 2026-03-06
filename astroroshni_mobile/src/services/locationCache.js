import AsyncStorage from '@react-native-async-storage/async-storage';
import majorCities from '../../assets/data/major_cities.json';

const CACHE_KEY = 'location_search_cache';
const CACHE_EXPIRY_DAYS = 30;

class LocationCacheService {
  constructor() {
    this.majorCities = majorCities;
  }

  /**
   * Search locations with hybrid strategy:
   * 1. Search in bundled major cities (instant)
   * 2. Search in AsyncStorage cache (fast)
   * 3. Fallback to Photon API
   * For short queries (2–4 chars), we always call Photon too and merge, so users
   * get Google + cache/major + Photon and aren't stuck with weak cache-only results.
   */
  async searchLocations(query, photonApiFallback) {
    const queryLower = query.toLowerCase().trim();
    const queryLen = queryLower.length;

    if (queryLen < 2) {
      return [];
    }

    const isShortQuery = queryLen <= 4;
    console.log(`🔍 Location search: "${query}"${isShortQuery ? ' (short – will merge with Photon)' : ''}`);

    // Step 1: Search in bundled major cities
    const majorCityResults = this.searchMajorCities(queryLower);

    // Step 2: Search in AsyncStorage cache
    const cachedResults = await this.searchCache(queryLower);

    // For short queries: always call Photon and merge with major/cache so we don't
    // show only a few weak results and never reach Google/Photon
    if (isShortQuery) {
      const photonResults = await photonApiFallback(query);
      if (photonResults.length > 0) {
        await this.cacheResults(queryLower, photonResults);
      }
      const seen = new Set();
      const merged = [];
      for (const r of [...majorCityResults, ...cachedResults, ...photonResults]) {
        const key = (r.name || '').trim().toLowerCase();
        if (key && !seen.has(key)) {
          seen.add(key);
          merged.push(r);
        }
        if (merged.length >= 10) break;
      }
      console.log(`✅ Short query: merged ${majorCityResults.length} major + ${cachedResults.length} cache + ${photonResults.length} Photon → ${merged.length} results`);
      return merged;
    }

    // Longer query: use fast path (major → cache → Photon) as before
    if (majorCityResults.length > 0) {
      console.log(`✅ Found ${majorCityResults.length} results in major cities (instant)`);
      return majorCityResults;
    }
    if (cachedResults.length > 0) {
      console.log(`✅ Found ${cachedResults.length} results in cache (fast)`);
      return cachedResults;
    }

    console.log(`🌐 No cached results, calling Photon API`);
    const apiResults = await photonApiFallback(query);
    if (apiResults.length > 0) {
      await this.cacheResults(queryLower, apiResults);
    }
    return apiResults;
  }

  /**
   * Search in bundled major cities JSON
   */
  searchMajorCities(queryLower) {
    return this.majorCities
      .filter(city => {
        const nameLower = city.name.toLowerCase();
        // Match if query is at start of city name or any word in the name
        return nameLower.includes(queryLower) || 
               nameLower.split(',').some(part => part.trim().startsWith(queryLower));
      })
      .slice(0, 5)
      .map((city, index) => ({
        id: `major_${index}_${Date.now()}`,
        name: city.name,
        latitude: city.lat,
        longitude: city.lng,
        source: 'bundled'
      }));
  }

  /**
   * Search in AsyncStorage cache
   */
  async searchCache(queryLower) {
    try {
      const cacheData = await AsyncStorage.getItem(CACHE_KEY);
      if (!cacheData) {
        return [];
      }

      const cache = JSON.parse(cacheData);
      const now = Date.now();
      const expiryTime = CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000;

      // Find matching cached queries
      const matchingEntries = Object.entries(cache).filter(([cachedQuery, data]) => {
        const isExpired = (now - data.timestamp) > expiryTime;
        const isMatch = cachedQuery.includes(queryLower) || queryLower.includes(cachedQuery);
        return !isExpired && isMatch;
      });

      if (matchingEntries.length === 0) {
        return [];
      }

      // Return results from the best matching cached query
      const [, data] = matchingEntries[0];
      return data.results.map((result, index) => ({
        ...result,
        id: `cached_${index}_${Date.now()}`,
        source: 'cached'
      }));
    } catch (error) {
      console.error('Error reading location cache:', error);
      return [];
    }
  }

  /**
   * Cache API results for future use
   */
  async cacheResults(query, results) {
    try {
      const cacheData = await AsyncStorage.getItem(CACHE_KEY);
      const cache = cacheData ? JSON.parse(cacheData) : {};

      // Add new results to cache
      cache[query] = {
        results: results.map(r => ({
          name: r.name,
          latitude: r.latitude,
          longitude: r.longitude
        })),
        timestamp: Date.now()
      };

      // Limit cache size to 100 entries (keep most recent)
      const entries = Object.entries(cache);
      if (entries.length > 100) {
        const sorted = entries.sort((a, b) => b[1].timestamp - a[1].timestamp);
        const limited = Object.fromEntries(sorted.slice(0, 100));
        await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(limited));
      } else {
        await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(cache));
      }

      console.log(`💾 Cached results for "${query}"`);
    } catch (error) {
      console.error('Error caching location results:', error);
    }
  }

  /**
   * Clear expired cache entries
   */
  async clearExpiredCache() {
    try {
      const cacheData = await AsyncStorage.getItem(CACHE_KEY);
      if (!cacheData) {
        return;
      }

      const cache = JSON.parse(cacheData);
      const now = Date.now();
      const expiryTime = CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000;

      const validEntries = Object.entries(cache).filter(([, data]) => {
        return (now - data.timestamp) <= expiryTime;
      });

      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(Object.fromEntries(validEntries)));
      console.log(`🧹 Cleared expired cache entries`);
    } catch (error) {
      console.error('Error clearing expired cache:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getCacheStats() {
    try {
      const cacheData = await AsyncStorage.getItem(CACHE_KEY);
      if (!cacheData) {
        return { entries: 0, size: 0 };
      }

      const cache = JSON.parse(cacheData);
      return {
        entries: Object.keys(cache).length,
        size: new Blob([cacheData]).size,
        majorCities: this.majorCities.length
      };
    } catch (error) {
      return { entries: 0, size: 0, error: error.message };
    }
  }
}

export default new LocationCacheService();
