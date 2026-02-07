import pytest
from unittest.mock import patch, MagicMock
from backend.chat.system_instruction_config import build_system_instruction, EVENT_PREDICTION_MULTIPLE_STRUCTURE, EVENT_PREDICTION_SINGLE_STRUCTURE, ROOT_CAUSE_ANALYSIS_STRUCTURE, GENERAL_ADVICE_STRUCTURE, CHART_ANALYSIS_STRUCTURE
from backend.ai.gemini_chat_analyzer import GeminiChatAnalyzer
from backend.chat.chat_context_builder import ChatContextBuilder

@pytest.mark.parametrize("analysis_type, expected_structure", [
    ("EVENT_PREDICTION_MULTIPLE", EVENT_PREDICTION_MULTIPLE_STRUCTURE),
    ("EVENT_PREDICTION_SINGLE", EVENT_PREDICTION_SINGLE_STRUCTURE),
    ("ROOT_CAUSE_ANALYSIS", ROOT_CAUSE_ANALYSIS_STRUCTURE),
    ("REMEDIAL_GUIDANCE", GENERAL_ADVICE_STRUCTURE),
    ("CHARACTER_ANALYSIS", CHART_ANALYSIS_STRUCTURE),
    (None, CHART_ANALYSIS_STRUCTURE), # Default case
])
def test_build_system_instruction_selects_correct_structure(analysis_type, expected_structure):
    """
    Tests if the build_system_instruction function correctly selects the
    main response structure based on the provided analysis_type.
    """
    intent_category = "career"
    instruction = build_system_instruction(analysis_type=analysis_type, intent_category=intent_category)

    # Check that the returned instruction contains the expected structure
    assert expected_structure in instruction

def test_build_system_instruction_includes_category_sutras():
    """
    Tests if the build_system_instruction function correctly includes
    domain-specific sutras based on the intent_category.
    """
    from backend.chat.system_instruction_config import CAREER_SUTRAS, WEALTH_SUTRAS

    # Test for 'career' category
    instruction_career = build_system_instruction(analysis_type="EVENT_PREDICTION_MULTIPLE", intent_category="career")
    assert CAREER_SUTRAS in instruction_career

    # Test for 'wealth' category
    instruction_wealth = build_system_instruction(analysis_type="EVENT_PREDICTION_MULTIPLE", intent_category="wealth")
    assert WEALTH_SUTRAS in instruction_wealth

@patch('backend.ai.gemini_chat_analyzer.ChatContextBuilder.build_context')
@patch('backend.ai.gemini_chat_analyzer.GeminiChatAnalyzer._get_gemini_model')
def test_analyzer_uses_correct_instruction(mock_get_model, mock_build_context):
    """
    Tests that GeminiChatAnalyzer uses the system instruction generated
    based on the intent router's analysis_type.
    """
    # 1. Setup Mocks
    # Mock the model and its response
    mock_model = MagicMock()
    mock_gemini_response = MagicMock()
    mock_gemini_response.text = "This is the AI response."
    mock_model.generate_content.return_value = mock_gemini_response
    mock_get_model.return_value = mock_model

    # Mock the context builder to return a specific intent
    analysis_type = "ROOT_CAUSE_ANALYSIS"
    intent_category = "health"
    mock_context = {
        "intent": {
            "analysis_type": analysis_type,
            "category": intent_category
        },
        # ... other necessary context data
    }
    mock_build_context.return_value = mock_context

    # 2. Instantiate Analyzer and Call Method
    analyzer = GeminiChatAnalyzer()
    user_question = "Why have I been feeling so tired lately?"
    chat_history = []
    user_id = 123

    analyzer.analyze_chat_message(user_question, chat_history, user_id)

    # 3. Assertions
    # Verify that generate_content was called
    mock_model.generate_content.assert_called_once()

    # Get the arguments passed to generate_content
    args, kwargs = mock_model.generate_content.call_args
    prompt_parts = args[0] # The prompt is the first positional argument

    # Reconstruct the system instruction that was actually passed to the model
    # The system instruction is the first part of the prompt
    system_instruction_used = prompt_parts[0]

    # Check that the system instruction used contains the correct structure
    from backend.chat.system_instruction_config import ROOT_CAUSE_ANALYSIS_STRUCTURE, HEALTH_SUTRAS
    assert ROOT_CAUSE_ANALYSIS_STRUCTURE in system_instruction_used
    assert HEALTH_SUTRAS in system_instruction_used
    print(f"\n✅ Successfully verified that analyzer used instruction for '{analysis_type}' with '{intent_category}' sutras.")

if __name__ == "__main__":
    pytest.main([__file__])
