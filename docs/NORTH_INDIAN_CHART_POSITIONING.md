# North Indian Chart Positioning Reference

## Overview
This document provides the complete positioning reference for the North Indian astrology chart component. Use this when recreating or modifying the chart positioning logic.

## Chart Structure
- **Dimensions**: 400x400 SVG viewBox
- **Houses**: 12 total (8 triangular + 4 diamond shapes)
- **Geometry**: Outer square + inner diamond + 2 diagonal lines
- **File**: `frontend/src/components/Charts/NorthIndianChart.js`

## House Centers (X, Y coordinates)

| House | Position | Shape | Coordinates |
|-------|----------|-------|-------------|
| 1 | Top center | Diamond | (200, 110) |
| 2 | Top-left | Triangle | (110, 70) |
| 3 | Left-top | Triangle | (70, 110) |
| 4 | Left center | Diamond | (110, 200) |
| 5 | Left-bottom | Triangle | (70, 290) |
| 6 | Bottom-left | Triangle | (110, 330) |
| 7 | Bottom center | Diamond | (200, 290) |
| 8 | Bottom-right | Triangle | (290, 330) |
| 9 | Right-bottom | Triangle | (330, 290) |
| 10 | Right center | Diamond | (290, 200) |
| 11 | Right-top | Triangle | (330, 110) |
| 12 | Top-right | Triangle | (290, 70) |

## Rashi Positioning

Rashi numbers are positioned with offsets from house centers:

| House | X Offset | Y Offset | Notes |
|-------|----------|----------|-------|
| 1 | -5 | -5 | Moved up slightly |
| 2 | -5 | +35 | Bottom of inverted triangle |
| 3 | +10 | +5 | Moved right |
| 4 | +40 | +5 | Moved far right |
| 5 | +10 | +5 | Moved right |
| 6 | -5 | -10 | Moved up |
| 7 | -5 | -10 | Moved up |
| 8 | -5 | -10 | Moved up |
| 9 | -20 | +5 | Moved left |
| 10 | -40 | +5 | Moved far left |
| 11 | -15 | +5 | Moved left |
| 12 | -5 | +35 | Bottom of inverted triangle |

## Planet Positioning Logic

### Single Planet Positioning

| House Group | X Position | Y Position | Relationship |
|-------------|------------|------------|--------------|
| 1,6,7,8 | center.x | center.y + offset | Below rashi |
| 2,12 | center.x | center.y - 15 | Above rashi (inverted triangles) |
| 3,4,5 | center.x - 15 | center.y + 5 | Left of rashi |
| 9,10,11 | center.x + 15 | center.y + 5 | Right of rashi |

### Multiple Planets (2-4 planets)

**Spacing**: 16px horizontal, 18px vertical

**Formula**: `center.x + baseOffset + (col === 0 ? -spacing : spacing)`

| House | Base X Offset | Base Y Offset | Notes |
|-------|---------------|---------------|-------|
| 1 | 0 | +15 | Standard grid |
| 3 | -25 | 0 | Left-aligned grid |
| 4 | -25 | 0 | Left-aligned grid |
| 5 | -25 | 0 | Left-aligned grid |
| 6,7,8 | 0 | +20 | Standard grid |
| 9 | +25 | 0 | Right-aligned grid |
| 10 | +15 | 0 | Right-aligned grid |
| 11 | +20 | 0 | Right-aligned grid |
| 12 | 0 | -5 | Above rashi |

### Multiple Planets (5+ planets)

**Layout**: 3-column grid
**Spacing**: 12px horizontal, 15px vertical
**Formula**: `center.x + baseOffset + (col * spacing)` or `center.x + (col - 1) * spacing`

## Key Rules

1. **Inverted Triangles (Houses 2, 12)**: Planets positioned above rashi
2. **Left Side (Houses 3, 4, 5)**: Planets positioned left of rashi
3. **Right Side (Houses 9, 10, 11)**: Planets positioned right of rashi
4. **Standard Houses (1, 6, 7, 8)**: Planets positioned below rashi
5. **Spacing Formula**: Always use `(col === 0 ? -spacing : spacing)` for proper gaps, NOT `(col * spacing)`
6. **Font Scaling**: 10px for 5+ planets, 12px for 3-4 planets, 14px for 1-2 planets

## Code Implementation

```javascript
// Rashi positioning
const rashiX = houseNumber === 1 ? houseData.center.x - 5 :
              houseNumber === 2 ? houseData.center.x - 5 :
              // ... (see full implementation in component)

// Planet positioning for 2-4 planets
if (totalPlanets <= 4) {
  const row = Math.floor(pIndex / 2);
  const col = pIndex % 2;
  const spacing = 16;
  const rowSpacing = 18;
  
  planetX = baseX + (col === 0 ? -spacing : spacing);
  planetY = baseY + (row * rowSpacing);
}
```

## Troubleshooting

- **Overlapping**: Check base offsets and ensure proper spacing formula
- **Wrong positioning**: Verify house number mapping and shape type
- **Inconsistent spacing**: Ensure using `(col === 0 ? -spacing : spacing)` pattern
- **Font too small**: Adjust font scaling based on planet count

## Reference Implementation

The complete implementation can be found in:
`frontend/src/components/Charts/NorthIndianChart.js`

Look for the comment block at the top of the file for quick reference.