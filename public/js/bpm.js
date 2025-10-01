/**
 * MURDOCK - BPM Transaction Search
 * JavaScript functionality for BPM interface
 */

// DOM Elements
let searchForm;
let transactionIdInput;
let marketTypeSelect;
let searchBtn;
let loadingState;
let resultsSection;
let resultsContent;
let errorSection;
let errorMessage;
let retryBtn;

// Validation patterns
const VALIDATION_PATTERNS = {
    // Backend (flask_server.py) allows 3-50 chars, alphanumeric, hyphen, underscore
    transactionId: /^[A-Za-z0-9_-]{3,50}$/,
    marketTypes: [
        'UNCLASSIFIED', 'APS_MT', 'CBPR_MX', 'SEPA_CLASSIC', 'RITS_MX',
        'LYNX_MX', 'ENTERPRISE_ISO', 'CHAPS_MX', 'T2S_MX', 'BESS_MT',
        'CHIPS_MX', 'SEPA_INSTANT', 'FEDWIRE', 'TAIWAN_MX', 'CHATS_MX',
        'PEPPLUS_IAT', 'TSF_TRIGGER'
    ]
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    attachEventListeners();
    initializeThemeToggle();
    initializeFormValidation();
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
    searchForm = document.getElementById('bmp-search-form');
    transactionIdInput = document.getElementById('transaction-id');
    marketTypeSelect = document.getElementById('market-type');
    searchBtn = document.getElementById('search-btn');
    loadingState = document.getElementById('loading-state');
    resultsSection = document.getElementById('results-section');
    resultsContent = document.getElementById('results-content');
    errorSection = document.getElementById('error-section');
    errorMessage = document.getElementById('error-message');
    retryBtn = document.getElementById('retry-btn');
}

/**
 * Attach event listeners to form elements
 */
function attachEventListeners() {
    if (searchForm) {
        searchForm.addEventListener('submit', handleFormSubmit);
        searchForm.addEventListener('reset', handleFormReset);
    }
    
    if (retryBtn) {
        retryBtn.addEventListener('click', handleRetry);
    }
    
    // Real-time validation on input
    if (transactionIdInput) {
        transactionIdInput.addEventListener('input', handleTransactionIdInput);
        transactionIdInput.addEventListener('blur', validateTransactionIdField);
    }
    
    if (marketTypeSelect) {
        marketTypeSelect.addEventListener('change', handleMarketTypeChange);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * Initialize form validation setup
 */
function initializeFormValidation() {
    // Set up input formatting for transaction ID
    if (transactionIdInput) {
        transactionIdInput.setAttribute('autocomplete', 'off');
        transactionIdInput.setAttribute('spellcheck', 'false');
    }
}

/**
 * Initialize theme toggle functionality (copied from main script.js pattern)
 */
function initializeThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const body = document.body;
    
    if (themeToggleBtn) {
        // Load saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            body.classList.remove('light-mode');
            body.classList.add('dark-mode');
            themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
        }
        
        themeToggleBtn.addEventListener('click', function() {
            if (body.classList.contains('light-mode')) {
                body.classList.remove('light-mode');
                body.classList.add('dark-mode');
                themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
                localStorage.setItem('theme', 'dark');
            } else {
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
                localStorage.setItem('theme', 'light');
            }
        });
    }
}

/**
 * Handle form submission
 */
function handleFormSubmit(event) {
    event.preventDefault();
    
    BPMLogger.info('Form submission attempted', getFormData());
    
    if (validateForm()) {
        BPMLogger.info('Form validation passed, starting search');
        performSearch();
    } else {
        BPMLogger.warn('Form validation failed', getFormData());
    }
}

/**
 * Handle form reset
 */
function handleFormReset(event) {
    setTimeout(() => {
        clearErrorMessages();
        hideAllSections();
        resetFieldValidation();
    }, 0);
}

/**
 * Handle transaction ID input with real-time validation
 */
function handleTransactionIdInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    // Clear previous validation state
    input.classList.remove('valid', 'invalid');
    clearFieldError('transaction-id-error');
    
    // Real-time validation feedback
    if (value.length > 0) {
        if (VALIDATION_PATTERNS.transactionId.test(value)) {
            input.classList.add('valid');
        } else if (value.length >= 3) { // Only show invalid after reasonable input
            input.classList.add('invalid');
            showFieldError('transaction-id-error', 'Use 3-50 characters: letters, numbers, hyphens (-), or underscores (_)');
        }
    }
}

/**
 * Handle market type selection change
 */
function handleMarketTypeChange(event) {
    const select = event.target;
    const value = select.value;
    
    // Clear previous validation state
    select.classList.remove('valid', 'invalid');
    clearFieldError('market-type-error');
    
    if (value && VALIDATION_PATTERNS.marketTypes.includes(value)) {
        select.classList.add('valid');
    }
    
    // Clear any previous results when changing market type
    hideAllSections();
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (searchForm && !searchBtn.disabled) {
            searchForm.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to clear results/errors
    if (event.key === 'Escape') {
        hideAllSections();
    }
}

/**
 * Validate form inputs
 */
function validateForm() {
    let isValid = true;
    
    // Clear previous error messages
    clearErrorMessages();
    resetFieldValidation();
    
    // Validate transaction ID
    const transactionId = transactionIdInput.value.trim();
    if (!transactionId) {
        showFieldError('transaction-id-error', 'Transaction ID is required');
        transactionIdInput.classList.add('invalid');
        isValid = false;
    } else if (!VALIDATION_PATTERNS.transactionId.test(transactionId)) {
        showFieldError('transaction-id-error', 'Use 3-50 characters: letters, numbers, hyphens (-), or underscores (_)');
        transactionIdInput.classList.add('invalid');
        isValid = false;
    } else {
        transactionIdInput.classList.add('valid');
    }
    
    // Validate market type
    const marketType = marketTypeSelect.value;
    if (!marketType) {
        showFieldError('market-type-error', 'Please select a market type');
        marketTypeSelect.classList.add('invalid');
        isValid = false;
    } else if (!VALIDATION_PATTERNS.marketTypes.includes(marketType)) {
        showFieldError('market-type-error', 'Invalid market type selected');
        marketTypeSelect.classList.add('invalid');
        isValid = false;
    } else {
        marketTypeSelect.classList.add('valid');
    }
    
    return isValid;
}

/**
 * Validate transaction ID field specifically
 */
function validateTransactionIdField() {
    const transactionId = transactionIdInput.value.trim();
    
    transactionIdInput.classList.remove('valid', 'invalid');
    clearFieldError('transaction-id-error');
    
    if (transactionId.length > 0) {
        if (VALIDATION_PATTERNS.transactionId.test(transactionId)) {
            transactionIdInput.classList.add('valid');
        } else {
            transactionIdInput.classList.add('invalid');
            showFieldError('transaction-id-error', 'Use 3-50 characters: letters, numbers, hyphens (-), or underscores (_)');
        }
    }
}

/**
 * Reset field validation classes
 */
function resetFieldValidation() {
    if (transactionIdInput) {
        transactionIdInput.classList.remove('valid', 'invalid');
    }
    if (marketTypeSelect) {
        marketTypeSelect.classList.remove('valid', 'invalid');
    }
}

/**
 * Show error message for a specific field
 */
function showFieldError(errorElementId, message) {
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        errorElement.setAttribute('role', 'alert');
    }
}

/**
 * Clear error message for a specific field
 */
function clearFieldError(errorElementId) {
    const errorElement = document.getElementById(errorElementId);
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
        errorElement.removeAttribute('role');
    }
}

/**
 * Clear all error messages
 */
function clearErrorMessages() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
        element.style.display = 'none';
        element.removeAttribute('role');
    });
}

/**
 * Hide all result/error sections
 */
