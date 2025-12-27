import os
import json
import logging
import traceback
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_paths = [
    '.env',
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    '/home/tarun_yadav/AstrologyApp/backend/.env'
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment from: {env_path}")
        break

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlankChartGeminiPredictor:
    """Gemini AI predictor for blank chart context with comprehensive error handling"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        print(f"🔑 GEMINI_API_KEY present: {bool(self.api_key)}")
        print(f"🔑 GEMINI_API_KEY length: {len(self.api_key) if self.api_key else 0}")
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize model with fallback options
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model with fallback options"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Try different model versions in order of preference (same as chat analyzer)
            model_names = [
                'models/gemini-3-pro-preview',  # Premium model first
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash-exp',
                'models/gemini-2.0-flash',
                'models/gemini-1.5-flash',
                'models/gemini-flash-latest'
            ]
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Initialized Gemini model: {model_name}")
                    print(f"✅ Initialized Gemini model: {model_name}")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Model {model_name} not available: {e}")
                    print(f"⚠️ Model {model_name} not available: {e}")
                    continue
            
            if not self.model:
                raise ValueError("No available Gemini model found")
                
        except ImportError as e:
            logger.error(f"Failed to import google.generativeai: {e}")
            raise ValueError(f"Google Generative AI library not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise ValueError(f"Failed to initialize Gemini model: {e}")
    
    def generate_prediction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI prediction from blank chart context with comprehensive error handling"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            logger.info(f"🚀 Starting blank chart prediction generation at {timestamp}")
            print(f"🚀 Starting blank chart prediction generation at {timestamp}")
            
            # Log context structure
            logger.info(f"📊 Context keys: {list(context.keys())}")
            print(f"📊 Context keys: {list(context.keys())}")
            
            if 'pillars' in context:
                pillars = context['pillars']
                logger.info(f"📊 Pillars available: {list(pillars.keys())}")
                print(f"📊 Pillars available: {list(pillars.keys())}")
            
            # Build prompt
            prompt = self._build_prediction_prompt(context)
            logger.info(f"📝 Generated prompt length: {len(prompt)} characters")
            print(f"📝 Generated prompt length: {len(prompt)} characters")
            
            # Log prompt to file for debugging
            self._log_to_file(f"blank_chart_prompt_{timestamp}.txt", prompt)
            
            # Call Gemini API
            logger.info("🤖 Calling Gemini API...")
            print("🤖 Calling Gemini API...")
            
            response = self.model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text') or not response.text:
                logger.error("❌ Empty response from Gemini API")
                print("❌ Empty response from Gemini API")
                return {
                    "success": False,
                    "error": "Empty response from Gemini API",
                    "fallback_prediction": self._get_fallback_prediction(context)
                }
            
            response_text = response.text.strip()
            logger.info(f"✅ Received response length: {len(response_text)} characters")
            print(f"✅ Received response length: {len(response_text)} characters")
            
            # Log response to file for debugging
            self._log_to_file(f"blank_chart_response_{timestamp}.txt", response_text)
            
            return {
                "success": True,
                "prediction": response_text,
                "confidence": "High",
                "timestamp": timestamp
            }
            
        except ImportError as e:
            error_msg = f"Google Generative AI library not available: {e}"
            logger.error(f"❌ Import error: {error_msg}")
            print(f"❌ Import error: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "fallback_prediction": self._get_fallback_prediction(context)
            }
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            stack_trace = traceback.format_exc()
            
            logger.error(f"❌ Prediction generation failed: {error_type}: {error_msg}")
            logger.error(f"❌ Stack trace: {stack_trace}")
            print(f"❌ Prediction generation failed: {error_type}: {error_msg}")
            print(f"❌ Stack trace: {stack_trace}")
            
            # Log error details to file
            error_log = f"ERROR: {error_type}: {error_msg}\n\nSTACK TRACE:\n{stack_trace}"
            self._log_to_file(f"blank_chart_error_{timestamp}.txt", error_log)
            
            # Provide specific error messages based on error type
            if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                user_error = "API quota exceeded. Please try again later."
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                user_error = "API authentication failed. Please check configuration."
            elif "timeout" in error_msg.lower():
                user_error = "Request timed out. Please try again."
            else:
                user_error = f"Prediction generation failed: {error_msg}"
            
            return {
                "success": False,
                "error": user_error,
                "error_type": error_type,
                "fallback_prediction": self._get_fallback_prediction(context)
            }
    
    def generate_quick_insight(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quick AI insight from blank chart context with comprehensive error handling"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            logger.info(f"🚀 Starting quick insight generation at {timestamp}")
            print(f"🚀 Starting quick insight generation at {timestamp}")
            
            prompt = self._build_quick_insight_prompt(context)
            logger.info(f"📝 Generated quick insight prompt length: {len(prompt)} characters")
            print(f"📝 Generated quick insight prompt length: {len(prompt)} characters")
            
            # Log prompt to file
            self._log_to_file(f"blank_chart_quick_prompt_{timestamp}.txt", prompt)
            
            response = self.model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text') or not response.text:
                logger.error("❌ Empty response from Gemini API for quick insight")
                print("❌ Empty response from Gemini API for quick insight")
                return {
                    "success": False,
                    "error": "Empty response from Gemini API",
                    "insight": self._get_fallback_insight(context)
                }
            
            response_text = response.text.strip()
            logger.info(f"✅ Received quick insight response length: {len(response_text)} characters")
            print(f"✅ Received quick insight response length: {len(response_text)} characters")
            
            # Log response to file
            self._log_to_file(f"blank_chart_quick_response_{timestamp}.txt", response_text)
            
            return {
                "success": True,
                "insight": response_text,
                "confidence": "99%",
                "timestamp": timestamp
            }
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            stack_trace = traceback.format_exc()
            
            logger.error(f"❌ Quick insight generation failed: {error_type}: {error_msg}")
            logger.error(f"❌ Stack trace: {stack_trace}")
            print(f"❌ Quick insight generation failed: {error_type}: {error_msg}")
            print(f"❌ Stack trace: {stack_trace}")
            
            # Log error to file
            error_log = f"ERROR: {error_type}: {error_msg}\n\nSTACK TRACE:\n{stack_trace}"
            self._log_to_file(f"blank_chart_quick_error_{timestamp}.txt", error_log)
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "insight": self._get_fallback_insight(context)
            }
    
    def _log_to_file(self, filename: str, content: str):
        """Log content to file for debugging"""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'blank_chart_logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, filename)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'='*80}\n")
                f.write(content)
            
            logger.info(f"📝 Logged to file: {log_file}")
            print(f"📝 Logged to file: {log_file}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to log to file {filename}: {e}")
            print(f"⚠️ Failed to log to file {filename}: {e}")
    
    def _build_prediction_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prediction prompt for Gemini"""
        pillars = context.get('pillars', {})
        metadata = context.get('metadata', {})
        age = metadata.get('target_age', 25)
        
        prompt = f"""You are a master Vedic astrologer specializing in STUNNING PREDICTIONS from classical texts. Generate SPECIFIC, FACTUAL predictions - NOT general descriptions.

IMPORTANT: Make CONCRETE predictions like:
- "Your house is a corner house" (Lal Kitab style)
- "You will fall ill at age 40" (BCP style)
- "You have 2 brothers and 1 sister" (specific family structure)
- "Your father works in government" (specific career)
- "You will get married in 2025" (exact timing)
- "You live on the 3rd floor" (physical details)
- "Your kitchen faces east" (house layout)
- "You have a mole on your left shoulder" (physical marks)

DO NOT give philosophical descriptions. Give STUNNING FACTUAL PREDICTIONS.

PERSON'S AGE: {age} years old

BHRIGU CHAKRA PADDHATI (BCP) - Make specific age-based predictions:
{json.dumps(pillars.get('bcp_activation', {}), indent=2)}

NAKSHATRA TRIGGERS - Predict exact events and timing:
{json.dumps(pillars.get('nakshatra_triggers', {}), indent=2)}

LAL KITAB ANCESTRAL DEBTS - Predict physical manifestations:
{json.dumps(pillars.get('lal_kitab_layer', {}), indent=2)}

SUDARSHANA CHAKRA - Predict personality and life facts:
{json.dumps(pillars.get('sudarshana_chakra', {}), indent=2)}

ELEMENTAL CLUSTERS - Predict temperament specifics:
{json.dumps(pillars.get('nadi_elemental_links', {}), indent=2)}

STUN FACTORS: {context.get('stun_factors', [])}

GENERATE STUNNING PREDICTIONS:

**1. BCP House Activation Predictions:**
- Predict SPECIFIC events that will happen at this age
- Give EXACT timing (months, years)
- Predict health issues, career changes, marriage timing

**2. Lal Kitab Physical Manifestations:**
- Predict house type (corner, middle, apartment)
- Predict family structure (number of siblings, parents' jobs)
- Predict physical features (marks, scars, appearance)
- Predict ancestral property details

**3. Nakshatra Fated Events:**
- Predict EXACT life events in fated years
- Give specific dates or age ranges
- Predict sudden changes, opportunities, challenges

**4. Family & Relationships:**
- Predict spouse's profession and appearance
- Predict number of children and their genders
- Predict relationship with parents and siblings

**5. Career & Wealth:**
- Predict specific job changes with timing
- Predict income levels and wealth accumulation
- Predict business success or failure

**6. Health & Physical:**
- Predict specific health issues with age
- Predict accidents or surgeries
- Predict physical changes

Format as stunning, specific predictions that would amaze the person with their accuracy. Use classical Vedic techniques to make factual statements, not general advice."""

        return prompt
    
    def _build_quick_insight_prompt(self, context: Dict[str, Any]) -> str:
        """Build quick insight prompt for Gemini"""
        pillars = context.get('pillars', {})
        metadata = context.get('metadata', {})
        age = metadata.get('target_age', 25)
        stun_factors = context.get('stun_factors', [])
        
        # Get most important elements
        bcp = pillars.get('bcp_activation', {})
        nakshatra = pillars.get('nakshatra_triggers', {})
        debts = pillars.get('lal_kitab_layer', {}).get('ancestral_debts', [])
        
        prompt = f"""You are a master Vedic astrologer. Use classical techniques from proven texts to give ONE powerful insight.

REFERENCE METHODS:
- Bhrigu Chakra Paddhati (Bhrigu Samhita)
- Nakshatra fated years (Nadi texts)
- Lal Kitab karmic analysis

KEY DATA for {age}-year-old:
- BCP Active House: {bcp.get('activated_house')} ({bcp.get('house_meaning')})
- Birth Star: {nakshatra.get('birth_star')}
- Fated Period: {nakshatra.get('is_fated_period')}
- Ancestral Debts: {len(debts)} detected
- Classical Indicators: {stun_factors}

Use ONLY Bhrigu Samhita BCP principles and Nadi timing methods. Provide ONE stunning insight (2-3 sentences) based on these classical techniques."""

        return prompt
    
    def _get_fallback_prediction(self, context: Dict[str, Any]) -> str:
        """Fallback prediction if Gemini fails"""
        try:
            pillars = context.get('pillars', {})
            age = context.get('metadata', {}).get('target_age', 25)
            
            bcp = pillars.get('bcp_activation', {})
            house = bcp.get('activated_house', 1)
            meaning = bcp.get('house_meaning', 'transformation')
            
            # Enhanced fallback with more context
            nakshatra_data = pillars.get('nakshatra_triggers', {})
            birth_star = nakshatra_data.get('birth_star', 'Unknown')
            is_fated = nakshatra_data.get('is_fated_period', False)
            
            fallback = f"At age {age}, you are in a {meaning.lower()} focused period. Your {house}th house is cosmically activated, bringing significant changes in this life area."
            
            if birth_star != 'Unknown':
                fallback += f" Born under {birth_star} nakshatra, "
                if is_fated:
                    fallback += "you are currently in a fated period where destiny accelerates."
                else:
                    fallback += "your natural talents are ready to manifest."
            
            return fallback
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback prediction generation failed: {e}")
            return f"You are in a significant life period with important cosmic influences at play."
    
    def _get_fallback_insight(self, context: Dict[str, Any]) -> str:
        """Fallback insight if Gemini fails"""
        try:
            age = context.get('metadata', {}).get('target_age', 25)
            stun_factors = context.get('stun_factors', [])
            
            if stun_factors:
                return f"At age {age}, you have {len(stun_factors)} major cosmic activations occurring simultaneously. This is a powerful time for transformation and growth."
            
            return f"Your {age}th year marks a significant turning point in your life's journey. The cosmic energies are aligning to support your evolution."
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback insight generation failed: {e}")
            return "You are in a cosmically significant period with important opportunities for growth and transformation."
    
    def test_gemini_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection and configuration"""
        try:
            logger.info("🧪 Testing Gemini API connection...")
            print("🧪 Testing Gemini API connection...")
            
            # Simple test prompt
            test_prompt = "Hello, this is a test. Please respond with 'Connection successful'."
            
            response = self.model.generate_content(test_prompt)
            
            if response and hasattr(response, 'text') and response.text:
                logger.info(f"✅ Gemini API test successful: {response.text[:100]}...")
                print(f"✅ Gemini API test successful: {response.text[:100]}...")
                return {
                    "success": True,
                    "message": "Gemini API connection successful",
                    "response": response.text
                }
            else:
                logger.error("❌ Gemini API test failed: Empty response")
                print("❌ Gemini API test failed: Empty response")
                return {
                    "success": False,
                    "error": "Empty response from Gemini API"
                }
                
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"❌ Gemini API test failed: {error_type}: {error_msg}")
            print(f"❌ Gemini API test failed: {error_type}: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type
            }