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
  const processBtn = document.getElementById("processBatchBtn");
  const setBatchBusy = (busy) => {
    if (!processBtn) return;
    processBtn.disabled = !!busy;
    processBtn.textContent = busy ? 'Processing ...' : 'Process Batch';
  };
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
    setBatchBusy(false); // Add this line
    return;
  }

  setBatchBusy(true); // Add this line

  const reader = new FileReader();
  reader.onload = function (e) {
        const text = e.target.result;
    const lines = text.trim().split(/\r?\n/);

    // Validate headers
    const headers = lines[0].split(/,\s*/);
    const isHeaderValid = ACCEPTED_HEADERS.every((h, idx) => headers[idx] && headers[idx].trim() === h);
    if (!isHeaderValid) {
      setBatchBusy(false);
      resultDiv.innerHTML = `<p style="color:red;">Invalid CSV header. Expected columns: ${ACCEPTED_HEADERS.join(", ")}</p>`;
      return;
    }

    // Build data lines excluding empty/invalid rows
    const dataLines = lines.slice(1).filter((ln) => {
      const cols = ln.split(/,\s*/);
      return !(cols.length < 3 || cols.every((c) => c.trim() === ""));
    });
    const total = dataLines.length; // number of valid transactions
    let processed = 0;
    let csvOutput = [...ACCEPTED_HEADERS, "Status", "Error Reason"].join(",") + "\n";

    // Validation constants (keep in sync with script.js and bpm_page.Options)
    const VALID_ACTIONS = ['STP-Release', 'Release', 'Block', 'Reject'];
    const VALID_MARKETS = [
      'Unclassified', 'APS-MT', 'CBPR-MX', 'SEPA-Classic', 'RITS-MX', 'LYNX-MX',
      'EnterpriseISO', 'CHAPS-MX', 'T2S-MX', 'BESS-MT', 'CHIPS-MX', 'SEPA-Instant',
      'FEDWIRE', 'Taiwan-MX', 'CHATS-MX', 'PEPPLUS-IAT', 'TSF-TRIGGER'
    ];

    const validateCsvRow = (transaction, market, action) => {
      if (!transaction || transaction.length > 64) {
        return { ok: false, reason: 'Transaction must be 1-64 characters' };
      }
      if (!VALID_ACTIONS.includes(action)) {
        return { ok: false, reason: `Invalid action: ${action}` };
      }
      if (!VALID_MARKETS.includes(market)) {
        return { ok: false, reason: `Invalid market: ${market}` };
      }
      return { ok: true };
    };

    // Helper to POST JSON and parse result
    const postJson = async (url, payload) => {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      let data = {};
      try { data = await resp.json(); } catch (_) { /* keep empty */ }
      return { ok: resp.ok, status: resp.status, data };
    };

    // Decide whether to call /api based on BPM result
    const decideFromBpm = (bpmResult) => {
      // Default: do NOT call /api
      const out = { callApi: false, reason: '', statusLabel: 'No action' };
      if (!bpmResult || typeof bpmResult !== 'object') {
        out.reason = 'Invalid BPM result';
        return out;
      }
      const env = (bpmResult.environment || '').toString().trim().toUpperCase();
      const details = bpmResult.details || {};
      const col4 = (details.current_status || '').toString();
      const col11 = (details.bpm_status || '').toString();
      const col4Lower = col4.toLowerCase();
      const col11Lower = col11.toLowerCase();

      // Step 1 — Global short-circuit: BUAT -> do NOT call /api
      if (env === 'BUAT') {
        out.reason = 'BPM environment BUAT';
        return out;
      }

      // Step 2 — Check 4th column
      if (col4Lower.includes('undefined')) {
        out.reason = 'CURRENT STATUS is UNDEFINED';
        return out;
      }
      if (col4Lower.includes('sendresponseto') || col4Lower.includes('sentresponseto')) {
        out.reason = 'NO HIT Transaction (SendResponseTo)';
        return out;
      }
      if (col4Lower.includes('businessresponseprocessed')) {
        out.reason = 'Response from Firco received';
        return out;
      }
      const col4IsPosted = col4Lower.includes('postedtxntofirco');

      // Step 3 — Check 11th column (STATUS)
      const statusHasSuccess = col11Lower.includes('success');
      const statusHasFailure = col11Lower.includes('failure');
      const statusHasWarning = col11Lower.includes('warning');

      if (statusHasFailure || statusHasWarning) {
        out.reason = `BPM STATUS indicates ${statusHasFailure ? 'FAILURE' : 'WARNING'}: ${col11}`;
        return out;
      }

      if (statusHasSuccess) {
        if (col4Lower.includes('sendresponseto') || col4Lower.includes('sentresponseto')) {
          out.reason = 'SUCCESS + SendResponseTo => No action';
          return out;
        }
        if (col4Lower.includes('businessresponseprocessed')) {
          out.reason = 'SUCCESS + BusinessResponseProcessed => No action';
          return out;
        }
        if (col4IsPosted) {
          out.callApi = true;
          out.reason = 'SUCCESS + PostedTxnToFirco => proceed';
          out.statusLabel = 'BPM_OK';
          return out;
        }
      }

      // Step 2 allowed calling when PostedTxnToFirco regardless of status; but Step 3 refines on SUCCESS.
      // If none matched yet, and 4th is PostedTxnToFirco without explicit SUCCESS, still allow per Step 2.
      if (col4IsPosted) {
        out.callApi = true;
        out.reason = 'PostedTxnToFirco => proceed';
        out.statusLabel = 'BPM_OK';
        return out;
      }

      // Step 4 — Default: do NOT call /api; carry BPM message when available
      out.reason = (bpmResult && bpmResult.message) ? bpmResult.message : 'BPM rules: default skip';
      return out;
    };

    const processLine = async (index) => {
      if (index >= dataLines.length) {
        // Finished processing
        const blob = new Blob([csvOutput], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.style.display = "block";
        downloadLink.innerText = "Download Results";
        progressInfo.innerText = `Processed ${processed} of ${total} transactions.`;
        setBatchBusy(false);
        return;
      }

      const cols = dataLines[index].split(/,\s*/);

      const [transaction, market, action] = cols.map(c => c.trim());
      // Add to table early
      const row = document.createElement("tr");
      row.className = "pending-row";
      row.innerHTML = `
        <td>${transaction}</td>
        <td>${market}</td>
        <td>${action}</td>
        <td>VALIDATING</td>
        <td></td>
      `;
      tableBody.appendChild(row);

      let finalStatus = "";
      let finalReason = "";

      try {
        // Client-side validation first
        const val = validateCsvRow(transaction, market, action);
        if (!val.ok) {
          finalStatus = 'validation_error';
          finalReason = val.reason;
          row.className = 'fail-row';
          row.cells[3].textContent = finalStatus;
          row.cells[4].textContent = finalReason;
        } else {
        // 1) BPM validation
        const bpmPayload = { transactionId: transaction, marketType: market };
        const bpmResp = await postJson('/api/bpm', bpmPayload);

        if (!bpmResp.ok || !bpmResp.data || bpmResp.data.status !== 'ok') {
          // BPM failed -> stop here
          finalStatus = 'FAIL';
          finalReason = bpmResp.data?.message || `BPM validation failed (HTTP ${bpmResp.status})`;
          row.className = 'fail-row';
          row.cells[3].textContent = finalStatus;
          row.cells[4].textContent = finalReason;
        } else {
          // Evaluate BPM result to decide whether to proceed with /api
          const bpm = (bpmResp.data && bpmResp.data.results && bpmResp.data.results.bpmResult) || {};
          const decision = decideFromBpm(bpm);

          if (!decision.callApi) {
            // Skip /api per BPM rules
            finalStatus = decision.statusLabel || 'No action';
            // Prefer specific mapping from 4th column scenarios when available
            if (decision.reason) {
              finalReason = `BPM: ${decision.reason}`;
            } else {
              finalReason = bpm?.message || 'BPM rule decided to skip';
            }
            row.className = 'success-row';
            row.cells[3].textContent = finalStatus;
            row.cells[4].textContent = finalReason;
          } else {
            // Show quick BPM success feedback
            row.className = 'success-row';
            row.cells[3].textContent = decision.statusLabel || 'BPM_OK';
            row.cells[4].textContent = '';

          // 2) Proceed to main /api call, using FircoPage.flow_start() semantics
          const apiPayload = {
            transaction: transaction,
            action: action,
            comment: 'Batch Processing',
            transactionType: market,
          };
          const apiResp = await postJson('/api', apiPayload);

          // Map UI strictly based on backend result fields
          const r = apiResp.data || {};
          const success = Boolean(r.success);
          const status = r.status || (apiResp.ok ? 'unknown' : 'processing_error');
          const statusDetail = r.status_detail || '';
          const message = r.message || '';

          // Determine row class by success flag
          row.className = success ? 'success-row' : 'fail-row';
          // Status column shows the backend status (not SUCCESS/FAIL), per flow_start logic
          finalStatus = statusDetail ? `${status} (${statusDetail})` : status;
          // Error reason shows backend message when present
          finalReason = message || (apiResp.ok ? '' : `Processing failed (HTTP ${apiResp.status})`);
          row.cells[3].textContent = finalStatus;
          row.cells[4].textContent = finalReason;
          }
        }
        // Close the outer 'else' started after client-side validation
        }
      } catch (err) {
        finalStatus = 'processing_error';
        finalReason = (err && err.message) ? err.message : 'Unexpected error';
        row.className = 'fail-row';
        row.cells[3].textContent = finalStatus;
        row.cells[4].textContent = finalReason;
      } finally {
        // Append to CSV with sanitized reason (no newlines/commas)
        csvOutput += `${transaction},${market},${action},${finalStatus},${(finalReason || '').replace(/\n|\r|,/g, ' ')}` + "\n";

        processed++;
        progressInfo.innerText = `Processed ${processed} of ${total} transactions.`;

        // Continue sequentially, yielding to UI
        setTimeout(() => { processLine(index + 1); }, 0);
      }
    };

    // Start processing from first data line
    processLine(0);


  };

  // Start busy state once we actually begin reading/processing
  setBatchBusy(true);
  reader.readAsText(file);
}
