# Release Notes - v1.5.0

## 🎯 Major Features

### 1. Chara Dasha System
- **Full Chara Dasha Implementation**: Added complete Chara Dasha calculation system with all 12 signs
- **Multi-Level Periods**: Support for Mahadasha, Antardasha, Pratyantardasha, Sookshma, and Prana levels
- **Interactive Dasha Browser**: Navigate through all dasha periods with expandable sub-periods
- **Chat Integration**: Ask questions about Chara Dasha periods directly in chat (e.g., "Tell me about my Chara Dasha")
- **Current Period Highlighting**: Automatically identifies and highlights currently running dashas

### 2. Conversational Chat Intelligence
- **Smart Clarification System**: AI asks contextual follow-up questions (max 2) for vague queries
  - Example: "How is my 2026?" → AI asks which life area to focus on
  - Example: "Tell me about my kids" → AI asks about number of children and specific concerns
- **Semantic Memory**: Stores user facts across sessions per birth chart
  - Remembers family details, career status, preferences, and major life events
  - 8 fact categories: career, family, health, location, preferences, education, relationships, major_events
- **Context-Aware Responses**: Uses stored facts to provide personalized insights without repetitive questions
- **Clarification UI**: Special yellow/orange styling for clarification messages with ❓ icon

### 3. Mobile App Enhancements
- **Conversational Chat**: Full feature parity with web app for clarifications and memory
- **Credit Auto-Refresh**: Credits now update automatically in chat screen after responses
- **Improved UX**: Clarification messages display with distinct styling on mobile

## 🐛 Bug Fixes
- Fixed Yogini Dasha subdasha display issue where antardashas weren't showing
- Resolved database lock errors during fact extraction
- Fixed duplicate intent router calls overwriting clarification status
- Corrected credit refresh issue in mobile app Credits screen

## 🔧 Technical Improvements
- Moved fact extraction outside main transaction to prevent database locks
- Added clarification count reset logic for new questions
- Enhanced intent router to recognize clarification responses vs new questions
- Optimized chat response polling with proper state management

## 📝 Database Changes
- Added `message_type` column to `chat_messages` table
- Created `conversation_state` table for tracking clarifications
- Created `user_facts` table for semantic memory storage
- Added indexes for performance optimization

---

**Note**: All backend changes automatically work for mobile app since it uses the same API endpoints.
