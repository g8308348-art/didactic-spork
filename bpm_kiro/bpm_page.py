"""BPM Page object model and helpers for UI automation flows.

This module defines the `Options` enumeration and the `BPMPage` page-object class
used by Playwright scripts to automate State Street’s BPM UI.
"""

# pylint: disable=invalid-name,line-too-long,logging-fstring-interpolation,broad-exception-raised,no-else-return,missing-module-docstring,missing-function-docstring

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Tuple
from playwright.sync_api import expect, Page
# Performance optimization imports
try:
    from performance_optimizations import (
        PerformanceOptimizer,
        BatchTextExtractor,
        OptimizedNumericParser,
        OptimizedEnvironmentDetector,
        PerformanceProfiler
    )
    from bmp_optimizations_patch import BPMPageOptimizations
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    logging.warning("Performance optimizations not available - using standard methods")
    PERFORMANCE_OPTIMIZATIONS_AVAILABLE = False



class Options(Enum):
    """Enumeration of BPM market / transaction type options displayed in the UI."""

    UNCLASSIFIED = "Unclassified"
    APS_MT = "APS-MT"
    CBPR_MX = "CBPR-MX"
    SEPA_CLASSIC = "SEPA-Classic"
    RITS_MX = "RITS-MX"
    LYNX_MX = "LYNX-MX"
    ENTERPRISE_ISO = "EnterpriseISO"
    CHAPS_MX = "CHAPS-MX"
    T2S_MX = "T2S-MX"
    BESS_MT = "BESS-MT"
    CHIPS_MX = "CHIPS-MX"
    SEPA_INSTANT = "SEPA-Instant"
    FEDWIRE = "FEDWIRE"
    TAIWAN_MX = "Taiwan-MX"
    CHATS_MX = "CHATS-MX"
    PEPPLUS_IAT = "PEPPLUS-IAT"
    TSF_TRIGGER = "TSF-TRIGGER"


@dataclass
class ColumnData:
    """Represents extracted column data from a BPM result row."""
    position: int
    value: str
    is_numeric: bool = False
    numeric_value: Optional[int] = None

    def __str__(self) -> str:
        return f"Col{self.position}: {self.value}"


@dataclass
class BPMSearchResult:
    """Enhanced search result containing all column data and environment info."""
    # Backward compatibility fields
    fourth_column: str
    last_column: str
    
    # New enhanced fields
    all_columns: List[ColumnData]
    second_to_last_column: str
    environment: str  # "buat", "uat", or "unknown"
    total_columns: int
    
    # Metadata
    transaction_found: bool
    search_timestamp: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "fourth_column": self.fourth_column,
            "last_column": self.last_column,
            "second_to_last_column": self.second_to_last_column,
            "environment": self.environment,
            "total_columns": self.total_columns,
            "transaction_found": self.transaction_found,
            "search_timestamp": self.search_timestamp,
            "all_columns": [
                {
                    "position": col.position,
                    "value": col.value,
                    "is_numeric": col.is_numeric,
                    "numeric_value": col.numeric_value
                }
                for col in self.all_columns
            ]
        }


