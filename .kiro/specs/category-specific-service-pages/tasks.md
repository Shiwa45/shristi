# Implementation Plan

- [x] 1. Set up enhanced data models and database structure
  - Create CategoryFormField model with category-specific field configurations
  - Create CategoryPricingRule model for category-specific pricing logic
  - Add database migrations for new models
  - Update existing ServiceCategory model to support category-specific configurations
  - _Requirements: 9.1, 10.1, 10.2_

- [x] 1.1 Create CategoryFormField model


  - Write CategoryFormField model with category choices, field types, and conditional logic support
  - Add JSON fields for options, show conditions, and pricing modifiers
  - Implement model methods for parsing JSON configurations and validation
  - _Requirements: 9.1, 10.1_



- [ ] 1.2 Create CategoryPricingRule model
  - Write CategoryPricingRule model with rule types and pricing formulas
  - Add support for quantity tiers, conditional pricing, and option modifiers

  - Implement pricing calculation methods in the model
  - _Requirements: 6.2, 7.1, 10.3_

- [x] 1.3 Update ServiceCategory model

  - Add category-specific configuration fields to ServiceCategory
  - Create method to get category-specific form fields
  - Add validation to ensure only 4 main categories remain active
  - _Requirements: 5.4, 10.5_

- [ ]* 1.4 Write unit tests for new models
  - Create unit tests for CategoryFormField model methods
  - Write tests for CategoryPricingRule pricing calculations
  - Test model validation and JSON field parsing
  - _Requirements: 9.1, 10.1_

- [x] 2. Enhance product detail views for category-specific functionality
  - Update static_product_detail view to detect category-specific products
  - Implement template selection logic for category-specific product pages
  - Add form field retrieval and context preparation for each category
  - Add category-specific context data for pricing and options
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 2.1 Update URL routing for category-specific pages


  - Modify services/urls.py to include category-specific routes
  - Add URL patterns for book-printing, paper-boxes, marketing-material, stationery
  - Implement URL validation to ensure only valid categories are accessible
  - _Requirements: 5.1, 5.2_

- [x] 2.2 Create CategorySpecificView class


  - Write view class that detects category and selects appropriate template
  - Implement get_template_name method with category-specific template mapping
  - Add context preparation for category-specific form fields and pricing rules
  - _Requirements: 5.2, 5.3_

- [x] 2.3 Implement form field context preparation


  - Create method to retrieve category-specific form fields from database
  - Organize form fields by sections with proper ordering
  - Prepare conditional field logic and dependencies for frontend
  - _Requirements: 1.2, 1.4, 9.1_

- [ ]* 2.4 Write integration tests for routing and views
  - Test category-specific URL routing and template selection
  - Test form field context preparation and data structure
  - Test access restriction for invalid categories
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 3. Create category-specific product detail templates
  - Update base product detail template with blocks for category-specific content
  - Implement book printing product detail template with sequential form sections
  - Add category-specific pricing calculator for book printing products
  - Create form field rendering with conditional logic support
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15_

- [x] 3.1 Create base category template


  - Write base_category.html template with shared layout structure
  - Add blocks for category header, form sections, and pricing calculator
  - Implement responsive design with form container and pricing sidebar
  - _Requirements: 1.1, 1.2_

- [x] 3.2 Implement book printing template



  - Create book_printing.html template extending base category template
  - Add all 7 sequential form sections (Interior Color, Book Size & Page Count, etc.)
  - Implement conditional field display for combine color and page count options
  - Add binding type restrictions based on page count
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15_

- [ ] 3.3 Create templates for other categories
  - Write paper_boxes.html template with box-specific form fields
  - Create marketing_material.html template with material-specific options
  - Implement stationery.html template with stationery-specific fields
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.4 Add form field rendering components
  - Create template tags for rendering different field types (radio, select, number, file)
  - Implement conditional field wrapper with data attributes for JavaScript
  - Add form validation display and error message handling
  - _Requirements: 9.2, 9.3, 9.4, 9.5_

- [ ]* 3.5 Write template rendering tests
  - Test category-specific template selection and rendering
  - Test form field rendering with different field types
  - Test conditional field display logic
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 4. Implement sequential form engine JavaScript
  - Create SequentialFormEngine class to manage step-by-step form progression
  - Implement section enabling/disabling logic based on completion status
  - Add form validation for each section before allowing progression
  - Handle dependency resets when previous fields are changed
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 4.1 Create SequentialFormEngine class
  - Write JavaScript class to manage form section progression
  - Implement section validation and enabling logic
  - Add methods for handling field dependencies and conditional display
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 4.2 Implement section progression logic
  - Add logic to enable next section when current section is completed and valid
  - Implement visual feedback for enabled/disabled sections
  - Add prevention of interaction with disabled sections
  - _Requirements: 9.2, 9.3, 9.4_

