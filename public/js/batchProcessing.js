function processBatch() {
  const fileInput = document.getElementById('csvFileInput');
  const file = fileInput.files[0];
  const resultDiv = document.getElementById('batchResult');
  const downloadLink = document.getElementById('downloadLink');

  if (!file) {
    resultDiv.innerHTML = '<p style="color: red;">Please select a CSV file.</p>';
    return;
  }

  if (file.name.split('.').pop().toLowerCase() !== 'csv') {
    resultDiv.innerHTML = '<p style="color: red;">File must be a CSV.</p>';
    return;
  }

  const reader = new FileReader();
  reader.onload = function(e) {
    const text = e.target.result;
    const lines = text.split('\n');
    let results = [];

    for (let i = 1; i < lines.length; i++) { // Skip header if exists
      const transactionId = lines[i].trim().split(',')[0];
      if (transactionId) {
        // Simulate processing. Replace with actual API call or logic.
        const isSuccess = Math.random() > 0.5; // Random success/fail for demo
        const reason = isSuccess ? '' : 'Not in BPM';
        results.push({
          id: transactionId,
          status: isSuccess ? 'SUCCESS' : 'FAIL',
          reason: reason
        });
      }
    }

    let csvContent = 'Transaction ID,Status,Reason\n';
    results.forEach(result => {
      csvContent += `${result.id},${result.status},${result.reason}\n`;
    });

    resultDiv.innerHTML = '<p>Processing complete. See results below:</p>';
    resultDiv.innerHTML += '<pre>' + csvContent + '</pre>';

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    downloadLink.href = url;
    downloadLink.style.display = 'block';
    downloadLink.innerText = 'Download Results';
  };

  reader.readAsText(file);
}