class BPMPage:
    """Page Object Model encapsulating high-level BPM UI interactions."""

    def __init__(self, page: Page):
        self.page = page
        self.menu_item = page.locator("div.modal-content[role='document']")
        
        # Performance optimization components
        if PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            self.performance_optimizer = BPMPageOptimizations()
            self.profiler = PerformanceProfiler()
            self._performance_mode_enabled = False
        else:
            self.performance_optimizer = None
            self.profiler = None
            self._performance_mode_enabled = False

    def safe_click(self, locator, description: str):
        if locator.is_visible():
            locator.click()
            logging.info("Clicked on %s.", description)
        else:
            msg = f"{description} is not visible."
            logging.error(msg)
            raise Exception(msg)

    def login(self, url: str, username: str, password: str) -> None:
        try:
            logging.info("Logging to BPM as %s.", username)
            self.page.goto(url)
            expect(self.page).to_have_title("State Street Login")
            self.page.fill("input[name='username']", username)
            self.page.fill("input[name='PASSWORD']", password)
            self.page.click("input[type='submit'][value='Submit']")
            self.page.wait_for_load_state("networkidle")

            title = self.page.title()
            if title == "State Street Corporation":
                logging.info("Successfully logged in to BPM as %s.", username)
            elif title == "State Street Login":
                raise Exception("Login failed: Invalid credentials.")
            else:
                raise Exception("Login failed: Unexpected page title.")

        except Exception as e:
            logging.error("Failed to login to BPM: %s", e)
            raise

    def verify_modal_visibility(self) -> None:
        try:
            if self.menu_item.is_visible():
                logging.info("<div class='modal-content' role='document'> is visible.")
            else:
                raise Exception(
                    "<div class='modal-content' role='document'> is not visible."
                )
        except Exception as e:
            logging.error("Failed to verify modal visibility: %s", e)
            raise

    def click_tick_box(self) -> None:
        try:
            tick_box = self.page.locator("li:has-text('ORI') i.fa-square-o")
            self.safe_click(tick_box, "tick box with text 'ORI'")
        except Exception as e:
            logging.error("Failed to click on the tick box with text 'ORI': %s", e)
            raise

    def click_ori_tsf(self) -> None:
        try:
            self.safe_click(
                self.page.locator("div i:has-text('ORI-TSF')"),
                "element with text 'ORI-TSF'",
            )
        except Exception as e:
            logging.error("Failed to click on the element with text 'ORI-TSF': %s", e)
            raise

    def check_options(self, options: list[Options]) -> None:

        try:
            logging.info("Checking options: %s", options)
            for option in options:
                option_locator = self.page.locator(
                    f"li span.inf-name:has-text('{option.value}') i.fa-square-o"
                )
                self.safe_click(option_locator, f"option '{option.value}'")
                time.sleep(1)

                # Verify the option is now checked by looking for the selected icon (fa-check-square-o)
                selected_locator = self.page.locator(
                    f"li span.inf-name:has-text('{option.value}') i.fa-check-square-o"
                )
                if selected_locator.is_visible():
                    logging.info("Verified option '%s' is selected.", option.value)
                else:
                    logging.warning(
                        "Warning: After clicking, option '%s' does NOT appear selected.",
                        option.value,
                    )
        except Exception as e:
            logging.error("Failed to check specified options in the list: %s", e)
            raise

    def click_submit_button(self) -> None:
        """Click the form's primary Submit button."""
        try:
            self.page.click("button.btn.btn-primary")
            logging.info("Clicked on the Submit button.")
        except Exception as e:
            logging.error("Failed to click on the Submit button: %s", e)
            raise

    # ------------------------------------------------------------------
    # Composite helpers
    # ------------------------------------------------------------------
    def check_options_and_submit(self, options: list[Options]) -> None:
        """High-level helper: tick given market checkboxes and press Submit.

        Args:
            options (list[Options]): Markets to select in the left-hand tree.
        """
        logging.info("Selecting market options: %s", [opt.value for opt in options])
        self.check_options(options)
        self.click_submit_button()

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def debug_list_advanced_fields(self) -> None:
        """Log every label text in the Advanced Search panel to aid selector tuning."""
        labels = self.page.locator("div.search-item label")
        count = labels.count()
        logging.info("Search-form labels found: %d", count)
        for idx in range(count):
            txt = labels.nth(idx).inner_text().strip()
            has_input = labels.nth(idx).evaluate(
                "el => !!el.nextElementSibling && el.nextElementSibling.tagName.toLowerCase() === 'input'"
            )
            logging.info("[LBL %02d] label='%s' adjacent-input=%s", idx, txt, has_input)

    # ------------------------------------------------------------------
    # Search helpers
    # ------------------------------------------------------------------
    def search_results(self, number_to_look_for: str, return_enhanced: bool = False) -> tuple | BPMSearchResult:
        """Wait for results grid and return tuple from 4th & last columns or enhanced data.

        Enhanced version that supports returning comprehensive column data including
        environment detection and second-to-last column information while maintaining
        backward compatibility with existing tuple return format.

        Args:
            number_to_look_for: The transaction number to search for
            return_enhanced: If True, returns BPMSearchResult; if False, returns tuple

        Returns:
            Union[tuple, BPMSearchResult]:
                - tuple: (fourth_column, last_column) when return_enhanced=False (default)
                - BPMSearchResult: Complete enhanced data when return_enhanced=True
                - ("NotFound", "NotFound") or equivalent BPMSearchResult on error

        Returns ("NotFound", "NotFound") if the number isn’t present or on error.
        """
        try:
            # self.select_all_from_dropdown()  # optional dropdown action
            self.page.wait_for_timeout(2000)
            self.wait_for_page_to_load()

            if return_enhanced:
                # Use enhanced look_for_number method for detailed results
                result = self.look_for_number_enhanced(number_to_look_for, return_enhanced=True)
                
                if isinstance(result, BPMSearchResult):
                    # Enhanced logging for new data fields while preserving existing logs
                    logging.info("4th Column Value: %s", result.fourth_column)
                    logging.info("Last Column Value: %s", result.last_column)
                    logging.info("Second-to-Last Column Value: %s", result.second_to_last_column)
                    logging.info("Environment Detected: %s", result.environment)
                    logging.info("Total Columns: %d", result.total_columns)
                    
                    return result
                else:
                    # Handle unexpected return type (defensive programming)
                    logging.warning(f"Unexpected result type from look_for_number_enhanced: {type(result)}")
                    return self._build_not_found_result()
            else:
                # Backward compatible behavior - use original look_for_number method
                fourth_val, last_val = self.look_for_number(number_to_look_for)
                logging.info("4th Column Value: %s", fourth_val)
                logging.info("Last Column Value: %s", last_val)
                return fourth_val, last_val
                
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error in search_results: %s", e)
            if return_enhanced:
                return self._build_not_found_result()
            else:
                return "NotFound", "NotFound"

    def perform_advanced_search(self, transaction_id: str) -> tuple:
        """Navigate to Search tab, fill reference field, submit, then fetch results."""
        logging.info(
            "Navigating to Search tab and performing advanced search for transaction ID: %s",
            transaction_id,
        )
        self.click_search_tab()
        self.page.wait_for_timeout(1000)
        self.fill_transaction_id(transaction_id)
        self.click_submit_button()
        self.page.wait_for_timeout(1000)
        return self.search_results(transaction_id)

    def click_element_with_dynamic_title(self) -> None:
        try:
            dynamic_title_element = self.page.locator("div.tcell.hover-td").first
            dynamic_title_value = dynamic_title_element.get_attribute("title")
            elements = self.page.locator(
                f"div.tcell.hover-td[title='{dynamic_title_value}']"
            )
            for i in range(elements.count()):
                element = elements.nth(i)
                if element.is_visible():
                    element.click()
                    logging.info(
                        f"Clicked on element {i+1} with class 'tcell hover-td' and title '{dynamic_title_value}'."
                    )
                    break
            else:
                raise Exception(
                    f"No visible element found with title '{dynamic_title_value}'."
                )
        except Exception as e:
            logging.error(
                "Failed to click on the element with title '%s': %s",
                dynamic_title_value,
                e,
            )
            raise

    def click_search_tab(self) -> None:
        """Navigate to the Search tab in BPM.."""
        try:
            logging.info("Navigating to Search.")
            search_tab = self.page.locator("li.nav-item.nav-link a[href='#search']")
            self.safe_click(search_tab, "Search tab")
        except Exception as e:
            logging.error("Failed to click on the Search tab: %s", e)
            raise

    def fill_transaction_id(self, transaction_id: str) -> None:
        """Fill the REFERENCE field in the advanced-search panel with extra diagnostics."""
        try:
            # Target the input directly following the label whose text is exactly 'REFERENCE:'
            # Using Playwright CSS :has-text() for clarity and robustness.
            selector = "div.search-item label:has-text('REFERENCE') + input"
            logging.debug("Looking for REFERENCE input with selector: %s", selector)
            input_field = self.page.locator(selector).first
            if not input_field or not input_field.is_visible():
                logging.error(
                    "REFERENCE input not visible – selector used: %s", selector
                )
                raise ValueError("REFERENCE input field not found or not visible")
            logging.debug("Using input locator: %s", input_field)
            input_field.fill(transaction_id)
            logging.info("Filled transaction id %s in reference field.", transaction_id)
        except Exception as e:
            logging.error("Failed to fill transaction id %s: %s", transaction_id, e)
            raise

    def select_all_from_dropdown(self) -> None:
        try:
            dropdown = self.page.locator("select")
            dropdown.wait_for(state="visible", timeout=5000)
            self.safe_click(dropdown, "'ALL' dropdown")
            dropdown.select_option(value="ALL")
            logging.info("Selected 'ALL' from the dropdown.")
        except Exception as e:
            logging.error("Failed to select 'ALL' from the dropdown: %s", e)
            raise

    def wait_for_page_to_load(self) -> None:
        try:
            self.page.wait_for_load_state("networkidle")
            logging.info("Page has finished loading.")
        except Exception as e:
            logging.error("Failed to wait for the page to finish loading: %s", e)
            raise

    def look_for_number(self, number: str) -> tuple:
        """Enhanced method to extract comprehensive column data with backward compatibility.
        
        This method now uses the new column extraction logic and environment detection
        while maintaining the existing tuple return format for backward compatibility.
        Falls back to original behavior if enhanced extraction fails.
        
        Args:
            number: The transaction number to search for
            
        Returns:
            tuple: (fourth_column, last_column) for backward compatibility
        """
        try:
            # Find all cells with the target number
            number_element = self.page.locator(f"div.tcell[title='{number}']")
            count = number_element.count()

            if count > 0:
                if count > 1:
                    logging.info(
                        f"Found {count} instances of number: {number}. Using the first match."
                    )
                else:
                    logging.info(f"Found the number: {number}")

                # Always use the first element when multiple matches are found
                first_element = number_element.first
                first_element.evaluate(
                    "element => element.scrollIntoView({block: 'center', inline: 'center'})"
                )

                parent_row = first_element.locator(
                    "xpath=ancestor::div[contains(@class, 'trow')]"
                )
                
                try:
                    # Use enhanced column extraction logic with comprehensive error handling
                    all_columns_data = self._extract_all_columns(parent_row)
                    
                    if all_columns_data:
                        # Perform environment detection
                        environment = self._detect_environment(all_columns_data)
                        
                        # Build enhanced result (for internal processing and logging)
                        enhanced_result = self._build_enhanced_result(all_columns_data, environment)
                        
                        # Log enhanced information for debugging and monitoring
                        logging.info(f"Enhanced search completed for {number}:")
                        logging.info(f"  - Total columns: {enhanced_result.total_columns}")
                        logging.info(f"  - Environment detected: {enhanced_result.environment}")
                        logging.info(f"  - Second-to-last column: {enhanced_result.second_to_last_column}")
                        
                        # Return tuple for backward compatibility
                        return enhanced_result.fourth_column, enhanced_result.last_column
                    else:
                        # Fall back to original extraction if enhanced extraction returns no data
                        logging.warning(f"Enhanced extraction returned no columns for {number}, falling back to original method")
                        return self._fallback_to_original_extraction(parent_row)
                        
                except Exception as enhanced_error:
                    # Use comprehensive error handling for extraction failures
                    logging.warning(f"Enhanced extraction failed for {number}, using error handler")
                    fallback_result = self._handle_extraction_failure(number, enhanced_error)
                    return fallback_result.fourth_column, fallback_result.last_column
                    
            else:
                raise Exception(f"Number {number} is not visible.")
                
        except Exception as e:
            logging.error("Failed to look for the number %s: %s", number, e)
            # If the error contains information about multiple elements, treat it as success
            if "resolved to 2 elements" in str(
                e
            ) or "resolved to multiple elements" in str(e):
                logging.info(
                    f"Multiple elements found for {number}, treating as success"
                )
                # Return placeholder values when we can't determine actual values due to multiple elements
                return "NotFound", "NotFound"
            raise

    def _fallback_to_original_extraction(self, parent_row) -> tuple:
        """Fallback method using original column extraction logic.
        
        This method preserves the original extraction behavior for cases where
        the enhanced extraction fails, ensuring system stability and backward
        compatibility.
        
        Args:
            parent_row: Playwright locator for the parent row element
            
        Returns:
            tuple: (fourth_column, last_column) using original extraction logic
        """
        try:
            fourth_column_value = parent_row.locator(
                "div.tcell:nth-child(4)"
            ).inner_text()
            last_column_value = parent_row.locator(
                "div.tcell:last-child"
            ).inner_text()
            
            logging.info("Fallback extraction successful")
            return fourth_column_value, last_column_value
            
        except Exception as fallback_error:
            logging.error(f"Fallback extraction also failed: {fallback_error}")
            return "NotFound", "NotFound"

    def click_first_row_total_column(self) -> None:
        try:
            total_column_element = self.page.locator(
                "div.mtex-datagrid-tbody .trow .tcell.hover-td div"
            ).first
            self.safe_click(total_column_element, "first row of the TOTAL column")
        except Exception as e:
            logging.error(
                "Failed to click on the text in the first row of the TOTAL column: %s",
                e,
            )
            raise

    def _parse_numeric_value(self, text: str) -> Tuple[bool, Optional[int]]:
        """Parse text to extract numeric value if present.
        
        Handles various numeric formats including:
        - Pure numbers: "25", "123"
        - Hyphenated formats: "25-Q1", "27-UAT"
        - Decimal numbers (extracts integer part): "25.5"
        - Mixed text with numbers: "ENV-27", "PACS.008"
        
        Args:
            text: The text string to parse for numeric values
            
        Returns:
            Tuple of (is_numeric: bool, numeric_value: Optional[int])
            - is_numeric: True if a numeric value was found
            - numeric_value: The extracted integer value, or None if not found
        """
        try:
            if not text or not isinstance(text, str):
                return False, None
                
            # Clean the text by stripping whitespace
            cleaned_text = text.strip()
            
            if not cleaned_text:
                return False, None
            
            # Handle pure integer strings
            if cleaned_text.isdigit():
                return True, int(cleaned_text)
            
            # Handle negative numbers
            if cleaned_text.startswith('-') and cleaned_text[1:].isdigit():
                return True, int(cleaned_text)
            
            # Handle decimal numbers (extract integer part)
            if '.' in cleaned_text and cleaned_text.replace('.', '').replace('-', '').isdigit():
                try:
                    float_val = float(cleaned_text)
                    return True, int(float_val)
                except ValueError:
                    pass
            
            # Use regex to find numeric patterns in mixed text
            # Find all numbers and return the first one by position in string
            all_matches = []
            for match in re.finditer(r'(\d+)', cleaned_text):
                all_matches.append((match.start(), int(match.group(1))))
            
            if all_matches:
                # Sort by position and return the first number found
                all_matches.sort(key=lambda x: x[0])
                numeric_value = all_matches[0][1]
                logging.debug(f"Extracted numeric value {numeric_value} from text '{text}' (first number found)")
                return True, numeric_value
            
            # No numeric value found
            logging.debug(f"No numeric value found in text '{text}'")
            return False, None
            
        except (ValueError, AttributeError, TypeError) as e:
            logging.debug(f"Error parsing numeric value from text '{text}': {e}")
            return False, None

    def _safe_extract_columns(self, parent_row) -> List[ColumnData]:
        """Safely extract columns with comprehensive error handling.
        
        This method provides enhanced error handling for column extraction with
        try-catch for each individual column, graceful degradation when column
        extraction fails, and appropriate error logging without exposing sensitive data.
        
        Args:
            parent_row: Playwright locator for the parent row element
            
        Returns:
            List[ColumnData]: List of column data objects, with error placeholders
                            for failed extractions to maintain position consistency
        """
        columns = []
        
        try:
            if not parent_row:
                logging.warning("No parent row provided for safe column extraction")
                return columns
            
            # Get all table cells in the row with error handling
            try:
                all_cells = parent_row.locator("div.tcell")
                cell_count = all_cells.count()
            except Exception as locator_error:
                logging.error(f"Failed to locate table cells in parent row: {locator_error}")
                return columns
            
            if cell_count == 0:
                logging.warning("No cells found in result row during safe extraction")
                return columns
            
            logging.debug(f"Safely extracting data from {cell_count} columns")
            
            # Extract data from each cell with individual error handling
            for i in range(cell_count):
                column_data = None
                
                try:
                    # Attempt to get the cell locator
                    try:
                        cell = all_cells.nth(i)
                    except Exception as cell_locator_error:
                        logging.warning(f"Failed to get locator for column {i+1}: {cell_locator_error}")
                        raise Exception(f"Cell locator failed: {cell_locator_error}")
                    
                    # Extract text content with error handling
                    cell_text = ""
                    try:
                        cell_text = cell.inner_text().strip()
                    except Exception as text_error:
                        logging.warning(f"Failed to extract text from column {i+1}: {text_error}")
                        # Continue with empty string rather than failing completely
                        cell_text = ""
                    
                    # Apply numeric parsing with error handling
                    is_numeric = False
                    numeric_value = None
                    try:
                        is_numeric, numeric_value = self._parse_numeric_value(cell_text)
                    except Exception as parse_error:
                        logging.warning(f"Failed to parse numeric value for column {i+1}: {parse_error}")
                        # Continue with non-numeric defaults
                        is_numeric = False
                        numeric_value = None
                    
                    # Create column data object
                    column_data = ColumnData(
                        position=i + 1,  # 1-based position
                        value=cell_text,
                        is_numeric=is_numeric,
                        numeric_value=numeric_value
                    )
                    
                    logging.debug(f"Column {i+1}: '{cell_text}' (numeric: {is_numeric}, value: {numeric_value})")
                    
                except Exception as cell_error:
                    # Log error without exposing sensitive data
                    logging.error(f"Error extracting data from column {i+1}: {type(cell_error).__name__}")
                    logging.debug(f"Detailed error for column {i+1}: {cell_error}")
                    
                    # Create placeholder column to maintain position consistency
                    column_data = ColumnData(
                        position=i + 1,
                        value="ExtractionError",
                        is_numeric=False,
                        numeric_value=None
                    )
                
                # Add the column data (either successful or placeholder)
                if column_data:
                    columns.append(column_data)
            
            successful_extractions = len([col for col in columns if col.value != "ExtractionError"])
            failed_extractions = len(columns) - successful_extractions
            
            if failed_extractions > 0:
                logging.warning(f"Column extraction completed with {failed_extractions} failures out of {len(columns)} columns")
            else:
                logging.info(f"Successfully extracted data from all {len(columns)} columns")
            
            return columns
            
        except Exception as e:
            # Log critical error without exposing sensitive data
            logging.error(f"Critical error in safe column extraction: {type(e).__name__}")
            logging.debug(f"Detailed critical error: {e}")
            return columns

    def _extract_all_columns(self, parent_row) -> List[ColumnData]:
        """Extract data from all columns in the result row.
        
        This method now uses the safe extraction approach with comprehensive
        error handling. It delegates to _safe_extract_columns for the actual
        extraction work while maintaining the same interface.
        
        Args:
            parent_row: Playwright locator for the parent row element
            
        Returns:
            List[ColumnData]: List of column data objects with position, value, 
                            and numeric information for each column
        """
        return self._safe_extract_columns(parent_row)

    def _detect_environment(self, columns: List[ColumnData]) -> str:
        """Detect environment based on numeric values in columns.
        
        Scans all columns for numeric values and classifies the environment based on
        the first qualifying numeric value found:
        - Values 25-29: "buat" environment
        - Values outside 25-29: "uat" environment  
        - No numeric values found: "unknown" environment
        
        Args:
            columns: List of ColumnData objects to scan for numeric values
            
        Returns:
            str: Environment classification ("buat", "uat", or "unknown")
        """
        try:
            if not columns or not isinstance(columns, list):
                logging.debug("No columns provided for environment detection")
                return "unknown"
            
            # Scan columns in order for numeric values
            for column in columns:
                if not isinstance(column, ColumnData):
                    logging.debug(f"Skipping invalid column data: {column}")
                    continue
                    
                if column.is_numeric and column.numeric_value is not None:
                    numeric_value = column.numeric_value
                    
                    # Check if value is in BUAT range (25-29 inclusive)
                    if 25 <= numeric_value <= 29:
                        logging.info(f"Environment 'buat' detected from column {column.position} value {numeric_value}")
                        return "buat"
                    else:
                        # Any other numeric value indicates UAT environment
                        logging.info(f"Environment 'uat' detected from column {column.position} value {numeric_value}")
                        return "uat"
            
            # No qualifying numeric values found
            logging.info("No qualifying numeric values found, environment unknown")
            return "unknown"
            
        except Exception as e:
            logging.error(f"Error during environment detection: {e}")
            return "unknown"

    def _build_enhanced_result(self, columns: List[ColumnData], environment: str) -> BPMSearchResult:
        """Build the enhanced result structure from extracted column data.
        
        Constructs a BPMSearchResult object with all column data, environment detection,
        and backward compatibility fields. Extracts specific columns (4th, last, 
        second-to-last) for backward compatibility while providing comprehensive data.
        
        Args:
            columns: List of ColumnData objects from column extraction
            environment: Environment classification from environment detection
            
        Returns:
            BPMSearchResult: Complete search result with all extracted data and metadata
        """
        try:
            if not columns or not isinstance(columns, list):
                logging.warning("No columns provided for result building, creating empty result")
                return self._build_not_found_result()
            
            total_cols = len(columns)
            logging.debug(f"Building enhanced result from {total_cols} columns")
            
            # Extract specific columns for backward compatibility
            # 4th column (index 3)
            fourth_column = columns[3].value if total_cols > 3 else "NotFound"
            
            # Last column
            last_column = columns[-1].value if total_cols > 0 else "NotFound"
            
            # Second-to-last column  
            second_to_last = columns[-2].value if total_cols > 1 else "NotFound"
            
            # Generate timestamp
            search_timestamp = datetime.now().isoformat()
            
            # Create the enhanced result
            result = BPMSearchResult(
                # Backward compatibility fields
                fourth_column=fourth_column,
                last_column=last_column,
                
                # Enhanced fields
                all_columns=columns,
                second_to_last_column=second_to_last,
                environment=environment,
                total_columns=total_cols,
                
                # Metadata
                transaction_found=True,
                search_timestamp=search_timestamp
            )
            
            logging.info(f"Enhanced result built successfully: {total_cols} columns, environment: {environment}")
            logging.debug(f"Fourth column: '{fourth_column}', Last column: '{last_column}', Second-to-last: '{second_to_last}'")
            
            return result
            
        except Exception as e:
            logging.error(f"Error building enhanced result: {e}")
            # Return a not found result as fallback
            return self._build_not_found_result()

    def _handle_extraction_failure(self, number: str, error: Exception) -> BPMSearchResult:
        """Handle cases where enhanced extraction fails with fallback scenarios.
        
        This method implements graceful degradation when column extraction fails
        by attempting to fall back to the original extraction method. If that also
        fails, it returns a safe default result structure. Provides appropriate
        error logging without exposing sensitive data.
        
        Args:
            number: The transaction number that was being searched for
            error: The exception that caused the extraction failure
            
        Returns:
            BPMSearchResult: Result structure with fallback data or safe defaults
        """
        # Log the extraction failure without exposing sensitive data
        logging.error(f"Enhanced extraction failed for transaction search: {type(error).__name__}")
        logging.debug(f"Detailed extraction failure for number {number}: {error}")
        
        try:
            # Attempt fallback to original extraction method
            logging.info("Attempting fallback to original extraction method")
            
            # Try to find the element again for fallback extraction
            try:
                number_element = self.page.locator(f"div.tcell[title='{number}']")
                count = number_element.count()
                
                if count > 0:
                    first_element = number_element.first
                    parent_row = first_element.locator("xpath=ancestor::div[contains(@class, 'trow')]")
                    
                    # Use the original fallback extraction method
                    fourth_val, last_val = self._fallback_to_original_extraction(parent_row)
                    
                    # Create enhanced result from fallback data
                    fallback_result = BPMSearchResult(
                        fourth_column=fourth_val,
                        last_column=last_val,
                        all_columns=[],  # No detailed column data available
                        second_to_last_column="ExtractionFailed",
                        environment="unknown",  # Cannot determine without column data
                        total_columns=0,  # Unknown due to extraction failure
                        transaction_found=fourth_val != "NotFound",
                        search_timestamp=datetime.now().isoformat()
                    )
                    
                    logging.info("Fallback extraction successful, returning partial data")
                    return fallback_result
                    
                else:
                    logging.warning("Element not found during fallback extraction")
                    
            except Exception as fallback_error:
                logging.error(f"Fallback extraction also failed: {type(fallback_error).__name__}")
                logging.debug(f"Detailed fallback error: {fallback_error}")
                
        except Exception as handler_error:
            logging.error(f"Error in extraction failure handler: {type(handler_error).__name__}")
            logging.debug(f"Detailed handler error: {handler_error}")
        
        # Final fallback: return not found result
        logging.info("All extraction methods failed, returning not found result")
        return self._build_not_found_result()

    def _build_not_found_result(self) -> BPMSearchResult:
        """Build result structure for when no transaction is found or errors occur.
        
        Creates a BPMSearchResult with appropriate "NotFound" values for all fields,
        maintaining consistency with existing error handling behavior while providing
        the enhanced data structure.
        
        Returns:
            BPMSearchResult: Result structure indicating no transaction was found
        """
        try:
            search_timestamp = datetime.now().isoformat()
            
            result = BPMSearchResult(
                # Backward compatibility fields with "NotFound" values
                fourth_column="NotFound",
                last_column="NotFound",
                
                # Enhanced fields with appropriate defaults
                all_columns=[],  # Empty list when no data found
                second_to_last_column="NotFound",
                environment="unknown",  # Cannot determine environment without data
                total_columns=0,
                
                # Metadata indicating failure
                transaction_found=False,
                search_timestamp=search_timestamp
            )
            
            logging.debug("Built not found result structure")
            return result
            
        except Exception as e:
            logging.error(f"Error building not found result: {e}")
            # Create minimal fallback result even if timestamp generation fails
            return BPMSearchResult(
                fourth_column="NotFound",
                last_column="NotFound",
                all_columns=[],
                second_to_last_column="NotFound", 
                environment="unknown",
                total_columns=0,
                transaction_found=False,
                search_timestamp="unknown"
            )

    def look_for_number_enhanced(self, number: str, return_enhanced: bool = False) -> tuple | BPMSearchResult:
        """Enhanced version of look_for_number with optional detailed return.
        
        This method provides backward compatibility by allowing callers to choose
        between the traditional tuple return format and the new enhanced BPMSearchResult
        format. Existing callers continue to work without modification, while new
        callers can opt into enhanced data by setting return_enhanced=True.
        
        Args:
            number: The transaction number to search for
            return_enhanced: If True, returns BPMSearchResult; if False, returns tuple
            
        Returns:
            Union[tuple, BPMSearchResult]: 
                - tuple: (fourth_column, last_column) when return_enhanced=False
                - BPMSearchResult: Complete enhanced data when return_enhanced=True
        """
        try:
            # Find all cells with the target number
            number_element = self.page.locator(f"div.tcell[title='{number}']")
            count = number_element.count()

            if count > 0:
                if count > 1:
                    logging.info(
                        f"Found {count} instances of number: {number}. Using the first match."
                    )
                else:
                    logging.info(f"Found the number: {number}")

                # Always use the first element when multiple matches are found
                first_element = number_element.first
                first_element.evaluate(
                    "element => element.scrollIntoView({block: 'center', inline: 'center'})"
                )

                parent_row = first_element.locator(
                    "xpath=ancestor::div[contains(@class, 'trow')]"
                )
                
                try:
                    # Use enhanced column extraction logic with comprehensive error handling
                    all_columns_data = self._extract_all_columns(parent_row)
                    
                    if all_columns_data:
                        # Perform environment detection
                        environment = self._detect_environment(all_columns_data)
                        
                        # Build enhanced result
                        enhanced_result = self._build_enhanced_result(all_columns_data, environment)
                        
                        # Enhanced logging for new data fields while preserving existing logs
                        logging.info("4th Column Value: %s", enhanced_result.fourth_column)
                        logging.info("Last Column Value: %s", enhanced_result.last_column)
                        logging.info("Second-to-Last Column Value: %s", enhanced_result.second_to_last_column)
                        logging.info("Environment Detected: %s", enhanced_result.environment)
                        logging.info("Total Columns: %d", enhanced_result.total_columns)
                        
                        # Return based on requested format
                        if return_enhanced:
                            return enhanced_result
                        else:
                            # Return tuple for backward compatibility
                            return enhanced_result.fourth_column, enhanced_result.last_column
                    else:
                        # Fall back to original extraction if enhanced extraction returns no data
                        logging.warning(f"Enhanced extraction returned no columns for {number}, falling back to original method")
                        fourth_val, last_val = self._fallback_to_original_extraction(parent_row)
                        
                        if return_enhanced:
                            # Create minimal enhanced result from fallback data
                            fallback_result = BPMSearchResult(
                                fourth_column=fourth_val,
                                last_column=last_val,
                                all_columns=[],
                                second_to_last_column="NotFound",
                                environment="unknown",
                                total_columns=0,
                                transaction_found=fourth_val != "NotFound",
                                search_timestamp=datetime.now().isoformat()
                            )
                            return fallback_result
                        else:
                            return fourth_val, last_val
                        
                except Exception as enhanced_error:
                    # Use comprehensive error handling for extraction failures
                    logging.warning(f"Enhanced extraction failed for {number}, using error handler")
                    fallback_result = self._handle_extraction_failure(number, enhanced_error)
                    
                    if return_enhanced:
                        return fallback_result
                    else:
                        return fallback_result.fourth_column, fallback_result.last_column
                    
            else:
                raise Exception(f"Number {number} is not visible.")
                
        except Exception as e:
            logging.error("Failed to look for the number %s: %s", number, e)
            
            # Handle multiple elements case
            if "resolved to 2 elements" in str(e) or "resolved to multiple elements" in str(e):
                logging.info(f"Multiple elements found for {number}, treating as success")
                if return_enhanced:
                    return self._build_not_found_result()
                else:
                    return "NotFound", "NotFound"
            
            # Return appropriate format based on request
            if return_enhanced:
                return self._build_not_found_result()
            else:
                return "NotFound", "NotFound"

    def search_results_enhanced(self, number_to_look_for: str, return_enhanced: bool = False) -> tuple | BPMSearchResult:
        """Enhanced version of search_results with optional detailed return.
        
        Wait for results grid and return either tuple from 4th & last columns (backward compatible)
        or complete BPMSearchResult with all column data and environment detection.
        Maintains existing error handling behavior while adding enhanced logging.
        
        Args:
            number_to_look_for: The transaction number to search for
            return_enhanced: If True, returns BPMSearchResult; if False, returns tuple
            
        Returns:
            Union[tuple, BPMSearchResult]:
                - tuple: (fourth_column, last_column) when return_enhanced=False  
                - BPMSearchResult: Complete enhanced data when return_enhanced=True
                - ("NotFound", "NotFound") or equivalent BPMSearchResult on error
        """
        try:
            # Wait for page to be ready (preserving existing behavior)
            self.page.wait_for_timeout(2000)
            self.wait_for_page_to_load()

            # Use the enhanced look_for_number method
            result = self.look_for_number_enhanced(number_to_look_for, return_enhanced=True)
            
            # Enhanced logging for new data fields while preserving existing logs
            if isinstance(result, BPMSearchResult):
                # Log traditional values for backward compatibility
                logging.info("4th Column Value: %s", result.fourth_column)
                logging.info("Last Column Value: %s", result.last_column)
                
                # Log new enhanced values
                logging.info("Second-to-Last Column Value: %s", result.second_to_last_column)
                logging.info("Environment Detected: %s", result.environment)
                logging.info("Total Columns: %d", result.total_columns)
                
                # Return in requested format
                if return_enhanced:
                    return result
                else:
                    return result.fourth_column, result.last_column
            else:
                # Handle unexpected return type (should not happen, but defensive programming)
                logging.warning(f"Unexpected result type from look_for_number_enhanced: {type(result)}")
                if return_enhanced:
                    return self._build_not_found_result()
                else:
                    return "NotFound", "NotFound"
                    
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error in enhanced search_results: %s", e)
            if return_enhanced:
                return self._build_not_found_result()
            else:
                return "NotFound", "NotFound"

    # ------------------------------------------------------------------
    # Helper methods for data access
    # ------------------------------------------------------------------
    
    def get_column_by_position(self, result: BPMSearchResult, position: int) -> Optional[ColumnData]:
        """Get column data by position with bounds checking.
        
        Utility method for accessing specific column data from a BPMSearchResult
        with proper validation and bounds checking to prevent index errors.
        
        Args:
            result: BPMSearchResult object containing column data
            position: 1-based column position to retrieve
            
        Returns:
            Optional[ColumnData]: Column data if found, None if position is invalid
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for column access: {type(result)}")
                return None
                
            if not result.all_columns:
                logging.debug("No columns available in result")
                return None
                
            if position < 1:
                logging.warning(f"Invalid column position {position}: must be >= 1")
                return None
                
            if position > len(result.all_columns):
                logging.debug(f"Column position {position} exceeds available columns ({len(result.all_columns)})")
                return None
                
            # Convert to 0-based index
            column_index = position - 1
            column_data = result.all_columns[column_index]
            
            logging.debug(f"Retrieved column {position}: '{column_data.value}'")
            return column_data
            
        except Exception as e:
            logging.error(f"Error accessing column at position {position}: {e}")
            return None

    def get_column_value_by_position(self, result: BPMSearchResult, position: int, default: str = "NotFound") -> str:
        """Get column value by position with default fallback.
        
        Convenience method for accessing column values with automatic fallback
        to a default value when the column is not found or invalid.
        
        Args:
            result: BPMSearchResult object containing column data
            position: 1-based column position to retrieve
            default: Default value to return if column not found
            
        Returns:
            str: Column value or default if not found
        """
        try:
            column_data = self.get_column_by_position(result, position)
            if column_data:
                return column_data.value
            else:
                logging.debug(f"Column {position} not found, returning default: '{default}'")
                return default
                
        except Exception as e:
            logging.error(f"Error getting column value at position {position}: {e}")
            return default

    def get_numeric_columns(self, result: BPMSearchResult) -> List[ColumnData]:
        """Get all columns that contain numeric values.
        
        Utility method for filtering columns to only those that contain
        numeric data, useful for environment detection and data analysis.
        
        Args:
            result: BPMSearchResult object containing column data
            
        Returns:
            List[ColumnData]: List of columns with numeric values
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for numeric column access: {type(result)}")
                return []
                
            if not result.all_columns:
                logging.debug("No columns available for numeric filtering")
                return []
                
            numeric_columns = [col for col in result.all_columns if col.is_numeric and col.numeric_value is not None]
            
            logging.debug(f"Found {len(numeric_columns)} numeric columns out of {len(result.all_columns)} total")
            return numeric_columns
            
        except Exception as e:
            logging.error(f"Error filtering numeric columns: {e}")
            return []

    def get_environment_info(self, result: BPMSearchResult) -> dict:
        """Get detailed environment information and metadata.
        
        Returns comprehensive information about the detected environment including
        classification details, numeric ranges, and descriptive metadata.
        
        Args:
            result: BPMSearchResult object containing environment data
            
        Returns:
            dict: Environment information with classification details
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for environment info: {type(result)}")
                return self._get_default_environment_info("unknown")
                
            environment = result.environment
            
            # Get numeric columns for additional context
            numeric_columns = self.get_numeric_columns(result)
            numeric_values = [col.numeric_value for col in numeric_columns if col.numeric_value is not None]
            
            env_info = {
                "environment": environment,
                "classification": self._get_environment_classification(environment),
                "numeric_values_found": numeric_values,
                "numeric_column_count": len(numeric_columns),
                "total_columns": result.total_columns,
                "detection_timestamp": result.search_timestamp
            }
            
            # Add environment-specific details
            if environment == "buat":
                env_info["qualifying_range"] = "25-29"
                env_info["description"] = "Business User Acceptance Testing environment"
            elif environment == "uat":
                env_info["qualifying_range"] = "Outside 25-29"
                env_info["description"] = "User Acceptance Testing environment"
            else:
                env_info["qualifying_range"] = "No numeric values found"
                env_info["description"] = "Environment could not be determined"
                
            logging.debug(f"Environment info generated for '{environment}': {len(numeric_values)} numeric values")
            return env_info
            
        except Exception as e:
            logging.error(f"Error getting environment info: {e}")
            return self._get_default_environment_info("unknown")

    def _get_environment_classification(self, environment: str) -> str:
        """Get human-readable environment classification.
        
        Args:
            environment: Environment string ("buat", "uat", "unknown")
            
        Returns:
            str: Human-readable classification
        """
        classifications = {
            "buat": "Business User Acceptance Testing",
            "uat": "User Acceptance Testing",
            "unknown": "Unknown Environment"
        }
        return classifications.get(environment, "Unknown Environment")

    def _get_default_environment_info(self, environment: str) -> dict:
        """Get default environment info structure for error cases.
        
        Args:
            environment: Environment string to use as default
            
        Returns:
            dict: Default environment information structure
        """
        return {
            "environment": environment,
            "classification": self._get_environment_classification(environment),
            "numeric_values_found": [],
            "numeric_column_count": 0,
            "total_columns": 0,
            "detection_timestamp": datetime.now().isoformat(),
            "qualifying_range": "Unknown",
            "description": "Environment information unavailable"
        }

    def validate_column_count(self, result: BPMSearchResult, expected_min: int = 1, expected_max: Optional[int] = None) -> bool:
        """Validate that the result has an acceptable number of columns.
        
        Performs bounds checking on the column count to ensure the result
        contains the expected number of columns for processing.
        
        Args:
            result: BPMSearchResult object to validate
            expected_min: Minimum expected number of columns (default: 1)
            expected_max: Maximum expected number of columns (optional)
            
        Returns:
            bool: True if column count is within expected bounds, False otherwise
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for column count validation: {type(result)}")
                return False
                
            column_count = result.total_columns
            
            # Check minimum bound
            if column_count < expected_min:
                logging.warning(f"Column count {column_count} below minimum {expected_min}")
                return False
                
            # Check maximum bound if specified
            if expected_max is not None and column_count > expected_max:
                logging.warning(f"Column count {column_count} exceeds maximum {expected_max}")
                return False
                
            logging.debug(f"Column count validation passed: {column_count} columns (min: {expected_min}, max: {expected_max})")
            return True
            
        except Exception as e:
            logging.error(f"Error validating column count: {e}")
            return False

    def has_required_columns(self, result: BPMSearchResult, required_positions: List[int]) -> bool:
        """Check if result has data at all required column positions.
        
        Validates that the result contains valid data at all specified
        column positions, useful for ensuring required fields are present.
        
        Args:
            result: BPMSearchResult object to check
            required_positions: List of 1-based column positions that must have data
            
        Returns:
            bool: True if all required positions have valid data, False otherwise
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for required columns check: {type(result)}")
                return False
                
            if not required_positions:
                logging.debug("No required positions specified, validation passes")
                return True
                
            missing_positions = []
            
            for position in required_positions:
                column_data = self.get_column_by_position(result, position)
                if not column_data or not column_data.value or column_data.value in ["NotFound", "ExtractionError", ""]:
                    missing_positions.append(position)
                    
            if missing_positions:
                logging.warning(f"Missing required data at column positions: {missing_positions}")
                return False
            else:
                logging.debug(f"All required column positions have valid data: {required_positions}")
                return True
                
        except Exception as e:
            logging.error(f"Error checking required columns: {e}")
            return False

    def get_column_summary(self, result: BPMSearchResult) -> dict:
        """Get summary information about all columns in the result.
        
        Provides a comprehensive overview of the column data including
        counts, types, and key values for analysis and debugging.
        
        Args:
            result: BPMSearchResult object to summarize
            
        Returns:
            dict: Summary information about columns
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for column summary: {type(result)}")
                return {"error": "Invalid result type"}
                
            if not result.all_columns:
                return {
                    "total_columns": 0,
                    "numeric_columns": 0,
                    "empty_columns": 0,
                    "error_columns": 0,
                    "environment": result.environment,
                    "transaction_found": result.transaction_found
                }
                
            # Count different column types
            numeric_count = len([col for col in result.all_columns if col.is_numeric])
            empty_count = len([col for col in result.all_columns if not col.value or col.value.strip() == ""])
            error_count = len([col for col in result.all_columns if col.value == "ExtractionError"])
            
            # Get key column values
            key_columns = {}
            if result.total_columns >= 4:
                key_columns["fourth_column"] = result.fourth_column
            if result.total_columns >= 1:
                key_columns["last_column"] = result.last_column
            if result.total_columns >= 2:
                key_columns["second_to_last_column"] = result.second_to_last_column
                
            summary = {
                "total_columns": result.total_columns,
                "numeric_columns": numeric_count,
                "empty_columns": empty_count,
                "error_columns": error_count,
                "environment": result.environment,
                "transaction_found": result.transaction_found,
                "key_columns": key_columns,
                "search_timestamp": result.search_timestamp
            }
            
            # Add numeric values if any found
            numeric_columns = self.get_numeric_columns(result)
            if numeric_columns:
                summary["numeric_values"] = [col.numeric_value for col in numeric_columns]
                
            logging.debug(f"Column summary generated: {summary['total_columns']} total, {summary['numeric_columns']} numeric")
            return summary
            
        except Exception as e:
            logging.error(f"Error generating column summary: {e}")
            return {"error": f"Summary generation failed: {type(e).__name__}"}

    def find_columns_with_pattern(self, result: BPMSearchResult, pattern: str, case_sensitive: bool = False) -> List[ColumnData]:
        """Find columns whose values match a specific pattern.
        
        Searches through all columns to find those whose values contain
        or match the specified pattern, useful for finding specific data types.
        
        Args:
            result: BPMSearchResult object to search
            pattern: Regular expression pattern to match
            case_sensitive: Whether the pattern matching should be case sensitive
            
        Returns:
            List[ColumnData]: List of columns matching the pattern
        """
        try:
            if not isinstance(result, BPMSearchResult):
                logging.warning(f"Invalid result type for pattern search: {type(result)}")
                return []
                
            if not result.all_columns:
                logging.debug("No columns available for pattern search")
                return []
                
            if not pattern:
                logging.warning("Empty pattern provided for column search")
                return []
                
            import re
            
            # Compile regex pattern with appropriate flags
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(pattern, flags)
            except re.error as regex_error:
                logging.error(f"Invalid regex pattern '{pattern}': {regex_error}")
                return []
                
            matching_columns = []
            
            for column in result.all_columns:
                if column.value and compiled_pattern.search(column.value):
                    matching_columns.append(column)
                    logging.debug(f"Column {column.position} matches pattern '{pattern}': '{column.value}'")
                    
            logging.info(f"Found {len(matching_columns)} columns matching pattern '{pattern}'")
            return matching_columns
            
        except Exception as e:
            logging.error(f"Error searching columns with pattern '{pattern}': {e}")
            return []

    # Performance-optimized methods
    def enable_performance_mode(self):
        """Enable performance optimizations by replacing methods with optimized versions."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            logging.warning("Performance optimizations not available")
            return False
        
        if self._performance_mode_enabled:
            logging.info("Performance mode already enabled")
            return True
        
        # Store original methods for restoration
        self._original_extract_all_columns = self._extract_all_columns
        self._original_detect_environment = self._detect_environment
        self._original_parse_numeric_value = self._parse_numeric_value
        
        # Replace with optimized versions
        self._extract_all_columns = self._optimized_extract_all_columns
        self._detect_environment = self._optimized_detect_environment
        self._parse_numeric_value = self._optimized_parse_numeric_value
        
        self._performance_mode_enabled = True
        logging.info("Performance mode enabled - using optimized methods")
        return True
    
    def disable_performance_mode(self):
        """Disable performance optimizations by restoring original methods."""
        if not self._performance_mode_enabled:
            logging.info("Performance mode not enabled")
            return True
        
        # Restore original methods
        if hasattr(self, '_original_extract_all_columns'):
            self._extract_all_columns = self._original_extract_all_columns
        if hasattr(self, '_original_detect_environment'):
            self._detect_environment = self._original_detect_environment
        if hasattr(self, '_original_parse_numeric_value'):
            self._parse_numeric_value = self._original_parse_numeric_value
        
        self._performance_mode_enabled = False
        logging.info("Performance mode disabled - using original methods")
        return True
    
    def _optimized_extract_all_columns(self, parent_row):
        """Optimized column extraction using batch text extraction."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            return self._safe_extract_columns(parent_row)
        return self.performance_optimizer._optimized_extract_all_columns(parent_row)
    
    def _optimized_detect_environment(self, columns):
        """Optimized environment detection using caching."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            # Fallback to original logic
            try:
                if not columns or not isinstance(columns, list):
                    return "unknown"
                
                for column in columns:
                    if hasattr(column, 'is_numeric') and hasattr(column, 'numeric_value'):
                        if column.is_numeric and column.numeric_value is not None:
                            if 25 <= column.numeric_value <= 29:
                                return "buat"
                            else:
                                return "uat"
                return "unknown"
            except Exception:
                return "unknown"
        
        return self.performance_optimizer._optimized_detect_environment(columns)
    
    def _optimized_parse_numeric_value(self, text: str):
        """Optimized numeric parsing using caching."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            # Fallback to original method
            return self._parse_numeric_value_original(text)
        return self.performance_optimizer._optimized_parse_numeric_value(text)
    
    def _parse_numeric_value_original(self, text: str):
        """Original numeric parsing method as fallback."""
        try:
            if not text or not isinstance(text, str):
                return False, None
                
            cleaned_text = text.strip()
            if not cleaned_text:
                return False, None
            
            if cleaned_text.isdigit():
                return True, int(cleaned_text)
            
            if cleaned_text.startswith('-') and cleaned_text[1:].isdigit():
                return True, int(cleaned_text)
            
            if '.' in cleaned_text and cleaned_text.replace('.', '').replace('-', '').isdigit():
                try:
                    float_val = float(cleaned_text)
                    return True, int(float_val)
                except ValueError:
                    pass
            
            import re
            all_matches = []
            for match in re.finditer(r'(\\d+)', cleaned_text):
                all_matches.append((match.start(), int(match.group(1))))
            
            if all_matches:
                all_matches.sort(key=lambda x: x[0])
                numeric_value = all_matches[0][1]
                return True, numeric_value
            
            return False, None
            
        except (ValueError, AttributeError, TypeError):
            return False, None
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics from operations."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            return {"error": "Performance optimizations not available"}
        return self.performance_optimizer.get_performance_metrics()
    
    def log_performance_metrics(self):
        """Log performance metrics and cache statistics."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE or not self.performance_optimizer:
            logging.warning("Performance optimizations not available")
            return
        self.performance_optimizer.log_performance_metrics()
    
    def clear_performance_caches(self):
        """Clear all performance caches."""
        if not PERFORMANCE_OPTIMIZATIONS_AVAILABLE:
            logging.warning("Performance optimizations not available")
            return
        PerformanceOptimizer.clear_caches()
        logging.info("Performance caches cleared")
    
    def is_performance_mode_enabled(self) -> bool:
        """Check if performance mode is currently enabled."""
        return getattr(self, '_performance_mode_enabled', False)


# --- Modular Actions moved from bpm.py ---
def perform_login_and_setup(
    bpm_page: BPMPage, test_url: str, username: str, password: str
):
    """Clear browser cookies and perform the initial BPM login/setup steps."""
    logging.info("Starting login and setup flow.")
    bpm_page.page.context.clear_cookies()

    bpm_page.login(test_url, username, password)
    bpm_page.verify_modal_visibility()
    bpm_page.click_tick_box()
    bpm_page.click_ori_tsf()
    logging.info("Login and initial setup completed.")



def map_transaction_type_to_option(transaction_type_str: str):
    """Map a transaction type string (from UI) to the corresponding Options enum.

    The front-end sends the HTML option `value` – this may match either the
    Enum *name* (e.g. ``APS_MT``) **or** the Enum *value* (e.g. ``APS-MT``).
    This helper normalises the input and returns a list with the matching
    ``Options`` entry so ``check_options`` can click the right item.
    """
    if not transaction_type_str:
        logging.warning("Transaction type string is empty – no options to map.")
        return []

    # 1. Try direct Enum name match (case-sensitive)
    if transaction_type_str in Options.__members__:
        return [Options[transaction_type_str]]

    # 2. Fallback: compare against Enum values (case-insensitive)
    for opt in Options:
        if opt.value.lower() == transaction_type_str.lower():
            return [opt]

    logging.warning(
        "Unknown transaction type received from UI: %s", transaction_type_str
    )
    return []
