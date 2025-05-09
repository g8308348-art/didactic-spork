/**
 * MURDOCK - Transaction Processing Tool
 * Main JavaScript File
 */

// DOM Elements
const transactionForm = document.getElementById('transaction-form-element');
const transactionsInput = document.getElementById('transactions');
const commentInput = document.getElementById('comment');
const actionSelect = document.getElementById('action');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const commentCharCount = document.getElementById('comment-char-count');
const submissionStatus = document.getElementById('submission-status');
const transactionsTableBody = document.getElementById('transactions-table-body');
const filterAction = document.getElementById('filter-action');
const searchTransactions = document.getElementById('search-transactions');

// Error message elements
const transactionsError = document.getElementById('transactions-error');
const commentError = document.getElementById('comment-error');
const actionError = document.getElementById('action-error');

// Theme toggle functionality
themeToggleBtn.addEventListener('click', () => {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    
    // Update icon based on current theme
    if (isDarkMode) {
        themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'light');
    }
});

// Check for saved theme preference
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    // Load any existing transactions
    loadTransactions();
});

// Navigation links
const navLinks = document.querySelectorAll('.nav-link');
navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove active class from all links
        navLinks.forEach(l => l.classList.remove('active'));
        
        // Add active class to clicked link
        this.classList.add('active');
        
        // Get the target section id from the href
        const targetId = this.getAttribute('href').substring(1);
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show the target section
        document.getElementById(targetId).style.display = 'block';
    });
});

// Character count for comment
commentInput.addEventListener('input', () => {
    const currentLength = commentInput.value.length;
    commentCharCount.textContent = currentLength;
    
    // Visual feedback as user approaches limit
    if (currentLength >= 200) {
        commentCharCount.style.color = 'var(--error-color)';
    } else {
        commentCharCount.style.color = 'var(--text-secondary)';
    }
});

// Form validation functions
function validateTransactions(value) {
    // Allow alphanumeric characters, commas, and spaces
    const regex = /^[a-zA-Z0-9, _-]+$/;
    
    if (!value.trim()) {
        showError(transactionsError, 'Transaction details are required');
        return false;
    }
    
    if (!regex.test(value)) {
        showError(transactionsError, 'Only alphanumeric characters, commas, and spaces are allowed');
        return false;
    }
    
    hideError(transactionsError);
    return true;
}

