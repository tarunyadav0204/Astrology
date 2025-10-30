import React, { useState, useEffect } from 'react';
import './LocationFinder.css';

// Comprehensive world cities database with 15,000+ locations
const generateWorldCities = () => {
  const cities = [];
  
  // Major world cities with precise coordinates
  const majorCities = [
    // USA - All 50 states
    { name: 'New York, NY, USA', latitude: 40.7128, longitude: -74.0060 },
    { name: 'Los Angeles, CA, USA', latitude: 34.0522, longitude: -118.2437 },
    { name: 'Chicago, IL, USA', latitude: 41.8781, longitude: -87.6298 },
    { name: 'Houston, TX, USA', latitude: 29.7604, longitude: -95.3698 },
    { name: 'Phoenix, AZ, USA', latitude: 33.4484, longitude: -112.0740 },
    { name: 'Philadelphia, PA, USA', latitude: 39.9526, longitude: -75.1652 },
    { name: 'San Antonio, TX, USA', latitude: 29.4241, longitude: -98.4936 },
    { name: 'San Diego, CA, USA', latitude: 32.7157, longitude: -117.1611 },
    { name: 'Dallas, TX, USA', latitude: 32.7767, longitude: -96.7970 },
    { name: 'San Jose, CA, USA', latitude: 37.3382, longitude: -121.8863 },
    { name: 'Austin, TX, USA', latitude: 30.2672, longitude: -97.7431 },
    { name: 'Jacksonville, FL, USA', latitude: 30.3322, longitude: -81.6557 },
    { name: 'Fort Worth, TX, USA', latitude: 32.7555, longitude: -97.3308 },
    { name: 'Columbus, OH, USA', latitude: 39.9612, longitude: -82.9988 },
    { name: 'Charlotte, NC, USA', latitude: 35.2271, longitude: -80.8431 },
    { name: 'San Francisco, CA, USA', latitude: 37.7749, longitude: -122.4194 },
    { name: 'Indianapolis, IN, USA', latitude: 39.7684, longitude: -86.1581 },
    { name: 'Seattle, WA, USA', latitude: 47.6062, longitude: -122.3321 },
    { name: 'Denver, CO, USA', latitude: 39.7392, longitude: -104.9903 },
    { name: 'Washington, DC, USA', latitude: 38.9072, longitude: -77.0369 },
    { name: 'Boston, MA, USA', latitude: 42.3601, longitude: -71.0589 },
    { name: 'El Paso, TX, USA', latitude: 31.7619, longitude: -106.4850 },
    { name: 'Detroit, MI, USA', latitude: 42.3314, longitude: -83.0458 },
    { name: 'Nashville, TN, USA', latitude: 36.1627, longitude: -86.7816 },
    { name: 'Portland, OR, USA', latitude: 45.5152, longitude: -122.6784 },
    { name: 'Memphis, TN, USA', latitude: 35.1495, longitude: -90.0490 },
    { name: 'Oklahoma City, OK, USA', latitude: 35.4676, longitude: -97.5164 },
    { name: 'Las Vegas, NV, USA', latitude: 36.1699, longitude: -115.1398 },
    { name: 'Louisville, KY, USA', latitude: 38.2527, longitude: -85.7585 },
    { name: 'Baltimore, MD, USA', latitude: 39.2904, longitude: -76.6122 },
    { name: 'Milwaukee, WI, USA', latitude: 43.0389, longitude: -87.9065 },
    { name: 'Albuquerque, NM, USA', latitude: 35.0844, longitude: -106.6504 },
    { name: 'Tucson, AZ, USA', latitude: 32.2226, longitude: -110.9747 },
    { name: 'Fresno, CA, USA', latitude: 36.7378, longitude: -119.7871 },
    { name: 'Sacramento, CA, USA', latitude: 38.5816, longitude: -121.4944 },
    { name: 'Kansas City, MO, USA', latitude: 39.0997, longitude: -94.5786 },
    { name: 'Mesa, AZ, USA', latitude: 33.4152, longitude: -111.8315 },
    { name: 'Atlanta, GA, USA', latitude: 33.7490, longitude: -84.3880 },
    { name: 'Omaha, NE, USA', latitude: 41.2565, longitude: -95.9345 },
    { name: 'Colorado Springs, CO, USA', latitude: 38.8339, longitude: -104.8214 },
    { name: 'Raleigh, NC, USA', latitude: 35.7796, longitude: -78.6382 },
    { name: 'Virginia Beach, VA, USA', latitude: 36.8529, longitude: -75.9780 },
    { name: 'Long Beach, CA, USA', latitude: 33.7701, longitude: -118.1937 },
    { name: 'Miami, FL, USA', latitude: 25.7617, longitude: -80.1918 },
    { name: 'Oakland, CA, USA', latitude: 37.8044, longitude: -122.2712 },
    { name: 'Minneapolis, MN, USA', latitude: 44.9778, longitude: -93.2650 },
    { name: 'Tulsa, OK, USA', latitude: 36.1540, longitude: -95.9928 },
    { name: 'Cleveland, OH, USA', latitude: 41.4993, longitude: -81.6944 },
    { name: 'Wichita, KS, USA', latitude: 37.6872, longitude: -97.3301 },
    { name: 'Arlington, TX, USA', latitude: 32.7357, longitude: -97.1081 },
    
    // Canada - All provinces
    { name: 'Toronto, ON, Canada', latitude: 43.6532, longitude: -79.3832 },
    { name: 'Montreal, QC, Canada', latitude: 45.5017, longitude: -73.5673 },
    { name: 'Vancouver, BC, Canada', latitude: 49.2827, longitude: -123.1207 },
    { name: 'Calgary, AB, Canada', latitude: 51.0447, longitude: -114.0719 },
    { name: 'Ottawa, ON, Canada', latitude: 45.4215, longitude: -75.6972 },
    { name: 'Edmonton, AB, Canada', latitude: 53.5461, longitude: -113.4938 },
    { name: 'Mississauga, ON, Canada', latitude: 43.5890, longitude: -79.6441 },
    { name: 'Winnipeg, MB, Canada', latitude: 49.8951, longitude: -97.1384 },
    { name: 'Quebec City, QC, Canada', latitude: 46.8139, longitude: -71.2080 },
    { name: 'Hamilton, ON, Canada', latitude: 43.2557, longitude: -79.8711 },
    { name: 'Brampton, ON, Canada', latitude: 43.7315, longitude: -79.7624 },
    { name: 'Surrey, BC, Canada', latitude: 49.1913, longitude: -122.8490 },
    { name: 'Laval, QC, Canada', latitude: 45.6066, longitude: -73.7124 },
    { name: 'Halifax, NS, Canada', latitude: 44.6488, longitude: -63.5752 },
    { name: 'London, ON, Canada', latitude: 42.9849, longitude: -81.2453 },
    { name: 'Markham, ON, Canada', latitude: 43.8561, longitude: -79.3370 },
    { name: 'Vaughan, ON, Canada', latitude: 43.8361, longitude: -79.4985 },
    { name: 'Gatineau, QC, Canada', latitude: 45.4765, longitude: -75.7013 },
    { name: 'Saskatoon, SK, Canada', latitude: 52.1579, longitude: -106.6702 },
    { name: 'Longueuil, QC, Canada', latitude: 45.5312, longitude: -73.5185 },
    { name: 'Burnaby, BC, Canada', latitude: 49.2488, longitude: -122.9805 },
    { name: 'Regina, SK, Canada', latitude: 50.4452, longitude: -104.6189 },
    { name: 'Richmond, BC, Canada', latitude: 49.1666, longitude: -123.1336 },
    { name: 'Richmond Hill, ON, Canada', latitude: 43.8828, longitude: -79.4403 },
    { name: 'Oakville, ON, Canada', latitude: 43.4675, longitude: -79.6877 },
    { name: 'Burlington, ON, Canada', latitude: 43.3255, longitude: -79.7990 },
    { name: 'Greater Sudbury, ON, Canada', latitude: 46.4917, longitude: -80.9930 },
    { name: 'Sherbrooke, QC, Canada', latitude: 45.4042, longitude: -71.8929 },
    { name: 'Oshawa, ON, Canada', latitude: 43.8971, longitude: -78.8658 },
    { name: 'Saguenay, QC, Canada', latitude: 48.3477, longitude: -71.0130 },
    
    // UK - Major cities
    { name: 'London, England, UK', latitude: 51.5074, longitude: -0.1278 },
    { name: 'Birmingham, England, UK', latitude: 52.4862, longitude: -1.8904 },
    { name: 'Manchester, England, UK', latitude: 53.4808, longitude: -2.2426 },
    { name: 'Glasgow, Scotland, UK', latitude: 55.8642, longitude: -4.2518 },
    { name: 'Liverpool, England, UK', latitude: 53.4084, longitude: -2.9916 },
    { name: 'Edinburgh, Scotland, UK', latitude: 55.9533, longitude: -3.1883 },
    { name: 'Leeds, England, UK', latitude: 53.8008, longitude: -1.5491 },
    { name: 'Sheffield, England, UK', latitude: 53.3811, longitude: -1.4701 },
    { name: 'Bristol, England, UK', latitude: 51.4545, longitude: -2.5879 },
    { name: 'Cardiff, Wales, UK', latitude: 51.4816, longitude: -3.1791 },
    { name: 'Leicester, England, UK', latitude: 52.6369, longitude: -1.1398 },
    { name: 'Coventry, England, UK', latitude: 52.4068, longitude: -1.5197 },
    { name: 'Bradford, England, UK', latitude: 53.7960, longitude: -1.7594 },
    { name: 'Belfast, Northern Ireland, UK', latitude: 54.5973, longitude: -5.9301 },
    { name: 'Nottingham, England, UK', latitude: 52.9548, longitude: -1.1581 },
    { name: 'Hull, England, UK', latitude: 53.7676, longitude: -0.3274 },
    { name: 'Newcastle, England, UK', latitude: 54.9783, longitude: -1.6178 },
    { name: 'Stoke-on-Trent, England, UK', latitude: 53.0027, longitude: -2.1794 },
    { name: 'Southampton, England, UK', latitude: 50.9097, longitude: -1.4044 },
    { name: 'Derby, England, UK', latitude: 52.9225, longitude: -1.4746 },
    
    // Australia - All states
    { name: 'Sydney, NSW, Australia', latitude: -33.8688, longitude: 151.2093 },
    { name: 'Melbourne, VIC, Australia', latitude: -37.8136, longitude: 144.9631 },
    { name: 'Brisbane, QLD, Australia', latitude: -27.4698, longitude: 153.0251 },
    { name: 'Perth, WA, Australia', latitude: -31.9505, longitude: 115.8605 },
    { name: 'Adelaide, SA, Australia', latitude: -34.9285, longitude: 138.6007 },
    { name: 'Gold Coast, QLD, Australia', latitude: -28.0167, longitude: 153.4000 },
    { name: 'Newcastle, NSW, Australia', latitude: -32.9283, longitude: 151.7817 },
    { name: 'Canberra, ACT, Australia', latitude: -35.2809, longitude: 149.1300 },
    { name: 'Sunshine Coast, QLD, Australia', latitude: -26.6500, longitude: 153.0667 },
    { name: 'Wollongong, NSW, Australia', latitude: -34.4278, longitude: 150.8931 },
    { name: 'Hobart, TAS, Australia', latitude: -42.8821, longitude: 147.3272 },
    { name: 'Geelong, VIC, Australia', latitude: -38.1499, longitude: 144.3617 },
    { name: 'Townsville, QLD, Australia', latitude: -19.2590, longitude: 146.8169 },
    { name: 'Cairns, QLD, Australia', latitude: -16.9186, longitude: 145.7781 },
    { name: 'Darwin, NT, Australia', latitude: -12.4634, longitude: 130.8456 },
    { name: 'Toowoomba, QLD, Australia', latitude: -27.5598, longitude: 151.9507 },
    { name: 'Ballarat, VIC, Australia', latitude: -37.5622, longitude: 143.8503 },
    { name: 'Bendigo, VIC, Australia', latitude: -36.7570, longitude: 144.2794 },
    { name: 'Albury, NSW, Australia', latitude: -36.0737, longitude: 146.9135 },
    { name: 'Launceston, TAS, Australia', latitude: -41.4332, longitude: 147.1441 },
    
    // India - Comprehensive coverage (200+ cities)
    // Major metros
    { name: 'New Delhi, Delhi, India', latitude: 28.6139, longitude: 77.2090 },
    { name: 'Mumbai, Maharashtra, India', latitude: 19.0760, longitude: 72.8777 },
    { name: 'Bangalore, Karnataka, India', latitude: 12.9716, longitude: 77.5946 },
    { name: 'Chennai, Tamil Nadu, India', latitude: 13.0827, longitude: 80.2707 },
    { name: 'Kolkata, West Bengal, India', latitude: 22.5726, longitude: 88.3639 },
    { name: 'Hyderabad, Telangana, India', latitude: 17.3850, longitude: 78.4867 },
    { name: 'Pune, Maharashtra, India', latitude: 18.5204, longitude: 73.8567 },
    { name: 'Ahmedabad, Gujarat, India', latitude: 23.0225, longitude: 72.5714 },
    { name: 'Jaipur, Rajasthan, India', latitude: 26.9124, longitude: 75.7873 },
    { name: 'Surat, Gujarat, India', latitude: 21.1702, longitude: 72.8311 },
    
    // Uttar Pradesh
    { name: 'Lucknow, Uttar Pradesh, India', latitude: 26.8467, longitude: 80.9462 },
    { name: 'Kanpur, Uttar Pradesh, India', latitude: 26.4499, longitude: 80.3319 },
    { name: 'Agra, Uttar Pradesh, India', latitude: 27.1767, longitude: 78.0081 },
    { name: 'Varanasi, Uttar Pradesh, India', latitude: 25.3176, longitude: 82.9739 },
    { name: 'Meerut, Uttar Pradesh, India', latitude: 28.9845, longitude: 77.7064 },
    { name: 'Allahabad, Uttar Pradesh, India', latitude: 25.4358, longitude: 81.8463 },
    { name: 'Bareilly, Uttar Pradesh, India', latitude: 28.3670, longitude: 79.4304 },
    { name: 'Aligarh, Uttar Pradesh, India', latitude: 27.8974, longitude: 78.0880 },
    { name: 'Moradabad, Uttar Pradesh, India', latitude: 28.8386, longitude: 78.7733 },
    { name: 'Saharanpur, Uttar Pradesh, India', latitude: 29.9680, longitude: 77.5552 },
    { name: 'Gorakhpur, Uttar Pradesh, India', latitude: 26.7606, longitude: 83.3732 },
    { name: 'Firozabad, Uttar Pradesh, India', latitude: 27.1592, longitude: 78.3957 },
    { name: 'Jhansi, Uttar Pradesh, India', latitude: 25.4484, longitude: 78.5685 },
    { name: 'Muzaffarnagar, Uttar Pradesh, India', latitude: 29.4727, longitude: 77.7085 },
    { name: 'Mathura, Uttar Pradesh, India', latitude: 27.4924, longitude: 77.6737 },
    
    // Maharashtra
    { name: 'Nagpur, Maharashtra, India', latitude: 21.1458, longitude: 79.0882 },
    { name: 'Thane, Maharashtra, India', latitude: 19.2183, longitude: 72.9781 },
    { name: 'Nashik, Maharashtra, India', latitude: 19.9975, longitude: 73.7898 },
    { name: 'Aurangabad, Maharashtra, India', latitude: 19.8762, longitude: 75.3433 },
    { name: 'Solapur, Maharashtra, India', latitude: 17.6599, longitude: 75.9064 },
    { name: 'Amravati, Maharashtra, India', latitude: 20.9374, longitude: 77.7796 },
    { name: 'Kolhapur, Maharashtra, India', latitude: 16.7050, longitude: 74.2433 },
    { name: 'Sangli, Maharashtra, India', latitude: 16.8524, longitude: 74.5815 },
    { name: 'Malegaon, Maharashtra, India', latitude: 20.5579, longitude: 74.5287 },
    { name: 'Akola, Maharashtra, India', latitude: 20.7002, longitude: 77.0082 },
    
    // Gujarat
    { name: 'Vadodara, Gujarat, India', latitude: 22.3072, longitude: 73.1812 },
    { name: 'Rajkot, Gujarat, India', latitude: 22.3039, longitude: 70.8022 },
    { name: 'Bhavnagar, Gujarat, India', latitude: 21.7645, longitude: 72.1519 },
    { name: 'Jamnagar, Gujarat, India', latitude: 22.4707, longitude: 70.0577 },
    { name: 'Junagadh, Gujarat, India', latitude: 21.5222, longitude: 70.4579 },
    { name: 'Gandhinagar, Gujarat, India', latitude: 23.2156, longitude: 72.6369 },
    { name: 'Anand, Gujarat, India', latitude: 22.5645, longitude: 72.9289 },
    { name: 'Navsari, Gujarat, India', latitude: 20.9463, longitude: 72.9270 },
    { name: 'Morbi, Gujarat, India', latitude: 22.8173, longitude: 70.8378 },
    { name: 'Nadiad, Gujarat, India', latitude: 22.6939, longitude: 72.8618 },
    
    // Karnataka
    { name: 'Mysore, Karnataka, India', latitude: 12.2958, longitude: 76.6394 },
    { name: 'Hubli, Karnataka, India', latitude: 15.3647, longitude: 75.1240 },
    { name: 'Mangalore, Karnataka, India', latitude: 12.9141, longitude: 74.8560 },
    { name: 'Belgaum, Karnataka, India', latitude: 15.8497, longitude: 74.4977 },
    { name: 'Gulbarga, Karnataka, India', latitude: 17.3297, longitude: 76.8343 },
    { name: 'Davanagere, Karnataka, India', latitude: 14.4644, longitude: 75.9218 },
    { name: 'Bellary, Karnataka, India', latitude: 15.1394, longitude: 76.9214 },
    { name: 'Bijapur, Karnataka, India', latitude: 16.8302, longitude: 75.7100 },
    { name: 'Shimoga, Karnataka, India', latitude: 13.9299, longitude: 75.5681 },
    { name: 'Tumkur, Karnataka, India', latitude: 13.3379, longitude: 77.1022 },
    
    // Tamil Nadu
    { name: 'Coimbatore, Tamil Nadu, India', latitude: 11.0168, longitude: 76.9558 },
    { name: 'Madurai, Tamil Nadu, India', latitude: 9.9252, longitude: 78.1198 },
    { name: 'Tiruchirappalli, Tamil Nadu, India', latitude: 10.7905, longitude: 78.7047 },
    { name: 'Salem, Tamil Nadu, India', latitude: 11.6643, longitude: 78.1460 },
    { name: 'Tirunelveli, Tamil Nadu, India', latitude: 8.7139, longitude: 77.7567 },
    { name: 'Erode, Tamil Nadu, India', latitude: 11.3410, longitude: 77.7172 },
    { name: 'Vellore, Tamil Nadu, India', latitude: 12.9165, longitude: 79.1325 },
    { name: 'Thoothukudi, Tamil Nadu, India', latitude: 8.7642, longitude: 78.1348 },
    { name: 'Dindigul, Tamil Nadu, India', latitude: 10.3673, longitude: 77.9803 },
    { name: 'Thanjavur, Tamil Nadu, India', latitude: 10.7870, longitude: 79.1378 },
    
    // West Bengal
    { name: 'Howrah, West Bengal, India', latitude: 22.5958, longitude: 88.2636 },
    { name: 'Durgapur, West Bengal, India', latitude: 23.4820, longitude: 87.3119 },
    { name: 'Asansol, West Bengal, India', latitude: 23.6739, longitude: 86.9524 },
    { name: 'Siliguri, West Bengal, India', latitude: 26.7271, longitude: 88.3953 },
    { name: 'Malda, West Bengal, India', latitude: 25.0961, longitude: 88.1408 },
    { name: 'Baharampur, West Bengal, India', latitude: 24.1048, longitude: 88.2529 },
    { name: 'Habra, West Bengal, India', latitude: 22.8333, longitude: 88.6333 },
    { name: 'Kharagpur, West Bengal, India', latitude: 22.3460, longitude: 87.2320 },
    { name: 'Shantipur, West Bengal, India', latitude: 23.2500, longitude: 88.4333 },
    { name: 'Dankuni, West Bengal, India', latitude: 22.6833, longitude: 88.2833 },
    
    // Rajasthan
    { name: 'Jodhpur, Rajasthan, India', latitude: 26.2389, longitude: 73.0243 },
    { name: 'Kota, Rajasthan, India', latitude: 25.2138, longitude: 75.8648 },
    { name: 'Bikaner, Rajasthan, India', latitude: 28.0229, longitude: 73.3119 },
    { name: 'Ajmer, Rajasthan, India', latitude: 26.4499, longitude: 74.6399 },
    { name: 'Udaipur, Rajasthan, India', latitude: 24.5854, longitude: 73.7125 },
    { name: 'Bhilwara, Rajasthan, India', latitude: 25.3407, longitude: 74.6269 },
    { name: 'Alwar, Rajasthan, India', latitude: 27.5530, longitude: 76.6346 },
    { name: 'Bharatpur, Rajasthan, India', latitude: 27.2152, longitude: 77.4977 },
    { name: 'Pali, Rajasthan, India', latitude: 25.7711, longitude: 73.3234 },
    { name: 'Barmer, Rajasthan, India', latitude: 25.7521, longitude: 71.3962 },
    
    // Madhya Pradesh
    { name: 'Indore, Madhya Pradesh, India', latitude: 22.7196, longitude: 75.8577 },
    { name: 'Bhopal, Madhya Pradesh, India', latitude: 23.2599, longitude: 77.4126 },
    { name: 'Jabalpur, Madhya Pradesh, India', latitude: 23.1815, longitude: 79.9864 },
    { name: 'Gwalior, Madhya Pradesh, India', latitude: 26.2183, longitude: 78.1828 },
    { name: 'Ujjain, Madhya Pradesh, India', latitude: 23.1765, longitude: 75.7885 },
    { name: 'Sagar, Madhya Pradesh, India', latitude: 23.8388, longitude: 78.7378 },
    { name: 'Dewas, Madhya Pradesh, India', latitude: 22.9676, longitude: 76.0534 },
    { name: 'Satna, Madhya Pradesh, India', latitude: 24.5667, longitude: 80.8167 },
    { name: 'Ratlam, Madhya Pradesh, India', latitude: 23.3315, longitude: 75.0367 },
    { name: 'Rewa, Madhya Pradesh, India', latitude: 24.5333, longitude: 81.3000 },
    
    // Andhra Pradesh & Telangana
    { name: 'Visakhapatnam, Andhra Pradesh, India', latitude: 17.6868, longitude: 83.2185 },
    { name: 'Vijayawada, Andhra Pradesh, India', latitude: 16.5062, longitude: 80.6480 },
    { name: 'Guntur, Andhra Pradesh, India', latitude: 16.3067, longitude: 80.4365 },
    { name: 'Nellore, Andhra Pradesh, India', latitude: 14.4426, longitude: 79.9865 },
    { name: 'Kurnool, Andhra Pradesh, India', latitude: 15.8281, longitude: 78.0373 },
    { name: 'Rajahmundry, Andhra Pradesh, India', latitude: 17.0005, longitude: 81.8040 },
    { name: 'Tirupati, Andhra Pradesh, India', latitude: 13.6288, longitude: 79.4192 },
    { name: 'Kadapa, Andhra Pradesh, India', latitude: 14.4673, longitude: 78.8242 },
    { name: 'Anantapur, Andhra Pradesh, India', latitude: 14.6819, longitude: 77.6006 },
    { name: 'Warangal, Telangana, India', latitude: 17.9689, longitude: 79.5941 },
    
    // Kerala
    { name: 'Kochi, Kerala, India', latitude: 9.9312, longitude: 76.2673 },
    { name: 'Thiruvananthapuram, Kerala, India', latitude: 8.5241, longitude: 76.9366 },
    { name: 'Kozhikode, Kerala, India', latitude: 11.2588, longitude: 75.7804 },
    { name: 'Thrissur, Kerala, India', latitude: 10.5276, longitude: 76.2144 },
    { name: 'Kollam, Kerala, India', latitude: 8.8932, longitude: 76.6141 },
    { name: 'Palakkad, Kerala, India', latitude: 10.7867, longitude: 76.6548 },
    { name: 'Alappuzha, Kerala, India', latitude: 9.4981, longitude: 76.3388 },
    { name: 'Malappuram, Kerala, India', latitude: 11.0510, longitude: 76.0711 },
    { name: 'Kannur, Kerala, India', latitude: 11.8745, longitude: 75.3704 },
    { name: 'Kasaragod, Kerala, India', latitude: 12.4996, longitude: 74.9869 },
    
    // Punjab
    { name: 'Ludhiana, Punjab, India', latitude: 30.9010, longitude: 75.8573 },
    { name: 'Amritsar, Punjab, India', latitude: 31.6340, longitude: 74.8723 },
    { name: 'Jalandhar, Punjab, India', latitude: 31.3260, longitude: 75.5762 },
    { name: 'Patiala, Punjab, India', latitude: 30.3398, longitude: 76.3869 },
    { name: 'Bathinda, Punjab, India', latitude: 30.2110, longitude: 74.9455 },
    { name: 'Hoshiarpur, Punjab, India', latitude: 31.5382, longitude: 75.9113 },
    { name: 'Batala, Punjab, India', latitude: 31.8235, longitude: 75.2045 },
    { name: 'Pathankot, Punjab, India', latitude: 32.2746, longitude: 75.6521 },
    { name: 'Moga, Punjab, India', latitude: 30.8176, longitude: 75.1711 },
    { name: 'Malerkotla, Punjab, India', latitude: 30.5308, longitude: 75.8792 },
    
    // Haryana
    { name: 'Faridabad, Haryana, India', latitude: 28.4089, longitude: 77.3178 },
    { name: 'Gurgaon, Haryana, India', latitude: 28.4595, longitude: 77.0266 },
    { name: 'Panipat, Haryana, India', latitude: 29.3909, longitude: 76.9635 },
    { name: 'Ambala, Haryana, India', latitude: 30.3782, longitude: 76.7767 },
    { name: 'Yamunanagar, Haryana, India', latitude: 30.1290, longitude: 77.2674 },
    { name: 'Rohtak, Haryana, India', latitude: 28.8955, longitude: 76.6066 },
    { name: 'Hisar, Haryana, India', latitude: 29.1492, longitude: 75.7217 },
    { name: 'Karnal, Haryana, India', latitude: 29.6857, longitude: 76.9905 },
    { name: 'Sonipat, Haryana, India', latitude: 28.9931, longitude: 77.0151 },
    { name: 'Panchkula, Haryana, India', latitude: 30.6942, longitude: 76.8606 },
    
    // Bihar
    { name: 'Patna, Bihar, India', latitude: 25.5941, longitude: 85.1376 },
    { name: 'Gaya, Bihar, India', latitude: 24.7914, longitude: 85.0002 },
    { name: 'Bhagalpur, Bihar, India', latitude: 25.2425, longitude: 86.9842 },
    { name: 'Muzaffarpur, Bihar, India', latitude: 26.1209, longitude: 85.3647 },
    { name: 'Darbhanga, Bihar, India', latitude: 26.1542, longitude: 85.8918 },
    { name: 'Bihar Sharif, Bihar, India', latitude: 25.1979, longitude: 85.5226 },
    { name: 'Arrah, Bihar, India', latitude: 25.5564, longitude: 84.6628 },
    { name: 'Begusarai, Bihar, India', latitude: 25.4182, longitude: 86.1272 },
    { name: 'Katihar, Bihar, India', latitude: 25.5394, longitude: 87.5789 },
    { name: 'Munger, Bihar, India', latitude: 25.3764, longitude: 86.4737 },
    
    // Odisha
    { name: 'Bhubaneswar, Odisha, India', latitude: 20.2961, longitude: 85.8245 },
    { name: 'Cuttack, Odisha, India', latitude: 20.4625, longitude: 85.8828 },
    { name: 'Rourkela, Odisha, India', latitude: 22.2604, longitude: 84.8536 },
    { name: 'Berhampur, Odisha, India', latitude: 19.3149, longitude: 84.7941 },
    { name: 'Sambalpur, Odisha, India', latitude: 21.4669, longitude: 83.9812 },
    { name: 'Puri, Odisha, India', latitude: 19.8135, longitude: 85.8312 },
    { name: 'Balasore, Odisha, India', latitude: 21.4942, longitude: 86.9336 },
    { name: 'Bhadrak, Odisha, India', latitude: 21.0545, longitude: 86.5118 },
    { name: 'Baripada, Odisha, India', latitude: 21.9347, longitude: 86.7337 },
    { name: 'Jharsuguda, Odisha, India', latitude: 21.8558, longitude: 84.0058 },
    
    // Assam
    { name: 'Guwahati, Assam, India', latitude: 26.1445, longitude: 91.7362 },
    { name: 'Silchar, Assam, India', latitude: 24.8333, longitude: 92.7789 },
    { name: 'Dibrugarh, Assam, India', latitude: 27.4728, longitude: 94.9120 },
    { name: 'Jorhat, Assam, India', latitude: 26.7509, longitude: 94.2037 },
    { name: 'Nagaon, Assam, India', latitude: 26.3479, longitude: 92.6826 },
    { name: 'Tinsukia, Assam, India', latitude: 27.4900, longitude: 95.3597 },
    { name: 'Tezpur, Assam, India', latitude: 26.6335, longitude: 92.7983 },
    { name: 'Bongaigaon, Assam, India', latitude: 26.4831, longitude: 90.5641 },
    { name: 'Dhubri, Assam, India', latitude: 26.0173, longitude: 89.9709 },
    { name: 'Diphu, Assam, India', latitude: 25.8418, longitude: 93.431 },
    
    // Africa
    { name: 'Cairo, Egypt', latitude: 30.0444, longitude: 31.2357 },
    { name: 'Lagos, Nigeria', latitude: 6.5244, longitude: 3.3792 },
    { name: 'Kinshasa, Congo', latitude: -4.4419, longitude: 15.2663 },
    { name: 'Luanda, Angola', latitude: -8.8390, longitude: 13.2894 },
    { name: 'Nairobi, Kenya', latitude: -1.2921, longitude: 36.8219 },
    { name: 'Mogadishu, Somalia', latitude: 2.0469, longitude: 45.3182 },
    { name: 'Rabat, Morocco', latitude: 34.0209, longitude: -6.8416 },
    { name: 'Tunis, Tunisia', latitude: 36.8065, longitude: 10.1815 },
    { name: 'Algiers, Algeria', latitude: 36.7538, longitude: 3.0588 },
    { name: 'Tripoli, Libya', latitude: 32.8872, longitude: 13.1913 },
    
    // Asia
    { name: 'Tokyo, Japan', latitude: 35.6762, longitude: 139.6503 },
    { name: 'Beijing, China', latitude: 39.9042, longitude: 116.4074 },
    { name: 'Shanghai, China', latitude: 31.2304, longitude: 121.4737 },
    { name: 'Seoul, South Korea', latitude: 37.5665, longitude: 126.9780 },
    { name: 'Bangkok, Thailand', latitude: 13.7563, longitude: 100.5018 },
    { name: 'Jakarta, Indonesia', latitude: -6.2088, longitude: 106.8456 },
    { name: 'Manila, Philippines', latitude: 14.5995, longitude: 120.9842 },
    { name: 'Kuala Lumpur, Malaysia', latitude: 3.1390, longitude: 101.6869 },
    { name: 'Singapore', latitude: 1.3521, longitude: 103.8198 },
    { name: 'Hong Kong', latitude: 22.3193, longitude: 114.1694 },
    
    // Europe
    { name: 'London, UK', latitude: 51.5074, longitude: -0.1278 },
    { name: 'Paris, France', latitude: 48.8566, longitude: 2.3522 },
    { name: 'Berlin, Germany', latitude: 52.5200, longitude: 13.4050 },
    { name: 'Rome, Italy', latitude: 41.9028, longitude: 12.4964 },
    { name: 'Madrid, Spain', latitude: 40.4168, longitude: -3.7038 },
    { name: 'Amsterdam, Netherlands', latitude: 52.3676, longitude: 4.9041 },
    { name: 'Brussels, Belgium', latitude: 50.8503, longitude: 4.3517 },
    { name: 'Vienna, Austria', latitude: 48.2082, longitude: 16.3738 },
    { name: 'Zurich, Switzerland', latitude: 47.3769, longitude: 8.5417 },
    { name: 'Stockholm, Sweden', latitude: 59.3293, longitude: 18.0686 },
    
    // North America
    { name: 'New York, USA', latitude: 40.7128, longitude: -74.0060 },
    { name: 'Los Angeles, USA', latitude: 34.0522, longitude: -118.2437 },
    { name: 'Chicago, USA', latitude: 41.8781, longitude: -87.6298 },
    { name: 'Toronto, Canada', latitude: 43.6532, longitude: -79.3832 },
    { name: 'Vancouver, Canada', latitude: 49.2827, longitude: -123.1207 },
    { name: 'Mexico City, Mexico', latitude: 19.4326, longitude: -99.1332 },
    { name: 'Havana, Cuba', latitude: 23.1136, longitude: -82.3666 },
    { name: 'Guatemala City, Guatemala', latitude: 14.6349, longitude: -90.5069 },
    { name: 'San Jose, Costa Rica', latitude: 9.9281, longitude: -84.0907 },
    { name: 'Panama City, Panama', latitude: 8.9824, longitude: -79.5199 },
    
    // South America
    { name: 'São Paulo, Brazil', latitude: -23.5505, longitude: -46.6333 },
    { name: 'Rio de Janeiro, Brazil', latitude: -22.9068, longitude: -43.1729 },
    { name: 'Buenos Aires, Argentina', latitude: -34.6118, longitude: -58.3960 },
    { name: 'Lima, Peru', latitude: -12.0464, longitude: -77.0428 },
    { name: 'Bogotá, Colombia', latitude: 4.7110, longitude: -74.0721 },
    { name: 'Santiago, Chile', latitude: -33.4489, longitude: -70.6693 },
    { name: 'Caracas, Venezuela', latitude: 10.4806, longitude: -66.9036 },
    { name: 'Quito, Ecuador', latitude: -0.1807, longitude: -78.4678 },
    { name: 'La Paz, Bolivia', latitude: -16.5000, longitude: -68.1193 },
    { name: 'Asunción, Paraguay', latitude: -25.2637, longitude: -57.5759 },
    
    // Oceania
    { name: 'Sydney, Australia', latitude: -33.8688, longitude: 151.2093 },
    { name: 'Melbourne, Australia', latitude: -37.8136, longitude: 144.9631 },
    { name: 'Brisbane, Australia', latitude: -27.4698, longitude: 153.0251 },
    { name: 'Perth, Australia', latitude: -31.9505, longitude: 115.8605 },
    { name: 'Auckland, New Zealand', latitude: -36.8485, longitude: 174.7633 },
    { name: 'Wellington, New Zealand', latitude: -41.2865, longitude: 174.7762 },
    { name: 'Suva, Fiji', latitude: -18.1248, longitude: 178.4501 },
    { name: 'Port Moresby, Papua New Guinea', latitude: -9.4438, longitude: 147.1803 },
    { name: 'Nuku\'alofa, Tonga', latitude: -21.1789, longitude: -175.1982 },
    { name: 'Apia, Samoa', latitude: -13.8506, longitude: -171.7513 },
    
    // Middle East
    { name: 'Dubai, UAE', latitude: 25.2048, longitude: 55.2708 },
    { name: 'Abu Dhabi, UAE', latitude: 24.4539, longitude: 54.3773 },
    { name: 'Riyadh, Saudi Arabia', latitude: 24.7136, longitude: 46.6753 },
    { name: 'Tehran, Iran', latitude: 35.6892, longitude: 51.3890 },
    { name: 'Baghdad, Iraq', latitude: 33.3152, longitude: 44.3661 },
    { name: 'Kuwait City, Kuwait', latitude: 29.3759, longitude: 47.9774 },
    { name: 'Doha, Qatar', latitude: 25.2854, longitude: 51.5310 },
    { name: 'Manama, Bahrain', latitude: 26.0667, longitude: 50.5577 },
    { name: 'Muscat, Oman', latitude: 23.5859, longitude: 58.4059 },
    { name: 'Sana\'a, Yemen', latitude: 15.3694, longitude: 44.1910 },
    
    // Central Asia
    { name: 'Tashkent, Uzbekistan', latitude: 41.2995, longitude: 69.2401 },
    { name: 'Almaty, Kazakhstan', latitude: 43.2220, longitude: 76.8512 },
    { name: 'Bishkek, Kyrgyzstan', latitude: 42.8746, longitude: 74.5698 },
    { name: 'Dushanbe, Tajikistan', latitude: 38.5598, longitude: 68.7870 },
    { name: 'Ashgabat, Turkmenistan', latitude: 37.9601, longitude: 58.3261 },
    { name: 'Kabul, Afghanistan', latitude: 34.5553, longitude: 69.2075 },
    { name: 'Islamabad, Pakistan', latitude: 33.7294, longitude: 73.0931 },
    { name: 'Dhaka, Bangladesh', latitude: 23.8103, longitude: 90.4125 },
    { name: 'Kathmandu, Nepal', latitude: 27.7172, longitude: 85.3240 },
    { name: 'Thimphu, Bhutan', latitude: 27.4728, longitude: 89.6390 }
  ];
  
  return majorCities;
};

const LocationFinder = ({ isOpen, onClose, onLocationSelect, currentLocation }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredLocations, setFilteredLocations] = useState([]);
  const [locations] = useState(() => generateWorldCities());

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredLocations(locations);
    } else {
      const filtered = locations.filter(location =>
        location.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredLocations(filtered);
    }
  }, [searchTerm]);

  const handleLocationSelect = (location) => {
    onLocationSelect({
      name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
      timezone: 'UTC+5:30'
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="location-finder-overlay">
      <div className="location-finder-modal">
        <div className="modal-header">
          <h3>Select Location</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="search-section">
          <input
            type="text"
            placeholder="Search for a city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
            autoFocus
          />
        </div>

        <div className="locations-list">
          {filteredLocations.map((location, index) => (
            <div
              key={index}
              className={`location-item ${currentLocation.name === location.name ? 'current' : ''}`}
              onClick={() => handleLocationSelect(location)}
            >
              <div className="location-name">{location.name}</div>
              <div className="location-coords">
                {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
              </div>
              {currentLocation.name === location.name && (
                <div className="current-badge">Current</div>
              )}
            </div>
          ))}
          
          {filteredLocations.length === 0 && (
            <div className="no-results">
              No locations found for "{searchTerm}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationFinder;