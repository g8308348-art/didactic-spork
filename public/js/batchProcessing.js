// Batch Processing Module
// Handles CSV validation, processing, progress feedback and result rendering.

const ACCEPTED_HEADERS = ["Transaction", "Market", "Action"];

// Initialise handlers once DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("processBatchBtn").addEventListener("click", processBatch);
  initTemplateLink();
});

function initTemplateLink() {
  const templateLink = document.getElementById("templateLink");
  const csvHeader = ACCEPTED_HEADERS.join(",") + "\n"; // Only header row
  const blob = new Blob([csvHeader], { type: "text/csv;charset=utf-8;" });
  templateLink.href = URL.createObjectURL(blob);
}

function processBatch() {
    const progressInfo = document.getElementById("progressInfo");
    const batchTable = document.getElementById("batchTable");
  const tableBody = batchTable.querySelector("tbody");
  batchTable.classList.remove("hidden");
  tableBody.innerHTML = ""; // Clear previous results

  const fileInput = document.getElementById("csvFileInput");
  const file = fileInput.files[0];
  const resultDiv = document.getElementById('batchResult');
  const downloadLink = document.getElementById('downloadLink');

    if (!file) {
    resultDiv.innerHTML = '<p style="color: red;">Please select a CSV file.</p>';
    return;
  }

    if (file.name.split(".").pop().toLowerCase() !== "csv") {
    resultDiv.innerHTML = '<p style="color: red;">File must be a CSV.</p>';
    return;
  }

    const reader = new FileReader();
    reader.onload = function (e) {
        const text = e.target.result;
    const lines = text.trim().split(/\r?\n/);

    // Validate headers
    const headers = lines[0].split(/,\s*/);
    const isHeaderValid = ACCEPTED_HEADERS.every((h, idx) => headers[idx] && headers[idx].trim() === h);
    if (!isHeaderValid) {
      resultDiv.innerHTML = `<p style="color:red;">Invalid CSV header. Expected columns: ${ACCEPTED_HEADERS.join(", ")}</p>`;
      return;
    }

    const total = lines.length - 1; // exclude header
    let processed = 0;
    let csvOutput = [...ACCEPTED_HEADERS, "Status", "Error Reason"].join(",") + "\n";

    const processLine = (index) => {
      if (index >= lines.length) {
        // Finished processing
        const blob = new Blob([csvOutput], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.style.display = "block";
        downloadLink.innerText = "Download Results";
        progressInfo.innerText = `Processed ${processed} of ${total} transactions.`;
        return;
      }

      const cols = lines[index].split(/,\s*/);
      if (cols.length < 3 || cols.every(c => c.trim() === "")) {
        // skip empty/invalid line
        processLine(index + 1);
        return;
      }

      const [transaction, market, action] = cols;
      // Simulate processing logic - replace with real API call
      const isSuccess = Math.random() >= 0.5;
      const errorReason = isSuccess ? "" : "Processing error";
      const statusText = isSuccess ? "SUCCESS" : "FAIL";

      // Add to table
      const row = document.createElement("tr");
      row.className = isSuccess ? "success-row" : "fail-row";
      row.innerHTML = `
        <td>${transaction}</td>
        <td>${market}</td>
        <td>${action}</td>
        <td>${statusText}</td>
        <td>${errorReason}</td>
      `;
      tableBody.appendChild(row);

      // Append to CSV
      csvOutput += `${transaction},${market},${action},${statusText},${errorReason}\n`;

      processed++;
      progressInfo.innerText = `Processed ${processed} of ${total} transactions.`;

      // Process next line asynchronously to allow UI update
      setTimeout(() => processLine(index + 1), 0);
    };

    // Start processing from first data line
    processLine(1);


  };

  reader.readAsText(file);
}
