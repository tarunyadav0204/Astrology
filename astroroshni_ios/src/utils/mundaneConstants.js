export const COUNTRIES = [
  { name: 'India', lat: 28.6139, lng: 77.2090, capital: 'New Delhi' },
  { name: 'USA', lat: 38.9072, lng: -77.0369, capital: 'Washington DC' },
  { name: 'UK', lat: 51.5074, lng: -0.1278, capital: 'London' },
  { name: 'China', lat: 39.9042, lng: 116.4074, capital: 'Beijing' },
  { name: 'Pakistan', lat: 33.6844, lng: 73.0479, capital: 'Islamabad' },
  { name: 'Bangladesh', lat: 23.8103, lng: 90.4125, capital: 'Dhaka' },
  { name: 'Sri Lanka', lat: 6.9271, lng: 79.8612, capital: 'Colombo' },
  { name: 'Nepal', lat: 27.7172, lng: 85.3240, capital: 'Kathmandu' },
  { name: 'Japan', lat: 35.6762, lng: 139.6503, capital: 'Tokyo' },
  { name: 'Germany', lat: 52.5200, lng: 13.4050, capital: 'Berlin' },
  { name: 'France', lat: 48.8566, lng: 2.3522, capital: 'Paris' },
  { name: 'Brazil', lat: -15.8267, lng: -47.9218, capital: 'Brasília' },
  { name: 'Russia', lat: 55.7558, lng: 37.6173, capital: 'Moscow' },
  { name: 'Australia', lat: -35.2809, lng: 149.1300, capital: 'Canberra' },
];

export const YEARS = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() + i);
