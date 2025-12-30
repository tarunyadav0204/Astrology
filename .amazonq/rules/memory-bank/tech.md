# Technology Stack

## Programming Languages

### Backend
- **Python 3.9+** - Primary backend language
- **SQL** - Database queries and schema definitions

### Frontend
- **JavaScript (ES6+)** - React web application
- **JSX** - React component syntax
- **CSS3** - Styling and responsive design
- **HTML5** - Markup

### Mobile
- **JavaScript (ES6+)** - React Native application
- **JSX** - React Native components

## Backend Technologies

### Core Framework
- **FastAPI 0.104.1** - Modern async web framework
  - Automatic OpenAPI documentation
  - Pydantic data validation
  - Dependency injection system
  - CORS middleware support

### Web Server
- **Uvicorn 0.24.0** - ASGI server
  - Async request handling
  - WebSocket support
  - Production-ready performance

### Astrological Calculations
- **PySwissEph 2.10.3.2** - Swiss Ephemeris Python bindings
  - Planetary position calculations
  - Lahiri Ayanamsa system
  - High precision ephemeris data
  - Divisional chart calculations

### AI & Machine Learning
- **Google Generative AI 0.3.2** - Gemini API integration
  - Natural language understanding
  - Context-aware responses
  - Structured output generation

### Authentication & Security
- **PyJWT 2.8.0** - JSON Web Token implementation
- **bcrypt 4.1.2** - Password hashing
- **cryptography 41.0.7** - Data encryption/decryption
  - Fernet symmetric encryption
  - Sensitive data protection

### Database
- **SQLite 3** - Embedded relational database
  - Built-in Python support
  - Zero configuration
  - ACID compliance
  - File-based storage

### Utilities
- **python-dotenv 1.0.0** - Environment variable management
- **python-dateutil 2.8.2** - Date/time manipulation
- **pytz 2023.3** - Timezone handling
- **timezonefinder 6.2.0** - Geographic timezone lookup
- **requests 2.31.0** - HTTP client library
- **psutil 5.9.6** - System monitoring
- **Twilio 8.10.0** - SMS service integration

### Data Validation
- **Pydantic 2.5.0** - Data validation using Python type hints
- **python-multipart 0.0.6** - Form data parsing

## Frontend Technologies

### Core Framework
- **React 18.2.0** - UI library
  - Functional components with hooks
  - Context API for state management
  - Virtual DOM for performance

### Build Tools
- **React Scripts 5.0.1** - Create React App toolchain
  - Webpack bundling
  - Babel transpilation
  - Development server with hot reload
  - Production optimization

### Routing
- **React Router DOM 7.9.4** - Client-side routing
  - Declarative routing
  - Protected routes
  - Navigation guards

### HTTP Client
- **Axios 1.6.0** - Promise-based HTTP client
  - Request/response interceptors
  - Automatic JSON transformation
  - Error handling

### UI Components & Styling
- **Styled Components 6.1.0** - CSS-in-JS styling
- **React Grid Layout 1.4.4** - Draggable grid system
- **React Toastify 9.1.3** - Toast notifications

### PDF Generation
- **@react-pdf/renderer 4.3.1** - React-based PDF generation
- **jsPDF 2.5.1** - Client-side PDF creation

### Utilities
- **date-fns 2.30.0** - Date manipulation library
- **React Helmet Async 2.0.5** - Document head management
- **gtag 1.0.1** - Google Analytics integration

## Mobile Technologies

### Framework
- **React Native 0.81.5** - Cross-platform mobile framework
- **React 19.1.0** - UI library
- **Expo 54.0.25** - React Native development platform
  - Managed workflow
  - Over-the-air updates
  - Build service (EAS)

### Navigation
- **@react-navigation/native 6.1.9** - Navigation library
- **@react-navigation/stack 6.3.20** - Stack navigator
- **react-native-screens 4.16.0** - Native screen optimization
- **react-native-gesture-handler 2.28.0** - Touch gesture system
- **react-native-safe-area-context 5.6.0** - Safe area handling

### UI Components
- **@expo/vector-icons 15.0.3** - Icon library
- **expo-linear-gradient 15.0.7** - Gradient backgrounds
- **react-native-svg 15.12.1** - SVG rendering
- **react-native-chart-kit 6.12.0** - Chart visualization

### Platform Features
- **@react-native-picker/picker 2.11.4** - Native picker component
- **@react-native-community/datetimepicker 8.5.1** - Date/time picker
- **react-native-webview 13.15.0** - WebView component

### Storage & File System
- **@react-native-async-storage/async-storage 2.2.0** - Async storage
- **expo-file-system 19.0.19** - File system access

