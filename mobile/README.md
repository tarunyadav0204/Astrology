# Astrology Mobile App

React Native mobile application for Vedic astrology calculations and analysis.

## Features

- **Birth Chart Calculation**: Generate accurate Vedic birth charts
- **Divisional Charts**: Support for Navamsa, Dasamsa, and other divisional charts
- **House Analysis**: Detailed analysis of all 12 houses
- **Planetary Analysis**: Comprehensive planetary positions and aspects
- **Yoga Detection**: Identify important yogas in the chart
- **Dasha Periods**: Calculate and display Vimshottari dasha periods
- **Cross-Platform**: Runs on iOS, Android, and Web

## Tech Stack

- **React Native**: Cross-platform mobile development
- **Expo**: Development platform and tools
- **React Navigation**: Navigation between screens
- **React Native SVG**: Chart rendering
- **Axios**: API communication

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator (for iOS development)
- Android Studio (for Android development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AstrologyApp/mobile
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure API endpoint**
   - Update `API_BASE_URL` in `src/services/apiService.js`
   - Point to your backend server (default: http://localhost:8000)

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Run on device/simulator**
   ```bash
   # iOS
   npm run ios
   
   # Android
   npm run android
   
   # Web
   npm run web
   ```

## Project Structure

```
mobile/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── NorthIndianChart.js
│   ├── screens/            # Screen components
│   │   ├── BirthFormScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── ChartsScreen.js
│   │   └── AnalysisScreen.js
│   ├── services/           # API and external services
│   │   └── apiService.js
│   └── utils/              # Utility functions
├── App.js                  # Main app component
└── package.json
```

## Screens

### 1. Birth Form Screen
- Input birth details (name, date, time, place)
- Location search and coordinate input
- Form validation and submission

### 2. Dashboard Screen
- Display birth chart with planetary positions
- Quick info cards (Lagna, Rashi, Nakshatra)
- Action buttons for different chart types

### 3. Charts Screen
- Divisional chart selection (D1, D9, D10, D12)
- Interactive chart display
- Planetary position details

### 4. Analysis Screen
- House analysis with detailed descriptions
- Planetary analysis and characteristics
- Yoga detection and explanations
- Dasha period calculations

## API Integration

The app communicates with the backend API for:
- Chart calculations
- Location search
- Data persistence
- Analysis computations

Update the `API_BASE_URL` in `apiService.js` to match your backend deployment.

## Building for Production

### Android
```bash
expo build:android
```

### iOS
```bash
expo build:ios
```

### Web
```bash
expo build:web
```

## Deployment

The app can be deployed to:
- **Google Play Store** (Android)
- **Apple App Store** (iOS)
- **Web hosting** (Netlify, Vercel, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms
5. Submit a pull request

## License

This project is licensed under the MIT License.