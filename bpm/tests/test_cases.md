# Test Cases for Firco Transaction Processing System

## Overview
This document outlines test cases for the Firco transaction processing system, which automates transaction handling through a web interface. The test cases cover various scenarios including transaction search, action execution, error handling, and integration with BPM.

## Environment Setup Tests

### ENV-001: Environment Variables Configuration
**Description:** Verify that the application correctly loads environment variables from .env file or uses defaults.
**Preconditions:** 
- .env file exists with test configuration
**Steps:**
1. Run the application with .env file present
2. Run the application with .env file removed
**Expected Results:**
- Application uses values from .env when present
- Application falls back to default values when .env is absent

### ENV-002: Directory Structure Creation
**Description:** Verify that the application creates the required directory structure.
**Steps:**
1. Delete existing output directories
2. Process a test transaction
**Expected Results:**
- Output directory structure is created with transaction-specific folders
- Screenshots are moved to the correct folders

## Login Tests

### LOGIN-001: Successful Login
**Description:** Verify that the application can successfully log in to the Firco system.
**Steps:**
1. Call login_to_firco with valid credentials
**Expected Results:**
- Login succeeds
- Page navigates to the main Firco interface

### LOGIN-002: Failed Login
**Description:** Verify that the application handles login failures gracefully.
**Steps:**
1. Call login_to_firco with invalid credentials
**Expected Results:**
- Application catches the authentication error
- Appropriate error message is logged

## Transaction Search Tests

### SEARCH-001: Transaction Found in Live Messages
**Description:** Verify that the system can find a transaction in Live Messages.
**Preconditions:**
- Transaction exists in Live Messages tab
**Steps:**
1. Call go_to_transaction_details with the transaction ID
**Expected Results:**
- Transaction is found
- Status "found_in_live" is returned
- Comment field is filled

### SEARCH-002: Transaction Found in History
**Description:** Verify that the system can find a transaction in History.
**Preconditions:**
- Transaction exists in History tab
**Steps:**
1. Call go_to_transaction_details with the transaction ID
**Expected Results:**
- Transaction is found
- Status "already_handled" is returned

### SEARCH-003: Multiple Transactions Found
**Description:** Verify that the system handles multiple matching transactions correctly.
**Preconditions:**
- Multiple transactions with the same ID exist
**Steps:**
1. Call go_to_transaction_details with perform_on_latest=False
2. Call go_to_transaction_details with perform_on_latest=True
**Expected Results:**
- With perform_on_latest=False: TransactionError is raised
- With perform_on_latest=True: Latest transaction is selected

### SEARCH-004: Transaction Not Found
**Description:** Verify that the system handles transactions not found in any tab.
**Preconditions:**
- Transaction does not exist in any tab
**Steps:**
1. Call go_to_transaction_details with a non-existent transaction ID
**Expected Results:**
- BPM search is attempted
- Status "transaction_not_found_in_any_tab" is returned if not found in BPM

## BPM Integration Tests

### BPM-001: Transaction Found in BPM
**Description:** Verify that the system can find a transaction in BPM.
**Preconditions:**
- Transaction exists in BPM
**Steps:**
1. Call check_bpm_page with the transaction ID and type
**Expected Results:**
- Transaction is found in BPM
- Status "found_in_bpm" is returned with appropriate message

### BPM-002: BPM Search Failure
**Description:** Verify that the system handles BPM search failures gracefully.
**Steps:**
1. Call check_bpm_page with conditions that would cause BPM search to fail
**Expected Results:**
- System attempts retries
- Status "failed_in_bpm" is returned after max retries

### BPM-003: BPM Page Reload Loop
**Description:** Verify that the system handles BPM page reload loops correctly.
**Steps:**
1. Simulate a BPM page reload loop during search
**Expected Results:**
- System detects the reload loop
- Retry mechanism is triggered
- Browser context is reset between retries

## Transaction Action Tests

