# Transaction Processing Flow (as of 2025-04-15)

## Key Files
- `main_logic.py`: Orchestrates the transaction processing workflow.
- `FircoPage.py`: Page Object for Firco UI automation, including search and row interaction logic.

---

## Current Flow

### 1. Parse and Prepare
- Parse transaction details from the input txt file.
- Prepare output folder structure.
- Connect to browser and open a new page.

### 2. Login as User
- Login to Firco as the initial user.

### 3. Transaction Search & Verification
- Create a `FircoPage` object.
- Call `verify_search_results(transaction)`:
    - Checks for the transaction in the main tab.
    - If not found, switches to the history tab and searches again.
    - Returns:
        - `'main'` if found in the main tab.
        - `'history'` if found only in the history tab.
        - Raises `TransactionError` if not found at all.
- **If found in main tab:**
    - Call `click_transaction_row_if_single()`:
        - Clicks the row only if exactly one result is present in the main tab.
- **If found in history tab:**
    - Return early with a message: "Transaction already processed (found in history tab)."
    - We should not process this transaction further.
    - We should get out from process_firco_transaction with success
- **If not found:**
    - Return early with error details from `TransactionError`.

### 4. Transaction Processing (if found in main tab)
- If action is not `STP-Release`:
    - Call `process_firco_transaction(..., needs_escalation=True)` (handles escalation flow).
- Else:
    - Call `process_firco_transaction(...)` directly.
- If escalation was performed:
    - Login as manager and process the transaction again.

### 5. Post-Processing
- Move screenshots to the appropriate folder.
- Handle any exceptions in screenshot moving.

---

## Key Logic in `FircoPage.py`
- `verify_search_results(transaction)`:
    - Only checks for presence/location; does not click rows or perform actions.
- `click_transaction_row_if_single()`:
    - Clicks the transaction row only if exactly one row is present in the main tab.
- No row clicking or comment filling occurs on the history tab.

---

## Error Handling
- If transaction is only found in history tab, no further processing occurs.
- If transaction is not found at all, an error is returned immediately.
- All UI actions are guarded by presence/location checks to avoid timeouts and UI errors.

---

## Outstanding Issues/Notes
- If further processing is attempted on the history tab, a logic error exists and must be fixed so that the early return is respected.
- Any changes to page structure or tab logic should be reflected in both `main_logic.py` and `FircoPage.py`.

---

_Last updated: 2025-04-15 by Cascade AI assistant._
