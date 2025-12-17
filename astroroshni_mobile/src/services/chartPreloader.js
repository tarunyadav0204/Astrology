import { storage } from './storage';
import { chartAPI } from './api';

class ChartPreloader {
  constructor() {
    this.cache = new Map();
    this.loading = new Set();
  }

  /**
   * Pre-load all charts for a birth data
   */
  async preloadAllCharts(birthData) {
    const cacheKey = this._getCacheKey(birthData);
    
    // Return cached if available
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    // Prevent duplicate loading
    if (this.loading.has(cacheKey)) {
      return this._waitForLoading(cacheKey);
    }

    this.loading.add(cacheKey);

    try {
      // Check storage first
      const stored = await storage.getItem(`charts_${cacheKey}`);
      if (stored) {
        const charts = JSON.parse(stored);
        this.cache.set(cacheKey, charts);
        this.loading.delete(cacheKey);
        return charts;
      }

      // Batch calculate all charts
      const response = await chartAPI.calculateAllCharts(birthData);
      const charts = response.data;

      // Cache in memory and storage
      this.cache.set(cacheKey, charts);
      await storage.setItem(`charts_${cacheKey}`, JSON.stringify(charts));
      
      this.loading.delete(cacheKey);
      return charts;

    } catch (error) {
      this.loading.delete(cacheKey);
      throw error;
    }
  }

  /**
   * Get specific chart from cache
   */
  getChart(birthData, chartType) {
    const cacheKey = this._getCacheKey(birthData);
    const charts = this.cache.get(cacheKey);
    
    if (!charts) return null;

    if (chartType === 'lagna') {
      return charts.lagna;
    }
    
    return charts.divisional_charts?.[chartType];
  }

  /**
   * Clear cache for birth data
   */
  async clearCache(birthData) {
    const cacheKey = this._getCacheKey(birthData);
    this.cache.delete(cacheKey);
    await storage.removeItem(`charts_${cacheKey}`);
  }

  /**
   * Clear all cache
   */
  async clearAllCache() {
    this.cache.clear();
    // Clear storage items starting with 'charts_'
    const keys = await storage.getAllKeys();
    const chartKeys = keys.filter(key => key.startsWith('charts_'));
    await Promise.all(chartKeys.map(key => storage.removeItem(key)));
  }

  _getCacheKey(birthData) {
    return `${birthData.id || birthData.name}_${birthData.date}_${birthData.time}_${birthData.latitude}_${birthData.longitude}`;
  }

  async _waitForLoading(cacheKey) {
    // Poll until loading is complete
    while (this.loading.has(cacheKey)) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return this.cache.get(cacheKey);
  }
}

export const chartPreloader = new ChartPreloader();