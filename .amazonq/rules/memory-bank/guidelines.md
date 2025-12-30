# Development Guidelines

## Code Quality Standards

### Formatting and Structure
- **Indentation**: 4 spaces for Python, 2 spaces for JavaScript/JSX
- **Line Length**: Keep lines under 120 characters where practical
- **File Organization**: Group related functionality together, separate concerns clearly
- **Import Organization**: Standard library first, third-party next, local imports last
- **Whitespace**: Use blank lines to separate logical sections within functions

### Naming Conventions
- **Python**: 
  - snake_case for functions, variables, and methods
  - PascalCase for classes
  - UPPER_CASE for constants
  - Descriptive names that indicate purpose (e.g., `calculate_cascading_dashas`, `fetch_planetary_positions`)
- **JavaScript/React**:
  - camelCase for functions and variables
  - PascalCase for React components
  - UPPER_CASE for constants
  - Descriptive component names (e.g., `CascadingDashaBrowser`, `AstroRoshniHomepage`)

### Documentation Standards
- **Python Docstrings**: Use triple-quoted strings for function/class documentation
  ```python
  def analyze_suitable_professions(self):
      \"\"\"Professional comprehensive career analysis\"\"\"
  ```
- **Inline Comments**: Explain complex logic, astrological calculations, or non-obvious decisions
- **Configuration Comments**: Document rule structures, planetary significations, and astrological mappings
- **React Components**: Add comments for complex state management or lifecycle logic

## Semantic Patterns

### Backend Patterns (Python/FastAPI)

#### 1. Calculator Inheritance Pattern
- Base calculator class provides common functionality
- Specialized calculators inherit and extend
- Example from codebase:
  ```python
  class SuitableProfessionsAnalyzer(BaseCalculator):
      def __init__(self, chart_data, birth_data):
          super().__init__(chart_data)
          # Initialize specialized calculators
          self.shadbala_calc = ShadbalaCalculator(chart_data)
          self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
  ```

#### 2. Comprehensive Data Structures
- Use dictionaries for complex astrological mappings
- Nested structures for hierarchical data (houses, planets, signs)
- Example pattern:
  ```python
  BODY_PARTS_BY_HOUSE = {
      1: {
          "primary": ["head", "brain", "skull"],
          "secondary": ["eyes", "hair", "complexion"],
          "ruling_signs": ["Aries"],
          "karaka_planets": ["Sun", "Mars"]
      }
  }
  ```

#### 3. Multi-Source Data Integration
- Combine multiple calculation systems (Shadbala, Dignities, Nakshatras)
- Synthesize results from different astrological techniques
- Pattern: Initialize multiple calculators, gather data, synthesize results

#### 4. Detailed Explanation Generation
- Provide astrological reasoning alongside predictions
- Include classical references and traditional wisdom
- Pattern: Generate both prediction and explanation in parallel

#### 5. Error Handling with Graceful Degradation
- Try-except blocks with specific error messages
- Fallback to default values when calculations fail
- Log errors for debugging without breaking user experience

### Frontend Patterns (React)

#### 1. State Management with Hooks
- useState for local component state
- useEffect for side effects and data fetching
- useCallback for memoized functions
- Custom hooks for reusable logic
- Example from codebase:
  ```javascript
  const [currentSlide, setCurrentSlide] = useState(0);
  const [horoscopeData, setHoroscopeData] = useState({});
  
  useEffect(() => {
      fetchHoroscopes();
  }, []);
  ```

#### 2. Conditional Rendering Patterns
- Ternary operators for simple conditions
- Logical AND (&&) for conditional display
- Early returns for loading/error states
- Example:
  ```javascript
  {loading ? (
      <div className="loading">Loading...</div>
  ) : (
      <div className="content">{data}</div>
  )}
  ```

#### 3. Component Composition
- Break complex UIs into smaller, reusable components
- Pass data via props, callbacks for actions
- Use children prop for flexible layouts
- Example: `<OptionCard>`, `<AnalysisCard>`, `<LifeAnalysisCard>`

#### 4. API Integration Pattern
- Centralized API service layer
- Async/await for API calls
- Error handling with try-catch
- Loading states during data fetch
- Example:
  ```javascript
  const fetchData = async () => {
      try {
          setLoading(true);
          const response = await apiService.getData();
          setData(response.data);
      } catch (error) {
          console.error('Error:', error);
      } finally {
          setLoading(false);
      }
  };
  ```

#### 5. Modal Management Pattern
- Boolean state for modal visibility
- Separate modal components
- Close handlers passed as props
- Example: `showChatModal`, `showCreditsModal`, `showBirthFormModal`

### Mobile Patterns (React Native)

#### 1. Animation Patterns
- Use Animated API for smooth transitions
- Stagger animations for list items
- Pulse effects for emphasis
- Example from codebase:
  ```javascript
  const fadeAnim = useRef(new Animated.Value(0)).current;
  
  Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
  }).start();
  ```

#### 2. Gradient Backgrounds
- LinearGradient for visual appeal
- Consistent color schemes across components
- Example: `['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']`