### PDF & Sharing
- **expo-print 15.0.7** - PDF generation
- **expo-sharing 14.0.7** - Native sharing
- **react-native-html-to-pdf 1.3.0** - HTML to PDF conversion

### HTTP Client
- **Axios 1.6.2** - HTTP requests

### Build Tools
- **@babel/core 7.20.0** - JavaScript compiler
- **@react-native/babel-preset 0.82.1** - React Native Babel preset
- **@react-native/metro-config 0.81.5** - Metro bundler config
- **@expo/metro-config 54.0.9** - Expo Metro config

## Development Tools

### Backend Development
```bash
# Start development server
python main.py

# Install dependencies
pip install -r requirements.txt

# Database migrations
python migrate_*.py

# Testing
python test_*.py
```

### Frontend Development
```bash
# Start development server (port 3001)
npm start

# Build for production
npm run build

# Build for development
npm run build:dev
```

### Mobile Development
```bash
# Start Expo development server
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios

# Build APK
./build-apk.sh

# Build for iOS
./build-ios.sh
```

## Build Systems

### Backend
- **pip** - Python package manager
- **requirements.txt** - Dependency specification
- No build step required (interpreted language)

### Frontend
- **npm** - Node package manager
- **Webpack** (via react-scripts) - Module bundler
- **Babel** - JavaScript transpiler
- Output: Static files in `build/` directory

### Mobile
- **npm** - Node package manager
- **Metro** - React Native bundler
- **Gradle** - Android build system
- **Xcode** - iOS build system
- **EAS Build** - Expo cloud build service

## Environment Configuration

### Backend (.env)
```
GEMINI_API_KEY=<api_key>
JWT_SECRET=<secret>
DATABASE_PATH=astrology.db
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=<phone>
```

### Frontend
- Proxy configuration in package.json: `http://localhost:8001`
- Environment-specific builds via NODE_ENV

### Mobile (app.json)
- App name, version, bundle identifiers
- Icon and splash screen assets
- Platform-specific configurations
- Build profiles in eas.json

## API Documentation

### Backend API
- **Automatic OpenAPI docs**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`
- RESTful API design
- JSON request/response format

### API Endpoints Structure
- `/birth-charts/*` - Chart CRUD operations
- `/charts/*` - Chart generation
- `/dashas/*` - Dasha calculations
- `/transits/*` - Transit data
- `/chat/*` - AI chat interface
- `/credits/*` - Credit management
- `/panchang/*` - Almanac data
- `/career/*` - Career analysis
- `/health/*` - Health analysis
- `/wealth/*` - Wealth analysis
- `/marriage/*` - Marriage analysis
- `/education/*` - Education analysis

## Database Management

### SQLite Operations
- Connection per request pattern
- Manual transaction management
- No ORM (raw SQL queries)
- Cursor-based query execution

### Schema Management
- SQL migration scripts in `/migrations`
- Manual schema updates
- Backup scripts included

## Deployment

### Production Server
- **OS**: Linux (Ubuntu/Debian)
- **Process Manager**: systemd
- **Reverse Proxy**: nginx (recommended)
- **SSL**: Let's Encrypt certificates

### Service Configuration
```bash
# Start service
sudo systemctl start astrology-app

# Enable on boot
sudo systemctl enable astrology-app

# View logs
sudo journalctl -u astrology-app -f
```

### Mobile Deployment
- **Android**: Google Play Store via EAS Build
- **iOS**: Apple App Store via EAS Build
- Over-the-air updates via Expo

## Version Control
- **Git** - Source control
- **GitHub** - Repository hosting
- **GitHub Actions** - CI/CD pipeline (configured in `.github/workflows/`)

## Monitoring & Logging

### Backend Logging
- Python logging module
- File-based logs: `backend.log`, `app.log`, `server.log`
- Structured logging for AI interactions in `logs/gemini_logs/`
- Intent routing logs in `logs/intent_logs/`

### Frontend
- Browser console logging
- Error boundary components
- React DevTools support

### Mobile
- Expo logging system
- React Native Debugger support
- Platform-specific crash reporting (configurable)

## Performance Considerations

### Backend
- Async/await for I/O operations
- Connection pooling for database
- Caching of ephemeris calculations
- Efficient Swiss Ephemeris usage

### Frontend
- Code splitting with React.lazy
- Memoization with useMemo/useCallback
- Virtual scrolling for large lists
- Image optimization

### Mobile
- Native module optimization
- FlatList for efficient rendering
- Image caching
- Bundle size optimization