function hideAllSections() {
    if (loadingState) loadingState.classList.add('hidden');
    if (resultsSection) resultsSection.classList.add('hidden');
    if (errorSection) errorSection.classList.add('hidden');
}

/**
 * Perform the BPM search
 */
async function performSearch() {
    const transactionId = transactionIdInput.value.trim();
    const marketType = marketTypeSelect.value;
    const searchStartTime = Date.now();
    
    BPMLogger.info('Starting BPM search', { transactionId, marketType });
    
    // Show loading state
    showLoadingState();
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
        
        BPMLogger.debug('Sending API request to /api/bpm');
        
        const response = await fetch('/api/bpm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                transactionId: transactionId,
                marketType: marketType
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const responseTime = Date.now() - searchStartTime;
        BPMLogger.info('API response received', { 
            status: response.status, 
            statusText: response.statusText,
            responseTime: responseTime + 'ms'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'ok') {
            showResults(data);
        } else if (data.status === 'error') {
            // Handle different error types based on error code with enhanced error details
            const errorCode = data.errorCode || 'UNKNOWN_ERROR';
            let errorType = 'server-error';
            
            // Classify error types for appropriate user messaging
            if (['MISSING_TRANSACTION_ID', 'MISSING_MARKET_TYPE', 'INVALID_MARKET_TYPE', 'INVALID_TRANSACTION_ID_FORMAT', 'TRANSACTION_TYPE_NOT_DEFINED', 'VALIDATION_ERROR', 'MARKET_TYPE_MAPPING_ERROR'].includes(errorCode)) {
                errorType = 'validation-error';
            } else if (['BPM_SYSTEM_UNAVAILABLE', 'SYSTEM_CONFIGURATION_ERROR', 'VALIDATION_SYSTEM_ERROR', 'SYSTEM_ERROR'].includes(errorCode)) {
                errorType = 'system-error';
            } else if (['BPM_AUTOMATION_ERROR', 'BPM_TIMEOUT_ERROR', 'BPM_CONNECTION_ERROR', 'BPM_DATA_ERROR'].includes(errorCode)) {
                errorType = 'automation-error';
            } else if (['REQUEST_PROCESSING_ERROR', 'INVALID_JSON'].includes(errorCode)) {
                errorType = 'network-error';
            } else if (errorCode === 'BPM_PERMISSION_ERROR') {
                errorType = 'system-error';
            }
            
            // Pass enhanced error details to showError function
            const errorDetails = {
                errorCode: data.errorCode,
                requestId: data.requestId,
                validationErrors: data.validationErrors,
                validOptions: data.validOptions,
                technicalDetails: data.technicalDetails,
                allowedCharacters: data.allowedCharacters
            };
            
            showError(data.message || 'Search failed', errorType, errorDetails);
        } else {
            showError(data.message || 'Unexpected response format', 'server-error', { errorCode: 'UNEXPECTED_RESPONSE' });
        }
        
    } catch (error) {
        console.error('Search error:', error);
        
        let errorType = 'server-error';
        let errorMessage = 'Search failed';
        let errorDetails = { errorCode: 'CLIENT_ERROR' };
        
        if (error.name === 'AbortError') {
            errorType = 'network-error';
            errorMessage = 'Search timed out. The request took too long to complete.';
            errorDetails.errorCode = 'TIMEOUT_ERROR';
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorType = 'network-error';
            errorMessage = 'Network error occurred. Please check your internet connection and try again.';
            errorDetails.errorCode = 'NETWORK_ERROR';
        } else if (error.message.includes('JSON')) {
            errorType = 'server-error';
            errorMessage = 'Server returned invalid response. Please try again or contact support.';
            errorDetails.errorCode = 'INVALID_RESPONSE';
        } else {
            errorMessage = `Search failed: ${error.message}`;
            errorDetails.errorCode = 'UNKNOWN_CLIENT_ERROR';
        }
        
        showError(errorMessage, errorType, errorDetails);
    } finally {
        hideLoadingState();
    }
}

/**
 * Show loading state with proper UI updates
 */
function showLoadingState() {
    hideAllSections();
    loadingState.classList.remove('hidden');
    searchBtn.disabled = true;
    searchBtn.classList.add('loading');
    
    // Disable form inputs during search
    transactionIdInput.disabled = true;
    marketTypeSelect.disabled = true;
    
    // Update button text
    const buttonText = searchBtn.querySelector('i').nextSibling;
    if (buttonText) {
        buttonText.textContent = ' Searching...';
    }
}

/**
 * Hide loading state and restore UI
 */
function hideLoadingState() {
    loadingState.classList.add('hidden');
    searchBtn.disabled = false;
    searchBtn.classList.remove('loading');
    
    // Re-enable form inputs
    transactionIdInput.disabled = false;
    marketTypeSelect.disabled = false;
    
    // Restore button text
    const buttonText = searchBtn.querySelector('i').nextSibling;
    if (buttonText) {
        buttonText.textContent = ' Search Transaction';
    }
}

/**
 * Display search results with enhanced formatting and multiple result support
 */
function showResults(data) {
    BPMLogger.info('Displaying search results', { 
        hasResults: !!data.results,
        resultType: data.results ? (isNoResultsResponse(data.results) ? 'no-results' : 'success') : 'unknown'
    });
    
    hideAllSections();
    
    if (resultsContent) {
        if (data.results) {
            // Check if this is a "no results" scenario
            if (isNoResultsResponse(data.results)) {
                showNoResults(data.results);
                return;
            }
            
            // Create a structured display of the results
            let resultsHtml = '<div class="search-results">';
            
            // Display search parameters
            resultsHtml += buildSearchSummary(data.results);
            
            // Display BPM automation results
            resultsHtml += buildBmpResults(data.results);
            
            // Display multiple results if available
            if (data.results.multipleResults && Array.isArray(data.results.multipleResults)) {
                resultsHtml += buildMultipleResultsTable(data.results.multipleResults);
            }
            
            // Display raw JSON for debugging (collapsible)
            resultsHtml += buildRawResultsSection(data.results);
            
            resultsHtml += '</div>';
            
            resultsContent.innerHTML = resultsHtml;
        } else {
            // Fallback to displaying the entire response
            const formattedData = formatJsonForDisplay(data);
            resultsContent.innerHTML = '<pre class="json-display">' + formattedData + '</pre>';
        }
    }
    
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Display no results found message with context
 */
function showNoResults(results) {
    hideAllSections();
    
    if (resultsContent) {
        let html = '<div class="search-results">';
        
        // Display search summary even for no results
        html += buildSearchSummary(results);
        
        // Display no results message
        html += '<div class="no-results">';
        html += '<i class="fas fa-search"></i>';
        html += '<h4>No Results Found</h4>';
        html += '<p>No transaction was found for the specified ID and market type.</p>';
        
        // Add specific context if available
        if (results.bmpResult && results.bmpResult.message) {
            html += `<p class="context-message">${sanitizeInput(results.bmpResult.message)}</p>`;
        }
        
        html += '</div>';
        
        // Still show raw results for debugging
        html += buildRawResultsSection(results);
        
        html += '</div>';
        
        resultsContent.innerHTML = html;
    }
    
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Check if the response indicates no results found
 */
function isNoResultsResponse(results) {
    // Prefer backend schema from bpm_page.search_results(): status not_found
    if (results.bmpResult) {
        const r = results.bmpResult;
        if ((r.status && r.status.toLowerCase() === 'not_found') || r.message === 'No results') {
            return true;
        }
    }

    // Backward compatibility flags if present
    if (results.noResults === true || results.transactionFound === false) {
        return true;
    }

    if (results.multipleResults && Array.isArray(results.multipleResults) && results.multipleResults.length === 0) {
        return true;
    }

    return false;
}

/**
 * Build search summary section
 */
function buildSearchSummary(results) {
    let html = '<div class="search-summary">';
    html += '<h4><i class="fas fa-search"></i> Search Summary</h4>';
    html += `<p><strong>Transaction ID:</strong> <span class="highlight-value">${sanitizeInput(results.transactionId || 'N/A')}</span></p>`;
    html += `<p><strong>Market Type:</strong> <span class="highlight-value">${sanitizeInput(results.marketType || 'N/A')}</span></p>`;
    html += `<p><strong>Search Time:</strong> <span class="highlight-value">${formatDateTime(results.searchTime) || 'N/A'}</span></p>`;
    
    if (results.mappedOptions && results.mappedOptions.length > 0) {
        html += `<p><strong>Mapped Options:</strong> <span class="highlight-value">${results.mappedOptions.map(opt => sanitizeInput(opt)).join(', ')}</span></p>`;
    }
    
    // Backend sends executionTime in results
    if (results.executionTime) {
        html += `<p><strong>Execution Time:</strong> <span class="highlight-value">${results.executionTime}ms</span></p>`;
    }
    // Also surface environment if computed
    if (results.bmpResult && results.bmpResult.environment) {
        html += `<p><strong>Environment:</strong> <span class="highlight-value">${sanitizeInput(results.bmpResult.environment)}</span></p>`;
    }
    
    html += '</div>';
    return html;
}

/**
 * Build BPM automation results section
 */
function buildBmpResults(results) {
    let html = '<div class="bmp-results">';
    html += '<h4><i class="fas fa-cogs"></i> BPM Automation Results</h4>';
    
    if (results.bmpResult) {
        const r = results.bmpResult;

        // Status line
        if (typeof r.status === 'string') {
            html += `<p><strong>Status:</strong> <span class="status-${r.status.toLowerCase()}">${sanitizeInput(r.status)}</span></p>`;
        }

        // Outcome badges
        if (r.success === true) {
            html += '<div class="transaction-found">';
            html += '<i class="fas fa-check-circle"></i>';
            html += '<p><strong>Transaction validated successfully.</strong></p>';
            html += '</div>';
        } else if (r.status && r.status.toLowerCase() === 'not_found') {
            html += '<div class="no-transaction-found">';
            html += '<i class="fas fa-exclamation-triangle"></i>';
            html += '<p>Transaction not found in BPM system</p>';
            html += '</div>';
        } else if (r.status && (r.status.toLowerCase() === 'failure' || r.status.toLowerCase() === 'error')) {
            html += '<div class="no-transaction-found">';
            html += '<i class="fas fa-exclamation-triangle"></i>';
            html += '<p>Transaction validation failed</p>';
            html += '</div>';
        }

        // Message
        if (r.message) {
            html += `<p><strong>Message:</strong> ${sanitizeInput(r.message)}</p>`;
        }

        // Environment and details
        if (r.environment) {
            html += `<p><strong>Environment:</strong> <span class="highlight-value">${sanitizeInput(r.environment)}</span></p>`;
        }

        if (r.details && typeof r.details === 'object') {
            html += '<details class="bpm-details">';
            html += '<summary>Details</summary>';
            const d = r.details;
            if (d.reference) html += `<p><strong>Reference (col 2):</strong> ${sanitizeInput(String(d.reference))}</p>`;
            if (d.current_status) html += `<p><strong>Current Status (col 4):</strong> ${sanitizeInput(String(d.current_status))}</p>`;
            if (d.bpm_status) html += `<p><strong>BPM Status (col 11):</strong> ${sanitizeInput(String(d.bpm_status))}</p>`;
            if (d.holding_qm) html += `<p><strong>Holding QM (col 10):</strong> ${sanitizeInput(String(d.holding_qm))}</p>`;
            if (d.columns_len !== undefined) html += `<p><strong>Columns Count:</strong> ${sanitizeInput(String(d.columns_len))}</p>`;
            html += '</details>';
        }
    } else {
        html += '<div class="search-completed">';
        html += '<i class="fas fa-info-circle"></i>';
        html += '<p>BPM search completed</p>';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

/**
 * Build multiple results table for structured display
 */
function buildMultipleResultsTable(multipleResults) {
    let html = '<div class="multiple-results">';
    html += '<h4><i class="fas fa-table"></i> Multiple Results Found</h4>';
    
    if (multipleResults.length === 0) {
        html += '<p class="no-results-message">No results found matching the search criteria.</p>';
    } else {
        html += '<div class="results-table-container">';
        html += '<table class="results-table">';
        
        // Build table header
        html += '<thead><tr>';
        const headers = Object.keys(multipleResults[0] || {});
        headers.forEach(header => {
            html += `<th>${sanitizeInput(header.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase()))}</th>`;
        });
        html += '</tr></thead>';
        
        // Build table body
        html += '<tbody>';
        multipleResults.forEach((result, index) => {
            html += `<tr class="result-row ${index % 2 === 0 ? 'even' : 'odd'}">`;
            headers.forEach(header => {
                const value = result[header];
                const displayValue = value !== null && value !== undefined ? sanitizeInput(String(value)) : 'N/A';
                html += `<td class="result-cell" data-label="${sanitizeInput(header)}">${displayValue}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody>';
        
        html += '</table>';
        html += '</div>';
        
        // Add results summary
        html += `<p class="results-summary"><strong>Total Results:</strong> ${multipleResults.length}</p>`;
    }
    
    html += '</div>';
    return html;
}

/**
 * Build raw results collapsible section
 */
function buildRawResultsSection(results) {
    let html = '<div class="raw-results">';
    html += '<details>';
    html += '<summary><i class="fas fa-code"></i> Raw Response Data</summary>';
    html += '<pre class="json-display">' + formatJsonForDisplay(results) + '</pre>';
    html += '</details>';
    html += '</div>';
    return html;
}

/**
 * Format date/time for display
 */
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return null;
    
    try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) return dateTimeString; // Return original if invalid
        
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        });
    } catch (error) {
        return dateTimeString; // Return original if parsing fails
    }
}

/**
 * Format JSON data for display with syntax highlighting
 */
function formatJsonForDisplay(data) {
    const jsonString = JSON.stringify(data, null, 2);
    
    // Simple syntax highlighting
    return jsonString
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/("[\w\s]+"):/g, '<span class="json-key">$1</span>:')
        .replace(/: (".*?")/g, ': <span class="json-string">$1</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
        .replace(/: (null)/g, ': <span class="json-null">$1</span>');
}

/**
 * Display error message with comprehensive error handling and user-friendly messaging
 */
function showError(message, errorType = 'server-error', errorDetails = null) {
    hideAllSections();
    
    // Log error for debugging
    console.error('BPM Error:', {
        message: message,
        type: errorType,
        details: errorDetails,
        timestamp: new Date().toISOString()
    });
    
    // Create enhanced error display
    if (errorMessage) {
        let errorHtml = `<div class="error-main-message">${sanitizeInput(message)}</div>`;
        
        // Add specific error guidance based on error type
        const errorGuidance = getErrorGuidance(errorType, errorDetails);
        if (errorGuidance) {
            errorHtml += `<div class="error-guidance">${errorGuidance}</div>`;
        }
        
        // Add technical details if available (for debugging)
        if (errorDetails && (errorDetails.requestId || errorDetails.errorCode)) {
            errorHtml += '<div class="error-technical-details">';
            errorHtml += '<details>';
            errorHtml += '<summary>Technical Details</summary>';
            
            if (errorDetails.requestId) {
                errorHtml += `<p><strong>Request ID:</strong> ${sanitizeInput(errorDetails.requestId)}</p>`;
            }
            if (errorDetails.errorCode) {
                errorHtml += `<p><strong>Error Code:</strong> ${sanitizeInput(errorDetails.errorCode)}</p>`;
            }
            if (errorDetails.validationErrors && Array.isArray(errorDetails.validationErrors)) {
                errorHtml += '<p><strong>Validation Issues:</strong></p>';
                errorHtml += '<ul>';
                errorDetails.validationErrors.forEach(error => {
                    errorHtml += `<li>${sanitizeInput(error)}</li>`;
                });
                errorHtml += '</ul>';
            }
            if (errorDetails.validOptions && Array.isArray(errorDetails.validOptions)) {
                errorHtml += '<p><strong>Valid Market Types:</strong></p>';
                errorHtml += '<ul>';
                errorDetails.validOptions.forEach(option => {
                    errorHtml += `<li>${sanitizeInput(option)}</li>`;
                });
                errorHtml += '</ul>';
            }
            
            errorHtml += '</details>';
            errorHtml += '</div>';
        }
        
        errorMessage.innerHTML = errorHtml;
    }
    
    // Add error type class for styling
    const errorContent = errorSection.querySelector('.error-content');
    if (errorContent) {
        errorContent.className = `error-content ${errorType}`;
        
        // Add appropriate icon based on error type
        const iconElement = errorContent.querySelector('.error-icon');
        if (iconElement) {
            iconElement.className = `error-icon ${getErrorIcon(errorType)}`;
        }
    }
    
    // Show error section with accessibility support
    errorSection.classList.remove('hidden');
    errorSection.setAttribute('role', 'alert');
    errorSection.setAttribute('aria-live', 'assertive');
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Focus on retry button for keyboard accessibility
    if (retryBtn) {
        setTimeout(() => retryBtn.focus(), 100);
    }
}

/**
 * Get user-friendly error guidance based on error type
 */
function getErrorGuidance(errorType, errorDetails) {
    switch (errorType) {
        case 'network-error':
            return `
                <div class="error-suggestions">
                    <h4>What you can try:</h4>
                    <ul>
                        <li>Check your internet connection</li>
                        <li>Refresh the page and try again</li>
                        <li>Contact IT support if the problem persists</li>
                    </ul>
                </div>
            `;
        case 'validation-error':
            return `
                <div class="error-suggestions">
                    <h4>Please check your input:</h4>
                    <ul>
                        <li>Ensure Transaction ID contains only letters, numbers, hyphens, and underscores</li>
                        <li>Transaction ID should be between 3-50 characters</li>
                        <li>Select a valid market type from the dropdown</li>
                    </ul>
                </div>
            `;
        case 'system-error':
        case 'automation-error':
            return `
                <div class="error-suggestions">
                    <h4>System temporarily unavailable:</h4>
                    <ul>
                        <li>Wait a few minutes and try again</li>
                        <li>Contact system administrator if the issue continues</li>
                        <li>Check system status page if available</li>
                    </ul>
                </div>
            `;
        case 'server-error':
        default:
            return `
                <div class="error-suggestions">
                    <h4>Something went wrong:</h4>
                    <ul>
                        <li>Try refreshing the page</li>
                        <li>Wait a moment and try your search again</li>
                        <li>Contact support if the problem continues</li>
                    </ul>
                </div>
            `;
    }
}

/**
 * Get appropriate icon class for error type
 */
function getErrorIcon(errorType) {
    switch (errorType) {
        case 'network-error':
            return 'fas fa-wifi';
        case 'validation-error':
            return 'fas fa-exclamation-triangle';
        case 'system-error':
        case 'automation-error':
            return 'fas fa-cogs';
        case 'server-error':
        default:
            return 'fas fa-exclamation-circle';
    }
}

/**
 * Handle retry button click
 */
function handleRetry() {
    hideAllSections();
    clearErrorMessages();
    resetFieldValidation();
    
    // Focus back to transaction ID input
    if (transactionIdInput) {
        transactionIdInput.focus();
    }
}

/**
 * Utility function to sanitize input
 */
function sanitizeInput(input) {
    return input.replace(/[<>\"'&]/g, function(match) {
        const escapeMap = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        };
        return escapeMap[match];
    });
}

/**
 * Get form data as object
 */
function getFormData() {
    return {
        transactionId: transactionIdInput.value.trim(),
        marketType: marketTypeSelect.value
    };
}

/**
 * Check if form has unsaved changes
 */
function hasUnsavedChanges() {
    const data = getFormData();
    return data.transactionId.length > 0 || data.marketType.length > 0;
}

/**
 * Enhanced logging utility for debugging and monitoring
 */
const BPMLogger = {
    logs: [],
    maxLogs: 100,
    
    log: function(level, message, data = null) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level: level,
            message: message,
            data: data,
            url: window.location.href,
            userAgent: navigator.userAgent.substring(0, 100) // Truncate for privacy
        };
        
        this.logs.push(logEntry);
        
        // Keep only the most recent logs
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // Console logging based on level
        switch (level) {
            case 'error':
                console.error(`[BPM] ${message}`, data);
                break;
            case 'warn':
                console.warn(`[BPM] ${message}`, data);
                break;
            case 'info':
                console.info(`[BPM] ${message}`, data);
                break;
            case 'debug':
            default:
                console.log(`[BPM] ${message}`, data);
                break;
        }
        
        // Store in localStorage for debugging (with size limit)
        try {
            const recentLogs = this.logs.slice(-20); // Keep only 20 most recent
            localStorage.setItem('bpm_debug_logs', JSON.stringify(recentLogs));
        } catch (e) {
            // Ignore localStorage errors (quota exceeded, etc.)
        }
    },
    
    error: function(message, data) { this.log('error', message, data); },
    warn: function(message, data) { this.log('warn', message, data); },
    info: function(message, data) { this.log('info', message, data); },
    debug: function(message, data) { this.log('debug', message, data); },
    
    getLogs: function() { return this.logs; },
    
    clearLogs: function() { 
        this.logs = []; 
        localStorage.removeItem('bmp_debug_logs');
    },
    
    exportLogs: function() {
        const logsData = {
            exportTime: new Date().toISOString(),
            logs: this.logs,
            sessionInfo: {
                url: window.location.href,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }
        };
        
        const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bpm-debug-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

/**
 * Initialize error monitoring and logging
 */
function initializeErrorMonitoring() {
    // Log page load
    BPMLogger.info('BPM interface initialized', {
        timestamp: new Date().toISOString(),
        url: window.location.href
    });
    
    // Global error handler for unhandled JavaScript errors
    window.addEventListener('error', function(event) {
        BPMLogger.error('Unhandled JavaScript error', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error ? event.error.toString() : null
        });
    });
    
    // Global handler for unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        BPMLogger.error('Unhandled promise rejection', {
            reason: event.reason ? event.reason.toString() : 'Unknown reason'
        });
    });
    
    // Add debug console commands (only in development)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.BPMDebug = {
            logs: () => BPMLogger.getLogs(),
            clearLogs: () => BPMLogger.clearLogs(),
            exportLogs: () => BPMLogger.exportLogs(),
            testError: () => showError('Test error message', 'validation-error', { errorCode: 'TEST_ERROR' })
        };
        BPMLogger.info('Debug commands available: BPMDebug.logs(), BPMDebug.clearLogs(), BPMDebug.exportLogs(), BPMDebug.testError()');
    }
}

// Initialize error monitoring when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeErrorMonitoring();
});

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateForm,
        clearErrorMessages,
        showFieldError,
        clearFieldError,
        formatJsonForDisplay,
        sanitizeInput,
        getFormData,
        showResults,
        showNoResults,
        isNoResultsResponse,
        buildSearchSummary,
        buildBmpResults,
        buildMultipleResultsTable,
        buildRawResultsSection,
        formatDateTime,
        showError,
        getErrorGuidance,
        getErrorIcon,
        BPMLogger,
        VALIDATION_PATTERNS
    };
}