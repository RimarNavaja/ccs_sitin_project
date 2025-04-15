document.addEventListener("DOMContentLoaded", function () {
  // --- DOM Elements ---
  const labFilter = document.getElementById("lab-filter");
  const purposeFilter = document.getElementById("purpose-filter");
  const applyFiltersBtn = document.getElementById("apply-filters-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");
  const resultsContainer = document.getElementById("results-container");
  const resultsTableBody = document.getElementById("results-table-body");
  const noResultsRow = document.getElementById("no-results-row"); // Get the initial row

  const printBtn = document.getElementById("print-btn");
  const exportPdfBtn = document.getElementById("export-pdf-btn");
  const exportExcelBtn = document.getElementById("export-excel-btn");
  const exportCsvBtn = document.getElementById("export-csv-btn");

  // --- Event Listeners ---
  applyFiltersBtn.addEventListener("click", fetchDataAndPopulateTable);
  resetFiltersBtn.addEventListener("click", resetFiltersAndTable);
  printBtn.addEventListener("click", printReport);

  // Add listeners for export buttons (basic implementation for now)
  exportPdfBtn.addEventListener("click", () => exportReport("pdf"));
  exportExcelBtn.addEventListener("click", () => exportReport("excel"));
  exportCsvBtn.addEventListener("click", () => exportReport("csv"));

  // Fetch data immediately when page loads
  fetchDataAndPopulateTable();

  // --- Functions ---

  // Function to fetch data based on filters and update the table
  function fetchDataAndPopulateTable() {
    const lab = labFilter.value;
    const purpose = purposeFilter.value;

    // Show loading state in table
    resultsTableBody.innerHTML = `
              <tr>
                  <td colspan="9" class="px-6 py-10 text-center text-gray-500 italic">
                      Loading report data...
                  </td>
              </tr>
          `;
    resultsContainer.classList.remove("hidden"); // Show container while loading

    // Construct the URL with query parameters
    const url = new URL("/admin/fetch-report-data", window.location.origin);
    if (lab) url.searchParams.append("lab", lab);
    if (purpose) url.searchParams.append("purpose", purpose);

    // Fetch data from the backend
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success && data.results) {
          populateTable(data.results);
        } else {
          showError(data.message || "Failed to fetch report data.");
        }
      })
      .catch((error) => {
        console.error("Error fetching report data:", error);
        showError(`An error occurred: ${error.message}`);
      });
  }

  // Function to populate the table with data
  function populateTable(results) {
    resultsTableBody.innerHTML = ""; // Clear previous results or loading message

    if (results.length === 0) {
      resultsTableBody.innerHTML = `
                  <tr>
                      <td colspan="9" class="px-6 py-10 text-center text-gray-500 italic">
                          No records found matching the selected filters.
                      </td>
                  </tr>
              `;
    } else {
      results.forEach((record) => {
        const row = document.createElement("tr");
        row.innerHTML = `
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${record.id}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${record.idno}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${record.student_name}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.course}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.purpose}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.lab}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.date}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.time_in}</td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${record.time_out}</td>
                  `;
        resultsTableBody.appendChild(row);
      });
    }
    resultsContainer.classList.remove("hidden"); // Ensure container is visible
  }

  // Function to show error messages in the table
  function showError(message) {
    resultsTableBody.innerHTML = `
              <tr>
                  <td colspan="9" class="px-6 py-10 text-center text-red-500 font-medium">
                      Error: ${message}
                  </td>
              </tr>
          `;
    resultsContainer.classList.remove("hidden"); // Ensure container is visible
  }

  // Function to reset filters and clear the table
  function resetFiltersAndTable() {
    labFilter.value = "";
    purposeFilter.value = "";
    resultsTableBody.innerHTML = ""; // Clear table body
    if (noResultsRow) {
      // Add back the initial placeholder row if it exists
      resultsTableBody.appendChild(noResultsRow.cloneNode(true));
    }
    resultsContainer.classList.add("hidden"); // Hide the results container
  }

  // Function to handle printing
  function printReport() {
    // Optional: Add specific print styles or prepare the page
    window.print();
  }

  // Function to handle exporting (requires backend implementation)
  function exportReport(format) {
    const lab = labFilter.value;
    const purpose = purposeFilter.value;

    // Construct the base URL for the export endpoint (adjust as needed)
    const baseUrl = `/admin/export/${format}`; // Example: /admin/export/csv
    const url = new URL(baseUrl, window.location.origin);

    // Add filter parameters
    if (lab) url.searchParams.append("lab", lab);
    if (purpose) url.searchParams.append("purpose", purpose);

    // Trigger the download by navigating to the URL
    // The backend should handle generating the file and sending it
    window.location.href = url.toString();

    // Note: Backend routes like /admin/export/csv, /admin/export/pdf, etc.,
    // need to be created in app.py to handle these requests.
    console.log(`Initiating ${format.toUpperCase()} export with URL: ${url}`);
    // alert(`Exporting to ${format.toUpperCase()}... (Backend endpoint required)`);
  }
});