#### 3. Card-Based Layouts
- Glassmorphism effects with rgba backgrounds
- Border styling with transparency
- Shadow effects for depth
- Example:
  ```javascript
  backgroundColor: 'rgba(255, 255, 255, 0.1)',
  borderWidth: 1,
  borderColor: 'rgba(255, 255, 255, 0.2)',
  ```

#### 4. FlatList Optimization
- Horizontal scrolling for chips/cards
- keyExtractor for unique keys
- snapToInterval for pagination effect
- Example: Dasha chips display

#### 5. SVG for Custom Graphics
- Use react-native-svg for charts and diagrams
- Dynamic SVG generation based on data
- Example: Moon phase visualization, zodiac wheel

## Astrological Calculation Patterns

### 1. Swiss Ephemeris Integration
- Use pyswisseph for planetary calculations
- Lahiri Ayanamsa for Vedic astrology
- Precise degree calculations with decimal precision

### 2. Dasha System Calculations
- Vimshottari: 120-year cycle with planetary periods
- Chara: Sign-based progression
- Yogini: 8-planet cycle
- Kalachakra: Nakshatra-based with gati variations
- Pattern: Calculate mahadasha, then subdivide into antardashas

### 3. House System Analysis
- Whole sign houses for Vedic astrology
- House strength calculations (Shadbala, Ashtakavarga)
- House significations from classical texts
- Pattern: Analyze house lord, planets in house, aspects to house

### 4. Nakshatra Analysis
- 27 nakshatras with 4 padas each
- Nakshatra lord influences
- Specialized interpretations per nakshatra
- Pattern: Calculate nakshatra position, apply pada-specific meanings

### 5. Yoga Detection
- Rule-based system for yoga identification
- Multiple conditions must be satisfied
- Classical references for each yoga
- Pattern: Check planetary positions, aspects, house placements

## API Design Patterns

### 1. RESTful Endpoint Structure
- `/api/resource` for collections
- `/api/resource/{id}` for specific items
- POST for creation, GET for retrieval
- Consistent response format: `{ success: bool, data: object, error: string }`

### 2. Request Validation
- Pydantic models for request validation
- Type checking and field validation
- Clear error messages for invalid input
- Example:
  ```python
  class FeedbackRequest(BaseModel):
      message_id: str
      rating: int = Field(..., ge=1, le=5)
      comment: Optional[str] = None
  ```

### 3. Authentication Pattern
- JWT tokens for authentication
- Dependency injection for user verification
- Example: `current_user: User = Depends(get_current_user)`

### 4. Database Access Pattern
- SQLite with manual connection management
- Context managers for connection cleanup
- Parameterized queries to prevent SQL injection
- Example:
  ```python
  conn = sqlite3.connect('astrology.db')
  cursor = conn.cursor()
  try:
      cursor.execute("SELECT * FROM table WHERE id = ?", (id,))
      result = cursor.fetchone()
  finally:
      conn.close()
  ```

### 5. Error Response Pattern
- HTTPException for API errors
- Descriptive error messages
- Appropriate status codes (400, 403, 404, 500)
- Example:
  ```python
  raise HTTPException(status_code=404, detail="Resource not found")
  ```

## Testing and Debugging Patterns

### 1. Console Logging
- Strategic console.log/print statements for debugging
- Log API responses, state changes, calculation results
- Remove or comment out verbose logs in production

### 2. Error Boundaries
- Try-catch blocks around critical operations
- Graceful error handling with user-friendly messages
- Fallback UI for error states

### 3. Data Validation
- Validate birth data before calculations
- Check for required fields
- Provide clear error messages for missing data

### 4. Development vs Production
- Environment-based API URLs
- Conditional feature flags
- Debug mode for additional logging

## Performance Optimization Patterns

### 1. Memoization
- useCallback for function memoization
- useMemo for expensive calculations
- Prevent unnecessary re-renders

### 2. Lazy Loading
- Load components on demand
- Defer non-critical data fetching
- Progressive enhancement approach

### 3. Caching Strategies
- Cache API responses in state
- LocalStorage for persistent data
- AsyncStorage for mobile app data
- Example: Today's lucky data cached with date check

### 4. Efficient List Rendering
- FlatList with keyExtractor
- Virtual scrolling for long lists
- Pagination for large datasets

### 5. Image and Asset Optimization
- Use appropriate image formats
- Lazy load images
- Optimize SVG paths

## Security Best Practices

### 1. Authentication
- JWT tokens with expiration
- Secure token storage
- Token refresh mechanism

### 2. Data Encryption
- Encrypt sensitive birth chart data
- Use cryptography library for encryption
- Secure key management

### 3. Input Sanitization
- Validate all user inputs
- Parameterized database queries
- Escape special characters

### 4. API Security
- CORS configuration
- Rate limiting (where applicable)
- Authentication required for sensitive endpoints

## Astrological Domain Patterns