- [ ] 4.3 Add dependency management
  - Implement logic to reset dependent sections when parent fields change
  - Add conditional field show/hide based on field values
  - Handle complex dependencies like combine color affecting page count fields
  - _Requirements: 9.4, 9.5, 1.5, 1.6_

- [ ] 4.4 Implement form validation
  - Add client-side validation for each field type
  - Implement section-level validation before progression
  - Add file upload validation for design files
  - _Requirements: 6.6, 8.2, 8.3_

- [ ]* 4.5 Write JavaScript unit tests
  - Test sequential form progression logic
  - Test dependency management and conditional fields
  - Test form validation and error handling
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 5. Create category-specific pricing calculator
  - Extend existing DynamicPricingCalculator for category-specific logic
  - Implement book printing pricing with page count, binding, and option modifiers
  - Add pricing calculations for other categories with their specific rules
  - Integrate with sequential form engine for real-time price updates
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 5.1 Extend DynamicPricingCalculator for categories
  - Modify existing pricing calculator to support category-specific logic
  - Add category detection and pricing rule loading
  - Implement base structure for category-specific pricing methods
  - _Requirements: 6.1, 7.1, 7.2_

- [ ] 5.2 Implement book printing pricing logic
  - Add calculateBookPricing method with interior color, page count, and binding modifiers
  - Implement combine color pricing with separate B&W and color page calculations
  - Add binding type pricing with page count restrictions
  - Include design service and ISBN allocation pricing
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 5.3 Add pricing for other categories
  - Implement paper box pricing with dimension and material calculations
  - Create marketing material pricing with type-specific modifiers
  - Add stationery pricing with item-specific calculations
  - _Requirements: 2.3, 2.4, 3.4, 3.5, 4.4, 4.5_

- [ ] 5.4 Integrate with sequential form engine
  - Connect pricing calculator with form progression events
  - Add real-time price updates as sections are completed
  - Implement price breakdown display with detailed cost components
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 5.5 Write pricing calculator tests
  - Test category-specific pricing calculations
  - Test book printing pricing with various combinations
  - Test real-time price update functionality
  - _Requirements: 6.1, 6.2, 7.1_

- [ ] 6. Implement detailed pricing breakdown and cost display
  - Create pricing breakdown component showing base price, modifiers, and totals
  - Add volume discount calculations and display
  - Implement shipping and GST calculations for final pricing
  - Add cost per book display and minimum quantity enforcement
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [ ] 6.1 Create pricing breakdown component
  - Write HTML template for detailed pricing breakdown display
  - Add sections for base price, option modifiers, quantity discounts
  - Implement shipping and GST calculation display
  - _Requirements: 6.2, 6.3, 6.4_

- [ ] 6.2 Implement volume discount calculations
  - Add quantity tier detection and discount percentage application
  - Display volume discount savings prominently
  - Update pricing breakdown when quantity changes
  - _Requirements: 6.4, 6.5_

- [ ] 6.3 Add shipping and GST calculations
  - Implement shipping cost calculation based on quantity and location
  - Add 18% GST calculation and display
  - Show final total including all charges
  - _Requirements: 6.3, 6.8_

- [ ] 6.4 Implement minimum quantity enforcement
  - Add validation for minimum 25 copies for book printing
  - Display minimum quantity requirements clearly
  - Prevent order submission below minimum quantities
  - _Requirements: 6.5, 6.8_

- [ ] 7. Add file upload functionality and validation
  - Implement file upload components for design files
  - Add file type validation (PDF, Word, Excel) for book printing
  - Create file upload progress and error handling
  - Add uploaded file display and removal functionality
  - _Requirements: 6.6, 6.7, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 7.1 Create file upload components
  - Write file upload HTML components with drag-and-drop support
  - Add separate upload areas for Cover Page and Inner Pages
  - Implement file upload progress indicators
  - _Requirements: 6.6, 6.7, 8.1_

- [ ] 7.2 Implement file validation
  - Add client-side file type validation for PDF, Word, Excel
  - Implement file size validation and limits
  - Add server-side file validation for security
  - _Requirements: 6.6, 8.2, 8.3_

- [ ] 7.3 Add file management functionality
  - Implement uploaded file display with file names and sizes
  - Add file removal functionality
  - Handle multiple file uploads per section
  - _Requirements: 8.3, 8.4_