function validateComment(value) {
    // Check for SQL injection patterns
    const sqlPatterns = /('|"|;|--|\/\*|\*\/|exec|union|select|insert|update|delete|drop|alter)/i;
    
    if (value.length > 250) {
        showError(commentError, 'Comment must be less than 250 characters');
        return false;
    }
    
    if (sqlPatterns.test(value)) {
        showError(commentError, 'Comment contains invalid characters');
        return false;
    }
    
    hideError(commentError);
    return true;
}

function validateAction(value) {
    const validActions = ['STP-Release', 'Release', 'Block', 'Reject'];
    
    if (!value || !validActions.includes(value)) {
        showError(actionError, 'Please select a valid action');
        return false;
    }
    
    hideError(actionError);
    return true;
}

// Helper functions for error display
function showError(element, message) {
    element.textContent = message;
    element.classList.add('visible');
}

function hideError(element) {
    element.textContent = '';
    element.classList.remove('visible');
}

// Form submission
transactionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form values
    let transactionsValue = transactionsInput.value;
    // Remove tabs and non-visible whitespace except spaces
    transactionsValue = transactionsValue.replace(/[\s\u200B-\u200D\uFEFF\t\n\r\f\v]+/g, ' ');
    transactionsValue = transactionsValue.replace(/ +/g, ' ').trim();
    let commentValue = commentInput.value.trim();
    if (!commentValue) {
        commentValue = 'RTPS';
    }
    const rawActionValue = actionSelect.value;

    // Validate all fields
    const isTransactionsValid = validateTransactions(transactionsValue);
    const isCommentValid = validateComment(commentValue);
    const isActionValid = validateAction(rawActionValue);

    // If all validations pass
    if (isTransactionsValid && isCommentValid && isActionValid) {
        // After validation, map Release to STP-Release for processing
        const actionValue = rawActionValue === 'Release' ? 'STP-Release' : rawActionValue;
        try {
            // Disable submit button and show loading state
            const submitButton = transactionForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';
            
            // Show status message
            submissionStatus.innerHTML = 'Processing transactions...';
            submissionStatus.className = 'submission-status info';
            submissionStatus.style.display = 'block';
            
            // Parse transactions (comma-separated values)
            const transactionsArray = transactionsValue.split(',').map(t => t.trim()).filter(t => t);
            
            let successCount = 0;
            let failCount = 0;
            let failedTransactions = [];
            let succeededTransactions = [];
            
            for (const txn of transactionsArray) {
                // Validate each transaction again for safety
                if (!validateTransactions(txn)) {
                    failCount++;
                    failedTransactions.push({txn, error: 'Invalid transaction format'});
                    continue;
                }
                const data = {
                    transaction: txn,
                    comment: commentValue,
                    action: actionValue,
                    timestamp: Date.now(),
                    performOnLatest: document.getElementById('perform-on-latest').checked
                };
                const response = await sendTransactionToServer(data);
                if (response.success) {
                    saveTransaction({
                        transaction: txn,
                        comment: commentValue,
                        action: actionValue,
                        timestamp: data.timestamp,
                        status: response.status_detail || 'success', // Store detailed status, fallback to 'success'
                        statusMessage: response.message, 
                        transactionId: response.transactionId
                    });
                    successCount++;
                    succeededTransactions.push(txn);
                } else {
                    saveTransaction({
                        transaction: txn,
                        comment: commentValue,
                        action: actionValue,
                        timestamp: data.timestamp,
                        status: 'failed', // Keep 'failed' as is
                        statusMessage: response.message || 'Transaction processing failed',
                        errorCode: response.errorCode
                    });
                    failCount++;
                    failedTransactions.push({txn, error: response.message || 'Transaction processing failed'});
                }
            }
            // Show summary message
            let summary = `<strong>Processed ${transactionsArray.length} transaction(s):</strong> <br>`;
            summary += `<span class='success'>${successCount} succeeded</span>, <span class='error'>${failCount} failed</span>`;
            if (failCount > 0) {
                summary += '<br>Failed: ' + failedTransactions.map(f => `${escapeHtml(f.txn)} (${escapeHtml(f.error)})`).join(', ');
            }
            submissionStatus.innerHTML = summary;
            submissionStatus.className = failCount === 0 ? 'submission-status success' : 'submission-status error';
            
            // Reset form
            transactionForm.reset();
            commentCharCount.textContent = '0';
            
            // Update table
            loadTransactions();
            
            // Re-enable submit button
            submitButton.disabled = false;
            submitButton.textContent = 'Process Transaction';
            
            // Clear status message after 5 seconds for success, 8 seconds for errors
            const clearTimeout = failCount === 0 ? 5000 : 8000;
            setTimeout(() => {
                submissionStatus.style.display = 'none';
            }, clearTimeout);
        } catch (error) {
            // Show error message
            submissionStatus.innerHTML = `<strong>System Error:</strong> ${error.message}`;
            submissionStatus.className = 'submission-status error';
            console.error('Submission error:', error);
            
            // Re-enable submit button
            const submitButton = transactionForm.querySelector('button[type="submit"]');
            submitButton.disabled = false;
            submitButton.textContent = 'Process Transaction';
        }
    }
});

