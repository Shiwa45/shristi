# Requirements Document

## Introduction

This feature implements category-specific pricing calculators and form fields on product detail pages for the 4 main printing categories (Book printing, Paper Boxes, Marketing Material, Stationery). When users view individual products (like "Children's Book Printing" or "Business Cards"), they should see specialized forms and pricing calculators tailored to that product's category. The category listing pages remain unchanged, showing products under each category, but the individual product pages get enhanced with category-specific functionality.

## Requirements

### Requirement 1

**User Story:** As a customer viewing a book printing product (like "Children's Book Printing"), I want a specialized book printing form with sequential fields specific to book production, so that I can configure my book step-by-step and get accurate pricing.

#### Acceptance Criteria

1. WHEN a user navigates to any book printing product detail page THEN the system SHALL display a specialized book printing form with sequential sections
2. WHEN the book printing product page loads THEN the system SHALL show "Book Options" section with the heading "Select The Colors, Paper Type, Binding And Cover Finish For Your Book"
3. WHEN displaying Interior Color options THEN the system SHALL show: Black & White Premium, Black & White Standard, Color Premium, Color Standard, Combine Color with appropriate descriptions
4. WHEN a user selects an Interior Color option THEN the system SHALL enable the "Book Size And Page Count" section
5. WHEN a user selects "Combine Color" for interior THEN the system SHALL display both "B/W Page Count" and "Color Page Count" input fields
6. WHEN a user selects any other interior color option THEN the system SHALL display only the "Page Count" input field
7. WHEN a user completes Book Size and Page Count THEN the system SHALL enable the "Paper Type" section with options: 75 GSM, 100 GSM, 100 GSM Art Paper, 130 GSM Art Paper (with "Option Not Available" placeholders where applicable)
8. WHEN a user completes Paper Type selection THEN the system SHALL enable the "Binding Type" section
9. WHEN a user enters less than 30 pages THEN the system SHALL show "Paperback (Perfect)" and "Hardcover" options as "Not Available for less than 30 pages"
10. WHEN a user enters 30 or more pages THEN the system SHALL show all binding options: Saddle Stitch, Spiral Binding, Paperback (Perfect), Hardcover as available
11. WHEN a user completes Binding Type THEN the system SHALL enable "Cover Finish" section with options: Glossy, Matte
12. WHEN a user completes Cover Finish THEN the system SHALL enable "Designing And Formatting" section with pricing note "Rs.1500/- Extra Per Cover Page And Rs. 50 Extra Per Inner Page"
13. WHEN a user selects "Yes You Can" for designing THEN the system SHALL show file upload fields for Cover Page and Inner Pages
14. WHEN a user completes Designing section THEN the system SHALL enable "ISBN Allocation" section with note "It May Take 5 to 7 More Working Days To Deliver"
15. WHEN all sections are completed THEN the system SHALL display "Book Specifications" summary showing all selections

### Requirement 2

**User Story:** As a customer viewing a paper box product (like "Custom Paper Boxes"), I want a specialized paper box form with fields specific to packaging (box dimensions, material type, printing options), so that I can configure custom packaging solutions.

#### Acceptance Criteria

1. WHEN a user navigates to any paper box product detail page THEN the system SHALL display a specialized paper box form
2. WHEN the paper box product page loads THEN the system SHALL show fields for box dimensions (length, width, height), material options (corrugated, cardboard, kraft)
3. WHEN a user selects box specifications THEN the system SHALL calculate pricing based on material cost, size, and printing requirements
4. WHEN displaying paper box options THEN the system SHALL include printing options (no printing, 1-color, full color) and finishing options (matte, gloss, UV coating)
5. WHEN a user inputs custom dimensions THEN the system SHALL validate dimensions and apply custom sizing pricing modifiers

### Requirement 3

**User Story:** As a customer viewing a marketing material product (like "Brochures" or "Business Flyers"), I want a specialized marketing materials form with fields for promotional products, so that I can choose the right marketing solution.

#### Acceptance Criteria

1. WHEN a user navigates to any marketing material product detail page THEN the system SHALL display a specialized marketing materials form
2. WHEN the marketing materials product page loads THEN the system SHALL show relevant options for that specific product type with type-specific configurations
3. WHEN a user selects a marketing material type THEN the system SHALL display relevant fields for that type (size options, folding options for brochures, paper weights)
4. WHEN calculating pricing for marketing materials THEN the system SHALL apply type-specific pricing rules and quantity discounts
5. WHEN displaying marketing material options THEN the system SHALL include design service options and rush order availability

### Requirement 4

**User Story:** As a customer viewing a stationery product (like "Business Cards" or "Letterheads"), I want a specialized stationery form with fields for business stationery items, so that I can create professional business materials.

#### Acceptance Criteria

1. WHEN a user navigates to any stationery product detail page THEN the system SHALL display a specialized stationery form
2. WHEN the stationery product page loads THEN the system SHALL show options specific to that stationery product with appropriate specifications
3. WHEN a user selects business cards THEN the system SHALL display card-specific options (standard sizes, premium papers, finishing options like embossing, foil stamping)
4. WHEN a user selects letterheads or envelopes THEN the system SHALL display relevant paper options and printing specifications
5. WHEN calculating stationery pricing THEN the system SHALL apply item-specific pricing with appropriate quantity breaks for business stationery