### ACTION-001: STP-Release Action
**Description:** Verify that the system can perform STP-Release action.
**Preconditions:**
- Transaction exists in Live Messages
**Steps:**
1. Call process_firco_transaction with action="STP-Release"
**Expected Results:**
- STP-Release button is clicked
- Confirm button is clicked
- Status "action_performed_on_live" is returned

### ACTION-002: Escalation Action
**Description:** Verify that the system can escalate a transaction.
**Preconditions:**
- Transaction exists in Live Messages
**Steps:**
1. Call process_firco_transaction with needs_escalation=True
**Expected Results:**
- Escalate button is clicked
- Status "escalated" is returned

### ACTION-003: Manager Processing After Escalation
**Description:** Verify that manager can process an escalated transaction.
**Preconditions:**
- Transaction has been escalated
**Steps:**
1. Login as manager
2. Call process_firco_transaction with appropriate action
**Expected Results:**
- Action is performed on the escalated transaction
- Status reflects the action performed

## Error Handling Tests

### ERROR-001: Browser Resource Cleanup
**Description:** Verify that browser resources are properly cleaned up after errors.
**Steps:**
1. Force an error during transaction processing
**Expected Results:**
- Page and browser are closed properly
- No resource leaks occur

### ERROR-002: Transaction Error Handling
**Description:** Verify that TransactionError exceptions are properly handled.
**Steps:**
1. Force a TransactionError during processing
**Expected Results:**
- Error is logged
- Error details are included in the result
- Error is written to error_log.txt

### ERROR-003: Generic Error Handling
**Description:** Verify that generic exceptions are properly handled.
**Steps:**
1. Force a generic exception during processing
**Expected Results:**
- Error is logged
- Generic error message is included in the result

## File Processing Tests

### FILE-001: Text File Parsing
**Description:** Verify that transaction text files are correctly parsed.
**Steps:**
1. Create a test transaction file with known content
2. Call parse_txt_file with the file path
**Expected Results:**
- Transaction ID, action, and comment are correctly extracted

### FILE-002: Screenshot Management
**Description:** Verify that screenshots are properly captured and managed.
**Steps:**
1. Process a transaction that generates screenshots
**Expected Results:**
- Screenshots are taken at appropriate steps
- Screenshots are moved to the transaction folder

### FILE-003: Transaction File Movement
**Description:** Verify that processed transaction files are moved correctly.
**Steps:**
1. Process a transaction from a text file
**Expected Results:**
- Original text file is moved to the transaction folder

## Integration Tests

### INT-001: End-to-End Transaction Processing
**Description:** Verify the complete transaction processing flow.
**Steps:**
1. Place a transaction file in the input directory
2. Run the full processing flow
**Expected Results:**
- Transaction is processed according to the specified action
- Results are logged appropriately
- Files are organized in the correct output structure

### INT-002: Multiple Transaction Processing
**Description:** Verify that multiple transactions can be processed in sequence.
**Steps:**
1. Place multiple transaction files in the input directory
2. Process all files in sequence
**Expected Results:**
- All transactions are processed correctly
- No cross-contamination between transaction processing

## Performance Tests

### PERF-001: Transaction Processing Time
**Description:** Measure the time taken to process transactions.
**Steps:**
1. Process a set of test transactions
2. Measure and record processing times
**Expected Results:**
- Processing times are within acceptable limits
- No significant performance degradation over time

### PERF-002: Retry Mechanism Performance
**Description:** Verify that the retry mechanism doesn't cause excessive delays.
**Steps:**
1. Force conditions that trigger retries
2. Measure the time taken with retries
**Expected Results:**
- Retry delays are reasonable
- System recovers efficiently after retries

## Security Tests

### SEC-001: Credential Handling
**Description:** Verify that credentials are handled securely.
**Steps:**
1. Review code for credential handling
2. Check for any logging of sensitive information
**Expected Results:**
- Credentials are not hardcoded
- Passwords are not logged or exposed

### SEC-002: Error Message Security
**Description:** Verify that error messages don't expose sensitive information.
**Steps:**
1. Force various errors
2. Review error messages in logs and UI
**Expected Results:**
- Error messages provide useful information without exposing system details
- No stack traces or sensitive data in user-facing errors
