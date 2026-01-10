"""
Karma Analysis Routes - API endpoints for past life karma analysis
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import os
import sys
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import get_current_user, User
from calculators.karma_context_builder import KarmaContextBuilder
from ai.karma_gemini_analyzer import KarmaGeminiAnalyzer
from credits.credit_service import CreditService

load_dotenv()

router = APIRouter()
credit_service = CreditService()

class KarmaAnalysisRequest(BaseModel):
    chart_id: str

def process_karma_analysis_background(chart_id: str, user_id: int, birth_data: dict, karma_cost: int):
    """Background task to process karma analysis"""
    try:
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'astrology.db'))
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE karma_insights SET status = 'processing', updated_at = CURRENT_TIMESTAMP WHERE chart_id = ? AND user_id = ?",
            (chart_id, user_id)
        )
        conn.commit()
        
        print(f"\n{'='*80}")
        print(f"🔮 KARMA ANALYSIS REQUEST - Chart ID: {chart_id}")
        print(f"{'='*80}")
        
        # Calculate chart from birth data
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        from calculators.chart_calculator import ChartCalculator
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Calculate divisional charts
        from calculators.divisional_chart_calculator import DivisionalChartCalculator
        div_calc = DivisionalChartCalculator(chart_data)
        d9_result = div_calc.calculate_divisional_chart(9)
        d60_result = div_calc.calculate_divisional_chart(60)
        
        # Extract divisional_chart data from wrapper
        divisional_charts = {
            'd9_navamsa': d9_result['divisional_chart'],
            'd60_shashtiamsa': d60_result['divisional_chart']
        }
        
        api_key = os.getenv('GEMINI_API_KEY')
        analyzer = KarmaGeminiAnalyzer(api_key)
        analysis = analyzer.analyze_karma(chart_data, divisional_charts, native_name=birth_data.get('name', 'the native'), log_request=True)
        
        print(f"\n{'='*80}")
        print(f"✅ KARMA ANALYSIS RESPONSE")
        print(f"{'='*80}")
        print(f"Success: {analysis.get('success')}")
        if analysis.get('success'):
            print(f"Sections count: {len(analysis.get('sections', {}))}")
            print(f"AI interpretation length: {len(analysis.get('ai_interpretation', ''))} chars")
        else:
            print(f"Error: {analysis.get('error')}")
        print(f"{'='*80}\n")
        
        if analysis['success']:
            cursor.execute(
                """UPDATE karma_insights 
                   SET status = 'complete', 
                       karma_context = ?, 
                       ai_interpretation = ?, 
                       sections = ?,
                       updated_at = CURRENT_TIMESTAMP 
                   WHERE chart_id = ? AND user_id = ?""",
                (
                    json.dumps(analysis['karma_context']),
                    analysis['ai_interpretation'],
                    json.dumps(analysis['sections']),
                    chart_id,
                    user_id
                )
            )
            conn.commit()
            
            # Deduct credits only on successful analysis
            print(f"💰 Deducting {karma_cost} credits for successful analysis")
            credit_service.spend_credits(
                user_id,
                karma_cost,
                'karma_analysis',
                f"Karma analysis for chart {chart_id}"
            )
        else:
            cursor.execute(
                "UPDATE karma_insights SET status = 'error', error = ?, updated_at = CURRENT_TIMESTAMP WHERE chart_id = ? AND user_id = ?",
                (analysis.get('error', 'Unknown error'), chart_id, user_id)
            )
            conn.commit()
            print(f"⚠️ Analysis failed - no credits deducted")
        conn.close()
        
    except Exception as e:
        print(f"\n❌ KARMA ANALYSIS BACKGROUND ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'astrology.db'))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE karma_insights SET status = 'error', error = ?, updated_at = CURRENT_TIMESTAMP WHERE chart_id = ? AND user_id = ?",
            (str(e), chart_id, user_id)
        )
        conn.commit()
        conn.close()
        print(f"⚠️ Exception occurred - no credits deducted")

@router.post("/karma-analysis")
async def analyze_karma(request: KarmaAnalysisRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), force_regenerate: bool = False):
    """Initiate karma analysis - returns immediately, processing happens in background"""
    print(f"\n{'='*80}")
    print(f"📥 KARMA ANALYSIS ENDPOINT CALLED")
    print(f"Chart ID: {request.chart_id}")
    print(f"User ID: {current_user.userid}")
    print(f"Force Regenerate: {force_regenerate}")
    print(f"{'='*80}\n")
    
    try:
        karma_cost = credit_service.get_credit_setting('karma_analysis_cost') or 25
        user_balance = credit_service.get_user_credits(current_user.userid)
        
        print(f"💳 Credits check: User has {user_balance}, needs {karma_cost}")
        
        if user_balance < karma_cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {karma_cost} credits but have {user_balance}."
            )
        
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'astrology.db'))
        cursor = conn.cursor()
        
        print(f"🔍 Fetching chart data for chart_id={request.chart_id}, user_id={current_user.userid}")
        
        cursor.execute(
            "SELECT name, date, time, latitude, longitude, timezone, place, gender FROM birth_charts WHERE id = ? AND userid = ?",
            (request.chart_id, current_user.userid)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            print(f"❌ Chart not found")
            raise HTTPException(status_code=404, detail="Chart not found")
        
        print(f"✅ Chart data found")
        
        # Decrypt all encrypted fields
        from encryption_utils import EncryptionManager
        try:
            encryptor = EncryptionManager()
        except ValueError:
            encryptor = None
        
        if encryptor:
            chart_data = {
                'name': encryptor.decrypt(result[0]),
                'date': encryptor.decrypt(result[1]),
                'time': encryptor.decrypt(result[2]),
                'latitude': float(encryptor.decrypt(str(result[3]))),
                'longitude': float(encryptor.decrypt(str(result[4]))),
                'timezone': result[5],
                'place': encryptor.decrypt(result[6] or ''),
                'gender': result[7] or ''
            }
        else:
            chart_data = {
                'name': result[0],
                'date': result[1],
                'time': result[2],
                'latitude': result[3],
                'longitude': result[4],
                'timezone': result[5],
                'place': result[6] or '',
                'gender': result[7] or ''
            }
        divisional_charts = None  # Will be calculated by KarmaContextBuilder
        
        cursor.execute(
            "SELECT status, karma_context, ai_interpretation, sections, error FROM karma_insights WHERE chart_id = ? AND user_id = ?",
            (request.chart_id, current_user.userid)
        )
        existing = cursor.fetchone()
        
        if existing and existing[0] == 'complete' and not force_regenerate:
            conn.close()
            print(f"✅ Returning cached result")
            return {
                "status": "complete",
                "data": {
                    "karma_context": json.loads(existing[1]),
                    "ai_interpretation": existing[2],
                    "sections": json.loads(existing[3])
                },
                "cached": True
            }
        
        print(f"📝 Creating new karma_insights entry")
        
        cursor.execute(
            """INSERT OR REPLACE INTO karma_insights 
               (chart_id, user_id, status, created_at, updated_at) 
               VALUES (?, ?, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (request.chart_id, current_user.userid)
        )
        conn.commit()
        conn.close()
        
        print(f"🚀 Starting background task (credits will be deducted on success)")
        
        background_tasks.add_task(
            process_karma_analysis_background,
            request.chart_id,
            current_user.userid,
            chart_data,
            karma_cost
        )
        
        print(f"✅ Returning pending status\n")
        
        return {
            "status": "pending",
            "message": "Analysis started. Use /karma-analysis/status to check progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ KARMA ANALYSIS ENDPOINT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/karma-analysis/status")
async def get_karma_status(chart_id: str, current_user: User = Depends(get_current_user)):
    """Check status of karma analysis"""
    try:
        conn = sqlite3.connect(os.getenv('DATABASE_PATH', 'astrology.db'))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT status, karma_context, ai_interpretation, sections, error FROM karma_insights WHERE chart_id = ? AND user_id = ?",
            (chart_id, current_user.userid)
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {"status": "not_found"}
        
        status = result[0]
        
        if status == 'complete':
            return {
                "status": "complete",
                "data": {
                    "karma_context": json.loads(result[1]),
                    "ai_interpretation": result[2],
                    "sections": json.loads(result[3])
                }
            }
        elif status == 'error':
            return {
                "status": "error",
                "error": result[4]
            }
        else:
            return {"status": status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
