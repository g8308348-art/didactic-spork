## MURDOCK Transaction Processing Tool - Logic Documentation

### Overview
The MURDOCK Transaction Processing Tool is a web-based application that automates the processing of financial transactions. It provides a user interface for submitting transactions, processes them through a server endpoint, and maintains a history of processed transactions in the browser's local storage.

### Key Components

#### 1. Frontend (JavaScript)
- **script.js**: Main application logic
- **index.html**: User interface
- **style.css**: Styling

#### 2. Backend (Server-Side)
- API endpoint at `http://localhost:8088/api` for transaction processing

### Transaction Processing Flow

#### 1. Form Submission
1. User enters transaction details in the form:
   - Transaction numbers (comma-separated)
   - Comment (optional, defaults to 'RTPS')
   - Action (Release, STP-Release, Block, Reject)
   - Transaction Type (various market types)

2. Form Validation:
   - **Transactions**: Must be alphanumeric with commas/spaces
   - **Comment**: Max 250 chars, no SQL injection patterns
   - **Action**: Must be one of the valid actions
   - **Transaction Type**: Must be selected

#### 2. Transaction Processing
1. **Initial Checks**:
   - Split input into individual transactions
   - Check each transaction against local storage for previous processing
   - Skip if already processed successfully (unless previously failed)

2. **Server Communication**:
   - Send transaction to `/api` endpoint via POST request
   - Handle response with success/failure status
   - Process response and update UI accordingly

3. **Status Handling**:
   - **Success**: Transaction processed successfully
   - **No Action**: Transaction already processed
   - **Failed**: Transaction processing failed
   - **Not Found**: Transaction not found in any tab

#### 3. Status Types and Handling

| Status | Description | UI Display |
|--------|-------------|------------|
| `action_performed_on_live` | Successfully processed in live tab | Success (Green) |
| `escalated` | Transaction required escalation | Success (Escalated) |
| `already_handled` | Found in history/BPM | No Action (Blue) |
| `found_in_bpm` | Found in BPM | No Action (Blue) |
| `found_in_sanctions_bypass` | Processed via sanctions bypass | Success (Sanctions) |
| `transaction_not_found_in_any_tab` | Transaction not found | Failed (Red) |
| `failed` | General failure | Failed (Red) |

#### 4. Local Storage
- Stores transaction history with:
  - Transaction ID/number
  - Action taken
  - Timestamp
  - Status and status details
  - Error messages (if any)

### Error Handling

#### Client-Side Errors
- **Validation Errors**: Displayed inline with form fields
- **Network Errors**: Shown in submission status area
- **Processing Errors**: Individual transaction failures shown in results

#### Server-Side Errors
- Returned as JSON with status codes
- Displayed in the submission status area

### Security Considerations

1. **Input Sanitization**:
   - All user inputs are validated
   - HTML escaping to prevent XSS
   - SQL injection patterns blocked in comments

2. **Data Storage**:
   - Transactions stored in browser's localStorage
   - No sensitive data should be stored in comments

### Performance Considerations

1. **Batch Processing**:
   - Multiple transactions processed sequentially
   - UI updates after each transaction

2. **Local Storage**:
   - All transactions stored in localStorage
   - Filtering and searching done client-side

### Testing and Debugging

#### Test Cases
1. **Happy Path**:
   - Single valid transaction
   - Multiple valid transactions
   - Transactions with comments

2. **Error Cases**:
   - Invalid transaction format
   - Server errors
   - Network failures
   - Duplicate transactions

#### Debugging
- Console logs for key operations
- Detailed error messages in UI
- Network tab for API request/response inspection

---

_Last updated: 2025-05-22 by Cascade AI assistant._
