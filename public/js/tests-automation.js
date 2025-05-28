document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const testOptions = document.querySelectorAll('input[name="test"]');
    const generateBtn = document.getElementById('generate-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const dispositionBtn = document.getElementById('disposition-btn');
    const pdfBtn = document.getElementById('pdf-btn');
    const statusDiv = document.getElementById('status');
    const generatedFilesDiv = document.getElementById('generated-files');
    const customFieldsDiv = document.getElementById('custom-fields');
    
    // State
    let currentTest = null;
    let generatedFiles = [];
    let screenshotDirs = [];
    let currentOutputDir = '';
    let stage = 'none';
    let currentUpi = null;
    
    // API configuration
    const API_PORT = 8090;
    const API_BASE = `http://localhost:${API_PORT}`;
    
    // Event Listeners
    testOptions.forEach(option => {
        option.addEventListener('change', function() {
            currentTest = this.value;
            updateCustomFields();
            clearStatus();
            generatedFilesDiv.innerHTML = '';
            // reset flow
            stage = 'none';
            generateBtn.disabled = false;
            uploadBtn.disabled = true;
            dispositionBtn.disabled = true;
            pdfBtn.disabled = true;
        });
    });
    
    generateBtn.addEventListener('click', generateTestFiles);
    uploadBtn.addEventListener('click', uploadToMtex);
    dispositionBtn.addEventListener('click', dispositionTransactions);
    pdfBtn.addEventListener('click', generatePdf);
    
    // Initialize
    updateCustomFields();
    
    // Main Functions
    async function generateTestFiles() {
        if (!currentTest) {
            showStatus('Please select a test first', 'error');
            return;
        }
        
        try {
            console.log('Starting file generation...');
            showStatus('Generating test files...', 'info');
            generateBtn.disabled = true;
            
            const requestBody = {
                testName: currentTest,
                placeholders: {}
            };
            
            console.log('Sending request:', {
                url: `${API_BASE}/api/generate-test-files`,
                method: 'POST',
                body: requestBody
            });
            
            const response = await fetch(`${API_BASE}/api/generate-test-files`, {
                method: 'POST',
                mode: 'cors',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                let errorMsg = `HTTP error! Status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    console.error('Error response:', errorData);
                    errorMsg = errorData.error || errorMsg;
                } catch (e) {
                    const text = await response.text();
                    console.error('Failed to parse error response:', e, 'Response text:', text);
                    errorMsg = `${errorMsg} - ${text || 'No details provided'}`;
                }
                throw new Error(errorMsg);
            }
            
            const result = await response.json().catch(e => {
                console.error('Failed to parse JSON response:', e);
                throw new Error('Invalid response from server');
            });
            
            console.log('Response data:', result);
            
            if (result && result.success) {
                generatedFiles = Array.isArray(result.files) ? result.files : [];
                currentOutputDir = result.outputDir || '';
                showGeneratedFiles(generatedFiles);
                showStatus('Test files generated successfully!', 'success');
                currentUpi = result.upi;
                // advance flow
                stage = 'generated';
                uploadBtn.disabled = false;
                dispositionBtn.disabled = true;
                pdfBtn.disabled = true;
            } else {
                throw new Error(result.error || 'Failed to generate test files');
            }
        } catch (error) {
            const errorMsg = error.message || 'An unknown error occurred';
            console.error('Error generating test files:', errorMsg, error);
            showStatus(`Error: ${errorMsg}`, 'error');
        } finally {
            generateBtn.disabled = false;
        }
    }
    
    async function uploadToMtex() {
        if (generatedFiles.length === 0) {
            showStatus('No files to upload', 'error');
            return;
        }
        
        try {
            showStatus('Uploading files to MTex...', 'info');
            uploadBtn.disabled = true;
            
            // Call server API to trigger MTex upload
            const response = await fetch(`${API_BASE}/api/upload-to-mtex`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: generatedFiles, outputDir: currentOutputDir })
            });
            const result = await response.json();
            if (!result.success) throw new Error(result.error);
            
            showStatus('Files uploaded to MTex successfully!', 'success');
            // advance flow
            stage = 'uploaded';
            dispositionBtn.disabled = false;
            pdfBtn.disabled = true;
        } catch (error) {
            console.error('Upload error:', error);
            showStatus(`Upload failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
        }
    }
    
    // Disposition Transactions handler
    async function dispositionTransactions() {
        try {
            showStatus('Disposing transactions...', 'info');
            dispositionBtn.disabled = true;
            const outputDir = currentOutputDir;
            screenshotDirs = [];
            // Process each generated XML file for disposition
            for (const filePath of generatedFiles) {
                if (!filePath.toLowerCase().endsWith('.xml')) continue;
                const namePart = filePath.split('/').pop().split('.')[0];
                const action = namePart.split('_').pop();
                const timestampNoUnderscore = outputDir.replace('_', '');
                const upi = `${timestampNoUnderscore}-${action}`;
                const response = await fetch(`${API_BASE}/api/disposition-transactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ outputDir, action, upi })
                });
                const result = await response.json();
                if (!result.success) {
                    throw new Error(`Action ${action} failed: ${result.error}`);
                }
                // Use screenshotsDir or fallback to nested screenshot_path
                const dir = result.screenshotsDir || result.result.screenshot_path;
                screenshotDirs.push(dir);
            }
            stage = 'dispositioned';
            pdfBtn.disabled = false;
            showStatus('All dispositions processed!', 'success');
        } catch (e) {
            showStatus(`Disposition failed: ${e.message}`, 'error');
        }
    }
    
    // Generate PDF handler
    async function generatePdf() {
        try {
            showStatus('Generating PDF...', 'info');
            pdfBtn.disabled = true;
            const response = await fetch(`${API_BASE}/api/generate-pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ screenshotDirs })
            });
            const result = await response.json();
            if (!result.success) throw new Error(result.error);
            window.open(result.url, '_blank');
            showStatus('PDF generated successfully!', 'success');
        } catch (e) {
            showStatus(`PDF generation failed: ${e.message}`, 'error');
        } finally {
            pdfBtn.disabled = stage !== 'dispositioned';
        }
    }
    
    // Helper Functions
    function updateCustomFields() {
        customFieldsDiv.innerHTML = '';
        
        if (!currentTest) return;
        
        const templateInfo = document.createElement('div');
        templateInfo.className = 'info';
        templateInfo.textContent = `Selected test: ${currentTest}`;
        customFieldsDiv.appendChild(templateInfo);
    }
    
    function showGeneratedFiles(files) {
        generatedFilesDiv.innerHTML = '<h3>Generated Files:</h3>';
        
        if (!files || files.length === 0) {
            generatedFilesDiv.innerHTML += '<p>No files were generated.</p>';
            return;
        }
        
        const container = document.createElement('div');
        container.className = 'file-list';
        
        files.forEach(file => {
            if (!file) return;
            
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileName = file.split('/').pop();
            const fileUrl = `${API_BASE}/${file}`;
            
            const link = document.createElement('a');
            link.href = fileUrl;
            link.textContent = fileName;
            link.target = '_blank';
            
            fileItem.appendChild(link);
            container.appendChild(fileItem);
        });
        
        generatedFilesDiv.appendChild(container);
    }
    
    function showStatus(message, type = 'info') {
        statusDiv.textContent = message;
        statusDiv.className = type;
    }
    
    function clearStatus() {
        statusDiv.textContent = '';
        statusDiv.className = '';
    }
});
