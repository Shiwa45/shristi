# Design Document

## Overview

This feature enhances the existing children's book ordering form by replacing the current simple design service toggle with a more comprehensive design service selection system. The current implementation shows inline checkboxes for "Cover Page" and "Inner Pages" when design service is selected. The new design will replace this with a 4-box grid layout that provides customers with clear design service options.

## Architecture

### Current System Analysis
- The existing system uses radio buttons ("Not Required" vs "Yes You Can") 
- When "Yes You Can" is selected, 2 checkboxes appear: "Cover Page" (₹1500) and "Inner Pages" (₹50 per page)
- These checkboxes are displayed inline after the radio buttons
- The system already handles design service pricing and integration with the order system
- Form validation ensures design service selection is captured properly

### Proposed Enhancement
- Keep the existing radio buttons ("Not Required" vs "Yes You Can")
- Replace the 2 inline checkboxes with a 4-box grid layout when "Yes You Can" is selected
- Transform from checkbox-based selection to single-option selection (like radio buttons)
- Maintain existing pricing integration and form validation
- Ensure responsive design for mobile and desktop

## Components and Interfaces

### 1. Design Service Toggle Component
**Location:** `templates/services/static_products/book_printing_detail.html`
**Current Implementation:** Radio buttons with inline checkboxes
**Enhancement:** Keep radio buttons, replace checkbox display with 4-box grid

### 2. Design Options Grid Component
**New Component:** 4-box grid layout
**Structure:**
```html
<div class="design-options-grid">
  <div class="design-option-box" data-option="basic-cover">
    <!-- Option 1: Basic Cover Design -->
  </div>
  <div class="design-option-box" data-option="premium-cover">
    <!-- Option 2: Premium Cover Design -->
  </div>
  <div class="design-option-box" data-option="full-design">
    <!-- Option 3: Full Book Design -->
  </div>
  <div class="design-option-box" data-option="custom-design">
    <!-- Option 4: Custom Design Package -->
  </div>
</div>
```

### 3. JavaScript Enhancement
**File:** Existing JavaScript in `book_printing_detail.html`
**Enhancements:**
- Update event listeners to handle box selection instead of checkboxes
- Maintain pricing calculation logic
- Add visual feedback for box selection
- Ensure form validation works with new selection method

## Data Models

### Design Service Options
The 4 design service options will be:

1. **Basic Cover Design** (₹1,500)
   - Professional cover design
   - 2 design concepts
   - 1 revision included

2. **Premium Cover Design** (₹2,500)
   - Premium cover design
   - 3 design concepts
   - 3 revisions included
   - High-resolution files

3. **Full Book Design** (₹3,500)
   - Cover + inner page design
   - Complete layout design
   - 2 design concepts
   - 2 revisions included

4. **Custom Design Package** (₹5,000)
   - Fully custom design
   - Unlimited concepts
   - Unlimited revisions
   - Premium support

### Form Data Structure
```javascript
{
  need_design_service: "yes|no",
  design_service_option: "basic-cover|premium-cover|full-design|custom-design",
  design_service_price: number
}
```

## Error Handling

### Validation Rules
1. If `need_design_service` is "yes", then `design_service_option` must be selected
2. Design service price must be calculated and added to total
3. Form submission should validate that exactly one design option is selected when design service is requested

### Error Messages
- "Please select a design service option" - when design service is requested but no option selected
- "Design service selection is required" - when form validation fails

### Fallback Behavior
- If JavaScript fails, form should still be submittable with basic validation
- Server-side validation should mirror client-side validation
- Graceful degradation to ensure functionality without JavaScript

## Testing Strategy

### Unit Testing
- Test design option selection logic
- Test pricing calculation with different design options
- Test form validation scenarios
- Test responsive grid layout

### Integration Testing
- Test integration with existing order system
- Test pricing API calls with new design options
- Test form submission with design service selections
- Test backward compatibility with existing orders

### User Experience Testing
- Test 4-box grid layout on different screen sizes
- Test hover and selection states
- Test accessibility with keyboard navigation
- Test visual feedback and confirmation

## Implementation Approach

### Phase 1: CSS and HTML Structure
- Create CSS classes for 4-box grid layout
- Add responsive design rules
- Implement hover and selection states
- Ensure accessibility compliance

### Phase 2: JavaScript Enhancement
- Update existing event listeners
- Add box selection logic
- Maintain pricing calculation
- Add visual feedback

### Phase 3: Integration and Testing
- Test with existing form validation
- Verify pricing integration
- Test order submission flow
- Validate responsive behavior

## Responsive Design Considerations

### Desktop (1024px+)
- 2x2 grid layout
- Larger boxes with detailed information
- Hover effects and animations

### Tablet (768px - 1023px)
- 2x2 grid layout with smaller boxes
- Simplified content
- Touch-friendly interactions

### Mobile (< 768px)
- 1x4 vertical stack layout
- Full-width boxes
- Touch-optimized selection

## Accessibility Requirements

- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode compatibility
- Focus indicators for all interactive elements
- Semantic HTML structure