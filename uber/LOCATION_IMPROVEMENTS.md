# Uber Location Accuracy Improvements

## Overview
Enhanced the location conversion process in the Uber API to provide significantly more accurate and precise coordinates using advanced LLM reasoning capabilities.

## What Changed

### 1. **Extended Thinking for Better Reasoning**
- Enabled Claude's extended thinking mode with 5000 token budget
- Allows the model to deeply reason about location ambiguities
- Provides step-by-step analysis before determining coordinates

### 2. **Enhanced Prompt Engineering**
The new prompt instructs the LLM to:
- **Identify the exact country and city** by analyzing contextual clues
- **Resolve ambiguities** (e.g., "Paris" could be France, Texas, or Ontario)
- **Handle abbreviations** (e.g., "St" as "Street" vs "Saint")
- **Provide precise coordinates** (minimum 6 decimal places)
- **Consider international address formats**

### 3. **Confidence Scoring**
- Each location now includes a confidence level (high/medium/low)
- System warns users when confidence is low
- Helps identify potential issues before booking

### 4. **Detailed Location Logging**
Now displays:
```
✓ Pickup: United States, Mountain View, CA, 1600 Amphitheatre Parkway (confidence: high)
  Coordinates: 37.422408, -122.084068
✓ Drop-off: United States, Cupertino, CA, 1 Apple Park Way (confidence: high)
  Coordinates: 37.334900, -122.009020
```

### 5. **Fallback Mechanism**
- Gracefully falls back to standard API if extended thinking is unavailable
- Ensures system remains functional even if advanced features fail

## Technical Details

### API Changes
```python
# Before
message = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{"role": "user", "content": prompt}]
)

# After
message = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,  # Must be greater than thinking budget_tokens
    temperature=1,    # Required to be 1 when using extended thinking
    messages=[{"role": "user", "content": prompt}],
    thinking={
        "type": "enabled",
        "budget_tokens": 5000  # Extended thinking budget
    }
)
```

### Response Format
```json
{
  "pickup": {
    "latitude": 37.422408,
    "longitude": -122.084068,
    "identified_as": "United States, Mountain View, CA, 1600 Amphitheatre Parkway",
    "confidence": "high"
  },
  "drop": {
    "latitude": 37.334900,
    "longitude": -122.009020,
    "identified_as": "United States, Cupertino, CA, 1 Apple Park Way",
    "confidence": "high"
  }
}
```

## Benefits

1. **More Accurate Coordinates**: Pinpoints exact addresses instead of city centers
2. **Better Disambiguation**: Correctly identifies which "Springfield" or "Paris" you mean
3. **International Support**: Handles different address formats worldwide
4. **Transparency**: Shows exactly what location was identified
5. **Safety**: Warns when system is uncertain about a location

## Testing

Run the test script to see improvements:
```bash
python3 uber/test_location_accuracy.py
```

This tests various scenarios:
- Clear addresses with no ambiguity
- Ambiguous city names
- Landmarks without full addresses
- Abbreviated addresses
- International addresses

## Example Improvements

### Before
- "Paris" → Generic Paris coordinates (could be anywhere)
- "Main Street" → Random Main Street location
- Precision: ~4 decimal places

### After
- "Paris" → Analyzes context, determines France, provides precise coordinates
- "Main Street, Springfield" → Reasons about which Springfield, provides exact location
- Precision: 6+ decimal places
- Confidence: Indicates certainty level

## Notes

- The extended thinking feature uses additional tokens but provides significantly better accuracy
- **Temperature must be set to 1 when using extended thinking** (API requirement)
- **max_tokens must be greater than thinking.budget_tokens** (API requirement)
  - We use max_tokens=8000 with budget_tokens=5000
- System automatically falls back if extended thinking is unavailable
- Fallback mode uses temperature=0 for maximum determinism
- All changes are backward compatible with existing API

## Future Enhancements

Potential improvements:
1. Add support for user-provided country/region hints
2. Cache common locations to reduce API calls
3. Add coordinate validation against known Uber service areas
4. Implement fuzzy matching for typos in addresses

