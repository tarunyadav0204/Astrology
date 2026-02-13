# Chat System Architecture Documentation

This document outlines the architecture of the asynchronous chat system, detailing the flow from a user's question to the final AI-generated response.

## Core Philosophy

The system is designed to be asynchronous, responsive, and intelligent. It handles potentially long-running astrological calculations in the background without blocking the user interface. It uses an initial, fast AI call for "intent routing" to understand the user's query, decide if clarification is needed, and determine the required type of analysis. This prevents expensive calculations for vague questions and creates a more natural conversational flow.

## High-Level Flow

1.  **Request & Queue**: The user submits a question. The system immediately acknowledges the request, creates a placeholder for the response, and returns a unique identifier (`message_id`).
2.  **Polling**: The frontend uses the `message_id` to periodically ask the server for the status of the response.
3.  **Background Processing**: A background task is initiated to handle the core logic:
    a. **Intent Routing**: A fast AI model classifies the user's question to determine its nature (e.g., career, marriage, annual forecast) and checks if it's specific enough to answer. This step can be bypassed for special modes.
    b. **Clarification (If Needed)**: If the question is too vague (e.g., "Tell me about my career"), the system asks a clarifying question. The process then waits for the user's answer.
    c. **Context Building**: Once the intent is clear, the system gathers all necessary astrological data. This is a computationally intensive step involving calculating planetary positions, dashas, divisional charts, transits, and more.
    d. **AI Analysis**: A comprehensive prompt, containing detailed system instructions and the complete astrological data, is sent to a powerful Gemini model for in-depth analysis.
    e. **Response & Storage**: The AI's response is received, parsed, and saved to the database. The status of the message is updated to `completed`.
4.  **Display**: On its next poll, the frontend receives the completed response and displays it to the user.
5.  **Learning**: Key facts from the conversation are extracted and stored to personalize future interactions.

## Key Components

### 1. Chat History API (`chat_history/routes.py`)

-   **Framework**: FastAPI.
-   **`POST /chat-v2/ask`**: The main entry point.
    -   Validates the request and checks user credits.
    -   Creates a `chat_messages` entry with a `processing` status.
    -   Spawns the `process_gemini_response` background task.
    -   Returns immediately with a `message_id`.
-   **`GET /chat-v2/status/{message_id}`**: The polling endpoint for the frontend to check if the response is ready.
-   **`process_gemini_response(...)`**: The orchestrator for the background chat logic. It calls the other components in sequence. It also detects the `@All_Events` trigger to activate the "Deep Dive" mode.

### 2. Intent Router (`ai/intent_router.py`)

-   **Model**: `gemini-2.5-flash` (optimized for speed).
-   **Purpose**: To quickly analyze the user's question *before* performing heavy calculations.
-   **Output**:
    -   `status`: `'READY'` or `'CLARIFY'`.
    -   `mode`: The type of analysis (e.g., `birth`, `annual`, `prashna`).
    -   `category`: The topic (e.g., `job`, `love`, `health`).
    -   `needs_transits`: A boolean indicating if transit calculations are required.
    -   `divisional_charts`: A list of required D-charts (e.g., `D9`, `D10`).
    -   `clarification_question`: A question to ask the user if the query is too vague.
-   **`force_ready` Parameter**: A new boolean parameter that, when true, forces the router to bypass clarification and return a `READY` status. This is used for the "Deep Dive" mode.

### 3. Chat Context Builder (`chat/chat_context_builder.py`)

-   **Purpose**: The primary data aggregation module. It builds the complete astrological dataset required for the analysis.
-   **Process**:
    -   It uses numerous specialized calculator modules (e.g., `ChartCalculator`, `DashaCalculator`, `RealTransitCalculator`, `YogaCalculator`).
    -   It generates a comprehensive JSON object containing all astrological data.
-   **Caching**: Implements `static_cache` (for birth data) and `dynamic_cache` (for date-specific data) to optimize performance for repeated queries.

### 4. Gemini Chat Analyzer (`ai/gemini_chat_analyzer.py`)

-   **Model**: `gemini-3-flash-preview` or a similar powerful model.
-   **Purpose**: To generate the final, detailed astrological analysis and response.
-   **`_create_chat_prompt`**: This method is now a lightweight wrapper that calls the centralized `build_final_prompt` function in `ai/output_schema.py`.
-   **`generate_chat_response`**: Makes the asynchronous call to the Gemini API, handles errors, and parses the final response. It now accepts a `mode` parameter to select the appropriate output schema (e.g., `'default'` or `'deep_dive'`).

### 5. Output Schema (`ai/output_schema.py`)

-   **Purpose**: Provides a single source of truth for all prompt engineering, including response formats and system instructions.
-   **`build_final_prompt()`**: A new centralized function that constructs the entire prompt sent to the Gemini model. It takes various parameters like the user's question, astrological context, and the analysis `mode` to assemble the final prompt.
-   **`get_output_schema()`**: Returns the standard response structure.
-   **`get_deep_dive_output_schema()`**: Returns the new, exhaustive event log structure for the "Deep Dive" mode.

### 6. Structured Analyzer (`ai/structured_analyzer.py`)

-   An alternative analyzer designed to receive a pure JSON object from the AI, instead of formatted text. This is likely used for specific backend tasks or features that require structured data without a conversational wrapper.

## Special Modes

### "Deep Dive" Mode

-   **Trigger**: Activated by starting the user's question with the phrase `@All_Events`.
-   **Purpose**: To generate an exhaustive, detailed log of all possible astrological events for a given period, intended for expert users or family members.
-   **Behavior**:
    1.  The `@All_Events` trigger is detected in `chat_history/routes.py`.
    2.  A `force_ready=True` flag is passed to the `IntentRouter`, which prevents it from asking for clarification.
    3.  A `mode='deep_dive'` flag is passed to the `GeminiChatAnalyzer`.
    4.  The `build_final_prompt` function in `ai/output_schema.py` selects the `get_deep_dive_output_schema`, instructing the AI to generate a detailed event log with 40-50+ entries.
    5.  The final output is a raw, chronological log of events with detailed astrological reasoning, rather than a user-friendly summary.

## Data Flow Diagram

```
[Frontend] --(POST /ask, includes optional @All_Events)--> [API: routes.py]
    |                                                              |
    '----(GET /status)--->'                                        | (Spawns Background Task)
                                                                   v
                                                     [process_gemini_response]
                                                                   |
                                                                   v
                                                     [IntentRouter.classify_intent] --(force_ready=True if @All_Events)--> [Bypasses Clarification]
                                                                   |
                                                                   v
                                                     [ChatContextBuilder.build_context] --(Gathers ALL astro data)--> [Massive JSON Context]
                                                                   |
                                                                   v
                                                     [GeminiChatAnalyzer.generate_chat_response(mode='deep_dive')]
                                                                   |
                                                                   v
                                                     [output_schema.build_final_prompt] --(Selects deep_dive schema)--> [Final Prompt]
                                                                   |
                                                                   v
                                                               [Gemini API]
                                                                   |
                                                                   v
                                                     [Receives AI Response] --(Parses & Saves)--> [Update DB: status='completed']
                                                                   |
'--(Frontend receives completed response on next poll) <--------------------------------------------------------------------'
```