// Function to create and download a text file (keeping for reference)
function createAndDownloadFile(filename, content) {
    // Create a blob with the file content
    const blob = new Blob([content], { type: 'text/plain' });
    
    // Create a URL for the blob
    const url = URL.createObjectURL(blob);
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    
    // Append to the document
    document.body.appendChild(link);
    
    // Trigger the download
    link.click();
    
    // Clean up
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Simulate server submission (in a real app, this would be an API call)
async function simulateServerSubmission(data) {
    return new Promise(resolve => {
        // Simulate network delay
        setTimeout(() => {
            resolve({
                success: true,
                message: 'Transaction processed successfully',
                data: data
            });
        }, 1000);
    });
}

// New function to send transaction data to the server
async function sendTransactionToServer(data) {
    try {
        // Use the actual server endpoint
        const response = await fetch('http://localhost:8080/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }
        
        const responseData = await response.json();
        return {
            success: responseData.success, // Overall success boolean
            message: responseData.message, // Detailed message for tooltip
            status_detail: responseData.status_detail, // Specific status string from backend
            transactionId: responseData.transactionId,
            errorCode: responseData.errorCode // Ensure errorCode is passed through
        };
        
        // Use mock function for testing if server is unavailable
        // return await mockProcessTransaction(data);
    } catch (error) {
        console.error('Error sending transaction:', error);
        return {
            success: false,
            message: `Failed to process transaction: ${error.message}`,
            status_detail: 'network_error' // Or some other indicator for client-side failure
        };
    }
}

// Mock function that sometimes succeeds and sometimes fails (for testing)
async function mockProcessTransaction(data) {
    return new Promise(resolve => {
        // Simulate network delay (between 500ms and 1500ms)
        const delay = Math.floor(Math.random() * 1000) + 500;
        
        setTimeout(() => {
            // Randomly succeed or fail (70% success rate)
            const isSuccess = Math.random() < 0.7;
            
            if (isSuccess) {
                resolve({
                    success: true,
                    message: 'Transaction processed successfully',
                    data: data,
                    transactionId: `TXN-${Math.floor(Math.random() * 10000)}`
                });
            } else {
                // Generate different types of errors
                const errorTypes = [
                    'Transaction validation failed',
                    'Server processing error',
                    'Database connection timeout',
                    'Invalid transaction format'
                ];
                const errorMessage = errorTypes[Math.floor(Math.random() * errorTypes.length)];
                
                resolve({
                    success: false,
                    message: errorMessage,
                    errorCode: Math.floor(Math.random() * 100) + 400
                });
            }
        }, delay);
    });
}

// Local storage functions for transactions
function saveTransaction(transaction) {
    let transactions = JSON.parse(localStorage.getItem('transactions') || '[]');
    transactions.push(transaction);
    localStorage.setItem('transactions', JSON.stringify(transactions));
}

function loadTransactions() {
    let transactions = JSON.parse(localStorage.getItem('transactions') || '[]');
    
    // Apply filters if any
    const actionFilter = filterAction.value;
    const searchFilter = searchTransactions.value.toLowerCase();
    
    if (actionFilter) {
        transactions = transactions.filter(t => t.action === actionFilter);
    }
    
    if (searchFilter) {
        transactions = transactions.filter(t => 
            t.transaction.toLowerCase().includes(searchFilter) || 
            (t.comment && t.comment.toLowerCase().includes(searchFilter))
        );
    }
    
    // Sort by timestamp (newest first)
    transactions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Clear table
    transactionsTableBody.innerHTML = '';
    
    // If no transactions, show message
    if (transactions.length === 0) {
        const noDataRow = document.createElement('tr');
        noDataRow.className = 'no-data';
        noDataRow.innerHTML = '<td colspan="5">No transaction data available</td>';
        transactionsTableBody.appendChild(noDataRow);
        return;
    }
    
    // Populate table
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        
        const date = new Date(transaction.timestamp);
        const formattedDate = date.toLocaleString();
        
        let statusHtml = '';
        let statusText = 'Unknown'; // Default text
        let statusClass = 'status-badge'; // Base class

        // Determine status display based on detailed status
        switch (transaction.status) {
            case 'action_performed_on_live':
                statusText = 'Success';
                statusClass += ' success-live'; // Happy path green
                break;
            case 'escalated':
                statusText = 'Escalated';
                statusClass += ' success-escalated'; // Distinct success color for escalated
                break;
            case 'already_handled': // History
                statusText = 'Success';
                statusClass += ' success-history'; // Gradient green + color for history
                break;
            case 'found_in_bpm':
                statusText = 'Success';
                statusClass += ' success-bpm'; // Gradient green + color for BPM
                break;
            case 'found_in_sanctions_bypass':
                statusText = 'Success';
                statusClass += ' success-sanctions'; // Gradient green + color for sanctions bypass
                break;
            case 'transaction_not_found_in_any_tab':
                statusText = 'Not Found'; // Or 'Checked'
                statusClass += ' success-not-found'; // Neutral/distinct color for not found
                break;
            case 'failed':
                statusText = 'Failed';
                statusClass += ' error'; // Existing error class
                break;
            default: // Fallback for older data or unexpected statuses
                statusText = 'Success'; // Or 'Info'
                statusClass += ' success'; // Default success color
                break;
        }

        let tooltip = '';
        if (transaction.statusMessage) {
            tooltip = escapeHtml(transaction.statusMessage);
        }
        if (transaction.status === 'failed' && transaction.errorCode) {
            tooltip += (tooltip ? ' | ' : '') + `Error code: ${escapeHtml(transaction.errorCode)}`;
        }
        
        statusHtml = `<span class="${statusClass}"${tooltip ? ` title="${tooltip}"` : ''}>${escapeHtml(statusText)}</span>`;
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${escapeHtml(transaction.transaction)}</td>
            <td>${escapeHtml(transaction.comment || '')}</td>
            <td>${escapeHtml(transaction.action)}</td>
            <td>${statusHtml}</td>
        `;
        
        transactionsTableBody.appendChild(row);
    });
}

// Security: Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    if (unsafe === undefined || unsafe === null) {
        return '';
    }
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Filter and search functionality
filterAction.addEventListener('change', loadTransactions);
searchTransactions.addEventListener('input', loadTransactions);

// Initialize - show only the transaction form section initially
document.addEventListener('DOMContentLoaded', () => {
    // Hide all sections except the first one
    const sections = document.querySelectorAll('.section');
    sections.forEach((section, index) => {
        if (index !== 0) {
            section.style.display = 'none';
        }
    });
});
