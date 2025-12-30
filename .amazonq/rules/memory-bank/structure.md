# Project Structure

## Repository Organization
Multi-platform monorepo with three main applications sharing a common backend.

```
AstrologyApp/
├── backend/              # Python FastAPI backend
├── frontend/             # React web application
├── astroroshni_mobile/   # React Native mobile app (primary)
├── mobile/               # Legacy mobile app (AstroGPT)
├── docs/                 # Documentation
├── systemd/              # Server deployment configs
└── logs/                 # Application logs
```

## Backend Architecture (`/backend`)

### Core Structure
```
backend/
├── main.py                    # FastAPI application entry point
├── auth.py                    # JWT authentication & user management
├── astrology.db               # SQLite database
├── requirements.txt           # Python dependencies
└── ephe/                      # Swiss Ephemeris data files
```

### Domain Modules
Organized by astrological domain with dedicated route handlers:

- **calculators/** - Core calculation engines (70+ specialized calculators)
  - Base calculator classes and inheritance hierarchy
  - Divisional charts, Dasha systems, strength calculations
  - Specialized analyzers (career, health, wealth, marriage, education)
  - Financial, mundane, numerology sub-modules
  
- **ai/** - AI-powered analysis using Google Gemini
  - Domain-specific context generators (career, health, wealth, marriage, education, trading)
  - Intent routing and response parsing
  - Gemini chat analyzer integration

- **chat/** - Conversational AI system
  - Chat routes and session management
  - Context building from birth chart data
  - Fact extraction and feedback system
  
- **birth_charts/** - Birth chart CRUD operations
- **charts/** - Chart generation and rendering
- **Dashas/** - Dasha calculation routes
- **transits/** - Real-time transit calculations
- **panchang/** - Daily almanac and muhurat
- **festivals/** - Festival calendar system
- **nakshatra/** - Nakshatra analysis routes
- **marriage_analysis/** - Compatibility and Guna Milan
- **career_analysis/** - Career path and timing analysis
- **health/** - Health activation and disease analysis
- **wealth/** - Wealth timing and financial analysis
- **education/** - Academic analysis
- **progeny/** - Child prediction analysis
- **credits/** - Credit management system with admin controls
- **chat_history/** - Chat session persistence
- **horoscope/** - Daily/weekly/monthly horoscope generation
- **nadi/** - Nadi astrology system
- **blank_chart/** - Query-based predictions without birth data
- **rule_engine/** - Configurable astrological rule system
- **event_prediction/** - Life event timing predictions
- **vedic_predictions/** - Classical Vedic prediction engines
- **classical_engine/** - Traditional interpretation system
- **utils/** - Timezone, validation, shared utilities

### Key Backend Files
- **encryption_utils.py** - Data encryption for sensitive information
- **sms_service.py** - Twilio SMS integration
- **user_settings.py** - User preference management
- **planetary_dignities.py** - Exaltation, debilitation calculations
- **complete_nakshatras.py** - Nakshatra data and interpretations
- **house_combinations.py** - House signification rules

## Frontend Architecture (`/frontend`)

### Structure
```
frontend/
├── public/
│   ├── images/           # Static assets
│   └── index.html        # Entry HTML
└── src/
    ├── App.js            # Main application component
    ├── index.js          # React entry point
    ├── components/       # React components
    ├── services/         # API service layer
    ├── context/          # React context providers
    ├── hooks/            # Custom React hooks
    ├── styles/           # CSS stylesheets
    ├── config/           # Configuration files
    ├── data/             # Static data files
    ├── utils/            # Utility functions
    └── user-persona/     # User profile components
```

### Component Organization
Components are organized by feature domain:
- **AstroRoshniHomepage/** - Landing page and navigation
- **BirthDetailsForm/** - User input for birth data
- **ChartDisplay/** - Chart rendering (North/South Indian styles)
- **DashaTable/** - Dasha period visualization
- **TransitDisplay/** - Real-time transit information
- **AnalysisTabs/** - Domain-specific analysis views
- **ChatInterface/** - AI chat components
- **PanchangDisplay/** - Daily almanac view
- **ReportGenerator/** - PDF report creation

## Mobile Architecture (`/astroroshni_mobile`)

### Structure
```
astroroshni_mobile/
├── App.js                # React Native entry point
├── app.json              # Expo configuration
├── eas.json              # Expo Application Services config
├── android/              # Android native code
├── ios/                  # iOS native code
├── assets/               # Images, icons, splash screens
└── src/
    ├── components/       # React Native components
    │   ├── Chat/         # Chat interface
    │   ├── Dasha/        # Dasha visualization
    │   ├── Charts/       # Chart rendering
    │   └── Analysis/     # Analysis views
    ├── navigation/       # React Navigation setup
    ├── services/         # API integration
    ├── utils/            # Utility functions
    └── credits/          # Credit management UI
```

### Mobile-Specific Features
- Native PDF generation and sharing
- Offline data caching
- Push notification support (configured)
- Platform-specific UI adaptations
- Gesture-based navigation

## Database Schema (`astrology.db`)

### Core Tables
- **users** - User accounts with authentication
- **birth_charts** - Stored birth chart data (encrypted)
- **chat_sessions** - Conversational AI sessions
- **chat_messages** - Individual chat messages
- **chat_feedback** - User feedback on AI responses
- **credits** - User credit balances
- **credit_transactions** - Credit usage history
- **credit_requests** - User credit requests
- **promo_codes** - Promotional code system
- **nakshatras** - Nakshatra reference data
- **planet_nakshatra_interpretations** - Interpretation texts
- **festivals** - Festival calendar data
- **user_settings** - User preferences

## Architectural Patterns

### Backend Patterns
1. **Modular Route Organization** - Domain-driven route modules
2. **Calculator Inheritance** - Base calculator classes with specialized implementations
3. **Context Builder Pattern** - AI context generation from chart data
4. **Service Layer** - Separation of business logic from routes
5. **Dependency Injection** - FastAPI dependency system for auth
6. **Database Connection Pooling** - SQLite connection management
7. **Error Handling** - Centralized exception handling with HTTPException

### Frontend Patterns
1. **Component Composition** - Reusable component hierarchy
2. **Context API** - Global state management (AuthContext, ChartContext)
3. **Custom Hooks** - Reusable logic extraction
4. **Service Layer** - Axios-based API abstraction
5. **Responsive Design** - Mobile-first CSS approach
6. **Lazy Loading** - Code splitting for performance
7. **Protected Routes** - Authentication-based routing

### Mobile Patterns
1. **Stack Navigation** - Screen-based navigation flow
2. **AsyncStorage** - Local data persistence
3. **Platform-Specific Code** - iOS/Android adaptations
4. **Expo Managed Workflow** - Simplified build process
5. **Component Reusability** - Shared components across screens

## Data Flow

### Chart Generation Flow
1. User submits birth details via form
2. Frontend validates and sends to `/birth-charts/create`
3. Backend calculates using Swiss Ephemeris
4. Chart data stored in database (encrypted)
5. Response includes chart positions, houses, aspects
6. Frontend renders chart in selected style

### AI Chat Flow
1. User sends message to `/chat/message`
2. Backend retrieves birth chart context
3. Context builder generates structured data
4. Intent router determines query type
5. Domain-specific AI context generator prepares prompt
6. Gemini API generates response
7. Response parser extracts structured data
8. Message stored in chat_history
9. Frontend displays formatted response

### Credit System Flow
1. User action requires credits
2. Frontend checks credit balance
3. Backend validates and deducts credits
4. Transaction recorded in credit_transactions
5. Service executes (AI query, report generation)
6. Response returned to user
7. Frontend updates credit display

## Configuration Files

- **backend/.env** - Environment variables (API keys, database path)
- **frontend/package.json** - NPM dependencies and scripts
- **astroroshni_mobile/app.json** - Expo app configuration
- **astroroshni_mobile/eas.json** - Build profiles
- **systemd/astrology-app.service** - Linux service configuration
- **.github/workflows/deploy.yml** - CI/CD pipeline

## Deployment Structure

### Production Setup
- Backend runs on port 8001 via uvicorn
- Frontend builds to static files served by nginx
- Mobile apps distributed via App Store/Play Store
- SQLite database with regular backups
- Systemd service for backend auto-restart
- Log rotation for application logs
