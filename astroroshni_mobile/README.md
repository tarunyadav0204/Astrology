# AstroRoshni Mobile App

A React Native mobile application for AstroRoshni - your personal astrology assistant.

## Features

- 🔮 **AI-Powered Chat**: Get personalized astrological predictions
- 👤 **Birth Details**: Secure storage of birth information
- 🌐 **Multi-Language**: Support for English, Hindi, Telugu, Gujarati, Tamil
- 🔊 **Text-to-Speech**: Listen to predictions
- 📱 **WhatsApp Sharing**: Share predictions easily
- 🎨 **Beautiful UI**: AstroRoshni branded design

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Run on device:
```bash
# iOS
npm run ios

# Android
npm run android
```

## Tech Stack

- **React Native** with Expo
- **React Navigation** for navigation
- **AsyncStorage** for local data
- **Expo Speech** for text-to-speech
- **Linear Gradient** for beautiful backgrounds
- **Axios** for API calls

## API Integration

The app connects to the AstroRoshni backend at `http://localhost:8000` for:
- Authentication
- Chat functionality
- Chart generation

## Build for Production

```bash
# Install EAS CLI
npm install -g @expo/eas-cli

# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios
```

## Color Theme

- Primary: #ff6b35 (AstroRoshni Orange)
- Secondary: #f7931e (Gradient Orange)
- Background: Linear gradient from primary to secondary
- Cards: White with orange accents