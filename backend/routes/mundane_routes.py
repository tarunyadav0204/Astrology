from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from auth import get_current_user
from calculators.mundane.mundane_context_builder import MundaneContextBuilder
from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from db import get_conn, execute

router = APIRouter()


class MundaneRequest(BaseModel):
    session_id: str
    country: str
    year: Optional[int] = None
    latitude: float
    longitude: float
    question: str
    category: Optional[str] = "general" # e.g., "sports", "markets", "wars", "general"
    event_date: Optional[str] = None    # YYYY-MM-DD
    event_time: Optional[str] = None    # HH:MM:SS
    entities: Optional[list[str]] = None # list of countries/teams/indices

@router.post("/api/mundane/session")
async def create_mundane_session(request: dict, current_user = Depends(get_current_user)):
    """Create a new mundane chat session"""
    import uuid
    session_id = str(uuid.uuid4())

    with get_conn() as conn:
        execute(
            conn,
            "INSERT INTO chat_sessions (session_id, user_id, birth_chart_id) VALUES (%s, %s, %s)",
            (session_id, current_user.userid, None),  # No birth_chart_id for mundane
        )
        conn.commit()

    return {"session_id": session_id}

@router.post("/api/mundane/analyze")
async def analyze_mundane(request: MundaneRequest, background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Start async mundane analysis - returns immediately with message_id for polling"""
    from credits.credit_service import CreditService
    
    # Extract year from question if not provided
    year = request.year
    if not year:
        import re
        year_match = re.search(r'\b(20\d{2})\b', request.question)
        year = int(year_match.group(1)) if year_match else datetime.now().year
    
    # Check credits (subscription tier discount applied)
    credit_service = CreditService()
    base_cost = credit_service.get_credit_setting('chat_question_cost')
    chat_cost = credit_service.get_effective_cost(current_user.userid, base_cost, 'chat_question_cost')
    user_balance = credit_service.get_user_credits(current_user.userid)
    
    if user_balance < chat_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You need {chat_cost} credits but have {user_balance}."
        )
    
    with get_conn() as conn:
        # Verify session belongs to user
        cur = execute(
            conn,
            "SELECT user_id FROM chat_sessions WHERE session_id = %s",
            (request.session_id,),
        )
        session = cur.fetchone()
        if not session or session[0] != current_user.userid:
            raise HTTPException(status_code=404, detail="Session not found")

        # Save user question
        cur = execute(
            conn,
            """
            INSERT INTO chat_messages (session_id, sender, content, status, completed_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING message_id
            """,
            (request.session_id, "user", request.question, "completed", datetime.now()),
        )

        # Create processing assistant message
        cur = execute(
            conn,
            """
            INSERT INTO chat_messages (session_id, sender, content, status, started_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING message_id
            """,
            (request.session_id, "assistant", "", "processing", datetime.now()),
        )
        row = cur.fetchone()
        message_id = row[0] if row else None
        conn.commit()

    # Start background processing
    background_tasks.add_task(
        process_mundane_response,
        message_id, request.session_id, request.question, request.country, year,
        request.latitude, request.longitude, current_user.userid, chat_cost,
        request.category, request.event_date, request.event_time, request.entities
    )
    
    return {
        "message_id": message_id,
        "status": "processing",
        "message": "Analyzing global trends..."
    }

async def process_mundane_response(
    message_id: int, session_id: str, question: str, country: str, year: int,
    latitude: float, longitude: float, user_id: int, chat_cost: int,
    category: str = "general", event_date: str = None, event_time: str = None, entities: list = None
):
    """Background task to process mundane analysis"""
    try:
        print(f"\n📅 Analyzing {category} for {country} (User asked: '{question}')")

        # Build lightweight conversation history (last 3 Q&A) for this mundane session
        history = []
        try:
            with get_conn() as conn:
                cur = execute(
                    conn,
                    """
                    SELECT message_id, sender, content, timestamp
                    FROM chat_messages
                    WHERE session_id = %s AND message_id < %s
                    ORDER BY timestamp ASC, message_id ASC
                    """,
                    (session_id, message_id),
                )
                rows = cur.fetchall() or []

            # Pair user/assistant messages into simple Q&A objects
            pending_question = None
            for mid, sender, content, ts in rows:
                if sender == "user":
                    # Start a new question; if there was an unanswered one, drop it
                    pending_question = content or ""
                elif sender == "assistant" and pending_question:
                    # Pair this assistant reply with the last user question
                    history.append(
                        {
                            "question": (pending_question or "")[:500],
                            "response": (content or "")[:500],
                        }
                    )
                    pending_question = None

            # Keep only the last 3 Q&A pairs
            if len(history) > 3:
                history = history[-3:]

            print(f"🧵 Mundane history pairs for Gemini: {len(history)}")
        except Exception as e:
            # History is optional; log and continue on failure
            print(f"⚠️ Failed to build mundane history context: {e}")
            history = []

        builder = MundaneContextBuilder()
        context = builder.build_mundane_context(
            country_name=country,
            year=year,
            latitude=latitude,
            longitude=longitude,
            category=category,
            event_date=event_date,
            event_time=event_time,
            entities=entities
        )
        context['analysis_type'] = 'mundane'
        
        gemini = GeminiChatAnalyzer()
        result = await gemini.generate_chat_response(
            user_question=question,
            astrological_context=context,
            conversation_history=history,
            language='english',
            response_style='detailed',
            user_id=user_id,
        )
        
        # Update database with result
        from credits.credit_service import CreditService

        credit_service = CreditService()
        with get_conn() as conn:
            if result.get("success"):
                # Deduct credits
                success = credit_service.spend_credits(
                    user_id,
                    chat_cost,
                    "mundane_analysis",
                    f"Mundane: {country} {year}",
                )

                if success:
                    execute(
                        conn,
                        """
                        UPDATE chat_messages
                        SET content = %s, status = %s, completed_at = %s
                        WHERE message_id = %s
                        """,
                        (result["response"], "completed", datetime.now(), message_id),
                    )
                else:
                    execute(
                        conn,
                        """
                        UPDATE chat_messages
                        SET status = %s, error_message = %s, completed_at = %s
                        WHERE message_id = %s
                        """,
                        ("failed", "Credit deduction failed", datetime.now(), message_id),
                    )
            else:
                execute(
                    conn,
                    """
                    UPDATE chat_messages
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE message_id = %s
                    """,
                    (
                        "failed",
                        result.get("error", "Analysis failed"),
                        datetime.now(),
                        message_id,
                    ),
                )
            conn.commit()

    except Exception as e:
        import traceback
        print(f"❌ Mundane Analysis Error: {str(e)}")
        print(traceback.format_exc())
        
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE chat_messages
                SET status = %s, error_message = %s, completed_at = %s
                WHERE message_id = %s
                """,
                ("failed", "Analysis failed. Please try again.", datetime.now(), message_id),
            )
            conn.commit()