### 1. Planetary Significations
- Maintain comprehensive planetary meaning dictionaries
- Context-specific interpretations (career, health, wealth)
- Example:
  ```python
  planet_significations = {
      'Sun': 'government, authority, leadership, public service',
      'Moon': 'public relations, hospitality, healthcare, nurturing services'
  }
  ```

### 2. House Significations
- Multi-level signification structure (primary, secondary, tertiary)
- House-specific body parts, life areas, relationships
- Classical text references

### 3. Sign Characteristics
- Element associations (Fire, Earth, Air, Water)
- Modality (Cardinal, Fixed, Mutable)
- Ruling planets and natural significations

### 4. Aspect Calculations
- Vedic aspects (full, 3/4, 1/2, 1/4)
- Jaimini aspects (sign-based)
- Orb considerations for precision

### 5. Dasha-Transit Integration
- Combine dasha periods with current transits
- Activation detection when transit triggers natal position
- Multi-layered timing analysis

## Code Organization Principles

### 1. Separation of Concerns
- Calculators for astrological logic
- Routes for API endpoints
- Services for business logic
- Components for UI rendering

### 2. DRY (Don't Repeat Yourself)
- Extract common functionality into base classes
- Reusable utility functions
- Shared configuration dictionaries

### 3. Single Responsibility
- Each function/class has one clear purpose
- Focused components with specific roles
- Modular design for maintainability

### 4. Configuration Over Code
- Externalize rules and mappings
- Configuration dictionaries for astrological data
- Easy to update without code changes
- Example: `rules_config.py`, `profession_config.py`

### 5. Progressive Enhancement
- Core functionality works first
- Enhanced features added incrementally
- Graceful degradation when features unavailable

## Common Code Idioms

### Python Idioms
```python
# Dictionary comprehension for data transformation
sign_names = {i: name for i, name in enumerate(SIGN_NAMES)}

# List comprehension with filtering
current_dashas = [d for d in dashas if d.get('current')]

# Ternary operator for default values
value = data.get('key') or 'default'

# String formatting with f-strings
message = f"Your {planet} is in {sign} sign"

# Multiple assignment
start_date, end_date = period['start'], period['end']
```

### JavaScript/React Idioms
```javascript
// Destructuring props
const { birthData, chartData, onClose } = props;

// Spread operator for state updates
setData({ ...data, newField: value });

// Optional chaining
const value = data?.nested?.property;

// Array methods for data transformation
const names = items.map(item => item.name);
const filtered = items.filter(item => item.active);

// Template literals
const message = `Welcome, ${user.name}!`;
```

### React Native Idioms
```javascript
// Animated value interpolation
opacity: fadeAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1]
})

// Platform-specific code
Platform.OS === 'ios' ? iosStyle : androidStyle

// Conditional styling
style={[baseStyle, isActive && activeStyle]}

// FlatList renderItem pattern
renderItem={({ item, index }) => (
    <Component data={item} />
)}
```

## Astrological Accuracy Standards

### 1. Calculation Precision
- Use Swiss Ephemeris for planetary positions
- Lahiri Ayanamsa for Vedic calculations
- Decimal precision for degrees (e.g., 15.4°)
- Accurate timezone handling

### 2. Classical Text References
- Cite sources (BPHS, Jataka Parijata, Saravali)
- Follow traditional interpretation methods
- Maintain authenticity in predictions

### 3. Multi-System Synthesis
- Combine multiple dasha systems for confirmation
- Cross-reference divisional charts
- Integrate Ashtakavarga for strength analysis
- Use multiple calculation methods for validation

### 4. Context-Aware Interpretations
- Consider house placement, sign, nakshatra together
- Analyze conjunctions and aspects
- Account for planetary strength (Shadbala)
- Provide nuanced, not generic, predictions

### 5. Timing Accuracy
- Precise dasha period calculations
- Transit activation detection
- Muhurat calculations with location-specific data
- Real-time planetary position updates

## User Experience Patterns

### 1. Progressive Disclosure
- Show essential information first
- Expand details on demand
- Avoid overwhelming users with data

### 2. Loading States
- Show loading indicators during API calls
- Skeleton screens for better perceived performance
- Informative loading messages

### 3. Error Messaging
- User-friendly error messages
- Actionable error guidance
- Avoid technical jargon in user-facing errors

### 4. Responsive Design
- Mobile-first approach
- Flexible layouts that adapt to screen size
- Touch-friendly interactive elements

### 5. Visual Hierarchy
- Clear headings and sections
- Consistent spacing and alignment
- Color coding for different data types
- Icons and emojis for visual interest

## Deployment and Maintenance

### 1. Environment Configuration
- Separate dev and production configs
- Environment variables for sensitive data
- API URL configuration per environment

### 2. Database Management
- Regular backups of SQLite database
- Migration scripts for schema changes
- Data encryption for sensitive information

### 3. Logging and Monitoring
- Application logs for debugging
- Error tracking and reporting
- Performance monitoring

### 4. Version Control
- Meaningful commit messages
- Feature branches for development
- Code review before merging

### 5. Documentation
- README files for setup instructions
- API documentation (OpenAPI/Swagger)
- Code comments for complex logic
- Architecture documentation for new developers