- [ ]* 7.4 Write file upload tests
  - Test file upload validation and error handling
  - Test file display and removal functionality
  - Test server-side file processing
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 8. Create admin interface for category configuration
  - Implement Django admin interface for CategoryFormField management
  - Add admin interface for CategoryPricingRule configuration
  - Create bulk import/export functionality for form field configurations
  - Add admin validation to ensure only 4 main categories remain active
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 8.1 Implement CategoryFormField admin interface
  - Create Django admin class for CategoryFormField with proper fieldsets
  - Add list display, filtering, and search functionality
  - Implement inline editing for related form field options
  - _Requirements: 10.1, 10.2_

- [ ] 8.2 Create CategoryPricingRule admin interface
  - Write Django admin class for CategoryPricingRule management
  - Add form validation for pricing rule configurations
  - Implement preview functionality for pricing calculations
  - _Requirements: 10.3, 10.4_

- [ ] 8.3 Add bulk configuration management
  - Implement import/export functionality for form field configurations
  - Add bulk editing capabilities for multiple form fields
  - Create configuration templates for quick category setup
  - _Requirements: 10.2, 10.4_

- [ ] 8.4 Implement category validation
  - Add admin validation to ensure only 4 main categories remain active
  - Implement checks for required form fields per category
  - Add validation for pricing rule completeness
  - _Requirements: 10.5_

- [ ] 9. Add comprehensive error handling and validation
  - Implement client-side form validation with user-friendly error messages
  - Add server-side validation for all form submissions
  - Create graceful error handling for pricing calculation failures
  - Add fallback mechanisms for JavaScript failures
  - _Requirements: 6.8, 7.5, 8.2, 8.5, 9.5_

- [ ] 9.1 Implement client-side validation
  - Add real-time field validation as users type
  - Implement section-level validation before progression
  - Create user-friendly error message display
  - _Requirements: 9.5, 8.2_

- [ ] 9.2 Add server-side validation
  - Implement comprehensive form data validation on submission
  - Add business rule validation (page counts, binding restrictions)
  - Create validation for file uploads and security checks
  - _Requirements: 8.5, 6.8_

- [ ] 9.3 Create error handling for pricing calculations
  - Add try-catch blocks for pricing calculation errors
  - Implement fallback to last valid price on calculation failure
  - Create user-friendly error messages for pricing issues
  - _Requirements: 7.5, 6.8_

- [ ] 9.4 Add JavaScript fallback mechanisms
  - Implement progressive enhancement for form functionality
  - Add server-side form processing as fallback
  - Create graceful degradation for pricing calculator
  - _Requirements: 7.5, 9.5_

- [ ] 10. Implement specifications summary and order functionality
  - Create dynamic specifications summary that updates with form selections
  - Add "Order Your Book" button with form submission handling
  - Implement order data preparation and validation before submission
  - Add success/confirmation page after order submission
  - _Requirements: 1.15, 6.7, 6.8_

- [ ] 10.1 Create specifications summary component
  - Write dynamic summary component that displays all user selections
  - Update summary in real-time as form sections are completed
  - Add clear display of book specifications, pricing, and files
  - _Requirements: 1.15_

- [x] 10.2 Implement order submission functionality



  - Add "Order Your Book" button with proper form validation
  - Implement order data collection and preparation
  - Create order submission handling with file attachments
  - _Requirements: 6.7, 6.8_

- [ ] 10.3 Add order confirmation and success handling
  - Create order confirmation page with order details
  - Implement email notifications for order confirmation
  - Add order tracking information and next steps
  - _Requirements: 6.8, 8.5_

- [ ]* 10.4 Write end-to-end tests
  - Test complete order flow from form filling to submission
  - Test specifications summary updates and accuracy
  - Test order confirmation and email notifications
  - _Requirements: 1.15, 6.7, 6.8_

- [ ] 11. Optimize performance and add final polish
  - Implement lazy loading for category-specific JavaScript and CSS
  - Add loading states and progress indicators for better UX
  - Optimize database queries for form field retrieval
  - Add caching for category configurations and pricing rules
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 11.1 Implement lazy loading and performance optimization
  - Add lazy loading for category-specific JavaScript modules
  - Implement CSS code splitting for category-specific styles
  - Optimize database queries with proper indexing and caching
  - _Requirements: 7.1, 7.2_

- [ ] 11.2 Add loading states and UX improvements
  - Implement loading spinners for pricing calculations
  - Add progress indicators for file uploads
  - Create smooth transitions between form sections
  - _Requirements: 7.3, 7.4_

- [ ] 11.3 Add final testing and bug fixes
  - Perform comprehensive testing across all categories
  - Fix any remaining bugs and edge cases
  - Optimize for mobile responsiveness and accessibility
  - _Requirements: 7.5_

- [ ]* 11.4 Write performance tests
  - Test page load times for category-specific pages
  - Test pricing calculation performance with complex configurations
  - Test file upload performance and error handling
  - _Requirements: 7.1, 7.2, 7.3_