### Requirement 5

**User Story:** As a website administrator, I want the system to automatically display category-specific forms and pricing calculators on product detail pages based on the product's category, so that customers always see the most relevant interface for their needs.

#### Acceptance Criteria

1. WHEN a user clicks on a product from a category listing page THEN the system SHALL display the product detail page with category-specific form and pricing calculator
2. WHEN the system detects a product belongs to book printing category THEN the system SHALL load the book printing form template and pricing logic
3. WHEN the system detects a product belongs to paper boxes category THEN the system SHALL load the paper boxes form template and pricing logic
4. WHEN the system detects a product belongs to marketing material category THEN the system SHALL load the marketing materials form template and pricing logic
5. WHEN the system detects a product belongs to stationery category THEN the system SHALL load the stationery form template and pricing logic
6. WHEN a product doesn't belong to any of the 4 main categories THEN the system SHALL display the generic product detail page

### Requirement 6

**User Story:** As a customer using the book printing page, I want to see detailed pricing calculations and file upload functionality, so that I can understand costs and provide necessary files for my book project.

#### Acceptance Criteria

1. WHEN a user completes book specifications THEN the system SHALL display "Cost Per Book" calculation showing "Rs. N/A" until all required fields are filled
2. WHEN all required fields are completed THEN the system SHALL show detailed pricing breakdown in "Pricing Estimate" section
3. WHEN displaying pricing estimate THEN the system SHALL show: Book Subtotal (excluding shipping and GST), Volume Discount percentage and amount, Shipping & Handling with delivery timeframe, GST 18%, Total including shipping and GST
4. WHEN a user enters number of copies THEN the system SHALL enforce minimum quantity of 25 copies
5. WHEN file upload is attempted THEN the system SHALL validate file types (PDF, Word File & Excel) for both Cover Page and Inner Page uploads
6. WHEN invalid file types are uploaded THEN the system SHALL display "Not a Valid File" validation message
7. WHEN all specifications and files are ready THEN the system SHALL enable "Order Your Book" button
8. WHEN pricing calculations update THEN the system SHALL recalculate all dependent pricing elements within 500ms

### Requirement 7

**User Story:** As a customer using any category-specific page, I want dynamic pricing calculations that update in real-time as I change specifications, so that I can see how my choices affect the final price.

#### Acceptance Criteria

1. WHEN a user changes any specification field THEN the system SHALL recalculate and display the updated price within 500ms
2. WHEN displaying pricing THEN the system SHALL show a breakdown of base price, option modifiers, quantity discounts, and total price
3. WHEN a user selects rush order or design services THEN the system SHALL add the appropriate charges to the total
4. WHEN quantity thresholds are reached THEN the system SHALL automatically apply volume discounts and highlight the savings
5. WHEN pricing calculations fail THEN the system SHALL display a user-friendly error message and maintain the last valid price

### Requirement 8

**User Story:** As a customer on any category page, I want to be able to upload design files and add special instructions, so that I can provide all necessary information for my printing project.

#### Acceptance Criteria

1. WHEN a category page loads THEN the system SHALL provide file upload functionality for design files
2. WHEN a user uploads files THEN the system SHALL validate file types (PDF, AI, PSD, JPG, PNG) and size limits
3. WHEN file upload is complete THEN the system SHALL display uploaded file names and allow file removal
4. WHEN a user wants to add special instructions THEN the system SHALL provide a text area for custom requirements
5. WHEN a user submits a quote request THEN the system SHALL include all uploaded files and instructions in the quote

### Requirement 9

**User Story:** As a website administrator, I want the system to enforce sequential field dependencies and prevent users from skipping required steps, so that all necessary information is collected in the correct order.

#### Acceptance Criteria

1. WHEN a user first loads any category page THEN the system SHALL only enable the first form section
2. WHEN a user attempts to interact with disabled form sections THEN the system SHALL prevent interaction and highlight the current required step
3. WHEN a user completes a required field or section THEN the system SHALL automatically enable the next sequential section
4. WHEN a user changes a previously completed field THEN the system SHALL reset and disable all subsequent dependent fields
5. WHEN form validation fails on any section THEN the system SHALL prevent progression to subsequent sections until validation passes

### Requirement 10

**User Story:** As a website administrator, I want to easily manage category-specific form fields and pricing rules through the Django admin, so that I can update options without code changes.

#### Acceptance Criteria

1. WHEN accessing the Django admin THEN the system SHALL provide interfaces to manage category-specific form fields
2. WHEN adding new form fields THEN the system SHALL allow specification of field type, validation rules, and pricing modifiers
3. WHEN updating pricing rules THEN the system SHALL allow modification of base prices, quantity tiers, and option modifiers per category
4. WHEN changes are saved in admin THEN the system SHALL immediately reflect updates on the corresponding category pages
5. WHEN managing categories THEN the system SHALL enforce that only the 4 main categories remain active and accessible