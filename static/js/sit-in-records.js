document.addEventListener("DOMContentLoaded", function () {
  // Elements
  const dateFilter = document.getElementById("date-filter");
  const courseFilter = document.getElementById("course-filter");
  const applyFiltersBtn = document.getElementById("apply-filters-btn");
  const recordsTableBody = document.getElementById("records-table-body");
  const paginationContainer = document.getElementById("pagination-container");
  const recordsCount = document.getElementById("records-count");

  // Pagination state
  let currentPage = 1;
  const perPage = 10;
  let totalPages = 0;

  // Initial load of records
  loadRecords();

  // Event listeners
  applyFiltersBtn.addEventListener("click", function () {
    currentPage = 1; // Reset to first page when applying new filters
    loadRecords();
  });

  // Function to load records with current filters and pagination
  function loadRecords() {
    // Show loading state
    recordsTableBody.innerHTML = `
      <tr>
        <td colspan="9" class="px-6 py-4 text-center">
          <div class="flex justify-center">
            <p class="text-gray-500">Loading records...</p>
          </div>
        </td>
      </tr>
    `;

    // Build query parameters
    const params = new URLSearchParams({
      page: currentPage,
      per_page: perPage,
      date_filter: dateFilter.value.toLowerCase().replace(" ", "_"),
      course_filter:
        courseFilter.value === "All Courses" ? "all" : courseFilter.value,
    });

    // Fetch records data
    fetch(`/admin/get-sit-in-records?${params.toString()}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          displayRecords(data.records);
          updatePagination(data.page, data.total_pages, data.total);
        } else {
          showError(data.message || "Failed to load records");
        }
      })
      .catch((error) => {
        console.error("Error loading records:", error);
        showError("An error occurred while loading records");
      });
  }

  // Function to display the records in the table
  function displayRecords(records) {
    if (records.length === 0) {
      recordsTableBody.innerHTML = `
        <tr>
          <td colspan="10" class="px-6 py-4 text-center text-gray-500">
            No records found
          </td>
        </tr>
      `;
      return;
    }

    recordsTableBody.innerHTML = "";

    records.forEach((record, index) => {
      const row = document.createElement("tr");
      row.className = index % 2 === 0 ? "bg-white" : "bg-gray-50";

      row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.id}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.student_id}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center">
            <div class="text-sm font-medium text-gray-900">${record.student_name}</div>
          </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.course}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.purpose}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.lab}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.date}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.start_time}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-900">${record.end_time}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
          <button 
            class="text-red-600 cursor-pointer hover:text-red-900 delete-record-btn" 
            data-record-id="${record.id}">
            Delete
          </button>
        </td>
      `;

      recordsTableBody.appendChild(row);
    });

    // Add event listeners to delete buttons
    document.querySelectorAll(".delete-record-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const recordId = this.getAttribute("data-record-id");
        deleteRecord(recordId);
      });
    });
  }

  // Function to update pagination controls
  function updatePagination(page, totalPages, totalRecords) {
    currentPage = page;
    this.totalPages = totalPages;

    // Update record count text
    recordsCount.textContent = `Showing ${
      (page - 1) * perPage + 1
    } to ${Math.min(page * perPage, totalRecords)} of ${totalRecords} results`;

    // Generate pagination HTML
    let paginationHTML = "";

    // Previous button
    paginationHTML += `
      <a href="#" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 ${
        page === 1 ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
      }" 
         ${page === 1 ? "" : 'id="prev-page"'}>
        <span class="sr-only">Previous</span>
        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </a>
    `;

    // Page numbers
    const visiblePages = calculateVisiblePages(page, totalPages);

    visiblePages.forEach((p) => {
      if (p === "...") {
        paginationHTML += `
          <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
            ...
          </span>
        `;
      } else {
        const isCurrentPage = p === page;
        paginationHTML += `
          <a href="#" 
             class="${
               isCurrentPage
                 ? "z-10 bg-violet-50 border-violet-500 text-violet-600"
                 : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
             } relative inline-flex items-center px-4 py-2 border text-sm font-medium page-number" 
             data-page="${p}">
            ${p}
          </a>
        `;
      }
    });

    // Next button
    paginationHTML += `
      <a href="#" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 ${
        page === totalPages || totalPages === 0
          ? "opacity-50 cursor-not-allowed"
          : "cursor-pointer"
      }" 
         ${page === totalPages || totalPages === 0 ? "" : 'id="next-page"'}>
        <span class="sr-only">Next</span>
        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
        </svg>
      </a>
    `;

    paginationContainer.innerHTML = paginationHTML;

    // Add event listeners to pagination controls
    const prevPageBtn = document.getElementById("prev-page");
    if (prevPageBtn) {
      prevPageBtn.addEventListener("click", function (e) {
        e.preventDefault();
        if (currentPage > 1) {
          currentPage--;
          loadRecords();
        }
      });
    }

    const nextPageBtn = document.getElementById("next-page");
    if (nextPageBtn) {
      nextPageBtn.addEventListener("click", function (e) {
        e.preventDefault();
        if (currentPage < totalPages) {
          currentPage++;
          loadRecords();
        }
      });
    }

    document.querySelectorAll(".page-number").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const pageNum = parseInt(this.getAttribute("data-page"), 10);
        if (pageNum !== currentPage) {
          currentPage = pageNum;
          loadRecords();
        }
      });
    });
  }

  // Helper function to calculate which page numbers to show
  function calculateVisiblePages(currentPage, totalPages) {
    if (totalPages <= 7) {
      // Show all pages if 7 or fewer
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    // Otherwise, show current page, the first and last pages,
    // and some pages around the current page
    const pages = [1];

    if (currentPage > 3) {
      pages.push("...");
    }

    // Pages around current page
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (currentPage < totalPages - 2) {
      pages.push("...");
    }

    pages.push(totalPages);

    return pages;
  }

  // Function to delete a record
  function deleteRecord(recordId) {
    if (
      !confirm(
        "Are you sure you want to delete this record? This action cannot be undone."
      )
    ) {
      return;
    }

    const formData = new FormData();

    fetch(`/admin/delete-sit-in-record/${recordId}`, {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Refresh the records
          loadRecords();
          // Show success message
          alert(data.message);
        } else {
          alert(data.message || "Failed to delete record");
        }
      })
      .catch((error) => {
        console.error("Error deleting record:", error);
        alert("An error occurred while deleting the record");
      });
  }

  // Helper function to show error message
  function showError(message) {
    recordsTableBody.innerHTML = `
      <tr>
        <td colspan="10" class="px-6 py-4 text-center text-red-500">
          ${message}
        </td>
      </tr>
    `;
  }
});
