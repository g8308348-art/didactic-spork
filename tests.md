## Test Explanations

### 1. Screening BPM Response Validation
- **Template**: Use the BPM response template matching the test type (e.g. `PCC_TAIWAN_ISO.xml` for PCC Taiwan ISO).
- **placeholders**: Replace `{upi}` with `<YYYYMMDDhhmmss>-<Action>` (e.g. `20250717131411-Release`, `20250717131411-Block`, `20250717131411-Reject`, `20250717131411-STP-Release`).
- **adr_line**: Replace `{adr_line}` with `"SB0SGB2X"`.
- **Generate Test Files**:
  1. Click **Generate Test Files**.
  2. Produce four XML files—one per action (STP‑Release, Release, Block, Reject).
  3. Save them under `test_data/screening_response_<timestamp>` (e.g. `test_data/screening_response_20250717131411/`).
  4. Name files as 'screening_response_20250717131411_STP-Release.xml', 'screening_response_20250717131411_Release.xml', 'screening_response_20250717131411_Block.xml', 'screening_response_20250717131411_Reject.xml'.

### 2. Cuban Filter Validation
- **Template**: Same as above, selecting the template for your test (e.g. `PCC_TAIWAN_ISO.xml`).
- **placeholders**:
  - `{upi}` → `<YYYYMMDDhhmmss>-<Action>` (as in Screening BPM).
  - `{adr_line}` → `"VTB BANK OAO"`.
- **Generate Test Files**:
  1. Click **Generate Test Files**.
  2. Create four XML files (STP‑Release, Release, Block, Reject).
  3. Save them under `test_data/cuban_filter_<timestamp>` (e.g. `test_data/cuban_filter_20250717131411/`).
  4. Name files as 'cuban_filter_20250717131411_STP-Release.xml', 'cuban_filter_20250717131411_Release.xml', 'cuban_filter_20250717131411_Block.xml', 'cuban_filter_20250717131411_Reject.xml'.

### 3. Unit Validation
- **Template**: Same as above, selecting the template for your test (e.g. `PCC_TAIWAN_ISO.xml`).
- **Placeholders**:
  - `{upi}` → `<YYYYMMDDhhmmss>-<Action>` (as in Screening BPM).
- **Generate Test Files**:
  1. Click **Generate Test Files**.
  2. Create four XML files (STP‑Release, Release, Block, Reject).
  3. Save them under `test_data/unit_<timestamp>` (e.g. `test_data/unit_20250717131411/`).
  4. Name files as 'unit_20250717131411_STP-Release.xml', 'unit_20250717131411_Release.xml', 'unit_20250717131411_Block.xml', 'unit_20250717131411_Reject.xml'.

### 4. Value Date Incorrect Format Validation

### 5. No Hit Validation

### 6. Special Character Validation

### 7. Exception Validation

### 8. Reference Field Length Validation

### 9. User Profile Unit Validation
