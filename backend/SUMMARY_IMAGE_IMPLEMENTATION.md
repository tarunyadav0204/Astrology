# Summary Image Implementation

## Overview
Changed from inline image tags to a single summary image that appears at the beginning of chat responses.

## Changes Made

### 1. Response Parser (`response_parser.py`)
**Old Behavior**: Extracted multiple inline `<image>` tags
**New Behavior**: Extracts single `SUMMARY_IMAGE_START...SUMMARY_IMAGE_END` block

```python
# Extracts summary image prompt
summary_image_prompt = None
if 'SUMMARY_IMAGE_START' in cleaned_text:
    prompt_section = cleaned_text.split('SUMMARY_IMAGE_START')[1].split('SUMMARY_IMAGE_END')[0]
    summary_image_prompt = prompt_section.strip()
```

### 2. Gemini Instructions (`gemini_chat_analyzer.py`)
**Old Instructions**: Generate 2-3 inline image tags with separate prompts
**New Instructions**: Generate ONE comprehensive infographic-style image prompt

**Example Prompt Format**:
```
SUMMARY_IMAGE_START
Astrological infographic sketch with 4 panels: 
- Top-left: Jupiter in 10th house with "Career Growth 2025" text
- Top-right: Moon in Rohini nakshatra with "Emotional Stability" label
- Bottom-left: Timeline showing "Saturn Mahadasha 2024-2043" with milestones
- Bottom-right: Yoga symbols with "Raj Yoga Active" text
- Center: Large "Promising Period Ahead" verdict
Cosmic purple and gold color scheme, hand-drawn mystical style
SUMMARY_IMAGE_END
```

### 3. Image Generation (`gemini_chat_analyzer.py`)
**Old Flow**: Generate multiple images from inline tags
**New Flow**: Generate single summary image

```python
summary_image_url = None
if self.flux_service and premium_analysis and parsed_response.get('summary_image_prompt'):
    summary_image_url = await self.flux_service.generate_image(parsed_response['summary_image_prompt'])
```

### 4. Response Format
**Old Return**:
```python
{
    'images': [
        {'id': 'jupiter_exalted', 'url': '...', 'prompt': '...'},
        {'id': 'moon_nakshatra', 'url': '...', 'prompt': '...'}
    ]
}
```

**New Return**:
```python
{
    'summary_image': 'https://replicate.delivery/...',  # Single URL or None
}
```

## Frontend Integration

The frontend should:
1. Check if `summary_image` exists in response
2. Display image at the **beginning** of the message bubble
3. Show image above the text content
4. Handle loading state while image generates

**Example Display**:
```
┌─────────────────────────┐
│  [Summary Image]        │
│  (Infographic sketch)   │
├─────────────────────────┤
│ Quick Answer: ...       │
│                         │
│ ### Key Insights        │
│ - Point 1               │
│ - Point 2               │
└─────────────────────────┘
```

## Benefits

1. **Single Visual Summary**: One comprehensive image instead of scattered visuals
2. **Better Context**: Image shows complete analysis at a glance
3. **Cleaner UI**: Image at top, text below - clear hierarchy
4. **Faster Generation**: One image instead of 2-3
5. **Better Prompts**: Gemini creates detailed multi-panel layouts

## Gemini Prompt Guidelines

The summary image should include:
- **Key planetary positions** with short labels
- **Major predictions** with brief text overlays
- **Timeline indicators** for important periods
- **Visual symbols** for yogas/doshas
- **Overall verdict** in center

Style: Hand-drawn sketch, infographic layout, cosmic colors (purple/gold)