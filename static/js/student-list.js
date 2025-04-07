document.addEventListener("DOMContentLoaded", function () {
  // DOM elements
  const searchInput = document.getElementById("search");
  const courseFilter = document.getElementById("course-filter");
  const searchButton = document.getElementById("search-btn");
  const resetButton = document.getElementById("reset-btn");
  const exportButton = document.getElementById("export-btn");
  const studentsTableBody = document.getElementById("students-table-body");
  const prevPageBtn = document.getElementById("prev-page");
  const nextPageBtn = document.getElementById("next-page");
  const prevPageMobileBtn = document.getElementById("prev-page-mobile");
  const nextPageMobileBtn = document.getElementById("next-page-mobile");
  const pageNumbersContainer = document.getElementById("page-numbers");
  const pageStart = document.getElementById("page-start");
  const pageEnd = document.getElementById("page-end");
  const totalStudents = document.getElementById("total-students");

  // Modal elements
  const deleteStudentModal = document.getElementById("delete-student-modal");
  const closeDeleteModalBtn = document.getElementById("close-delete-modal");
  const deleteStudentName = document.getElementById("delete-student-name");
  const cancelDeleteBtn = document.getElementById("cancel-delete");
  const confirmDeleteBtn = document.getElementById("confirm-delete");

  // State variables
  let currentPage = 1;
  let totalPages = 1;
  let studentsPerPage = 10;
  let selectedStudentId = null;
  let currentSearchTerm = "";
  let currentCourseFilter = "";

  // Initialize the student list
  fetchStudents();

  // Event listeners
  searchButton.addEventListener("click", function () {
    currentSearchTerm = searchInput.value.trim();
    currentCourseFilter = courseFilter.value;
    currentPage = 1;
    fetchStudents();
  });

  resetButton.addEventListener("click", function () {
    searchInput.value = "";
    courseFilter.value = "";
    currentSearchTerm = "";
    currentCourseFilter = "";
    currentPage = 1;
    fetchStudents();
  });

  prevPageBtn.addEventListener("click", function () {
    if (currentPage > 1) {
      currentPage--;
      fetchStudents();
    }
  });

  nextPageBtn.addEventListener("click", function () {
    if (currentPage < totalPages) {
      currentPage++;
      fetchStudents();
    }
  });

  prevPageMobileBtn.addEventListener("click", function () {
    if (currentPage > 1) {
      currentPage--;
      fetchStudents();
    }
  });

  nextPageMobileBtn.addEventListener("click", function () {
    if (currentPage < totalPages) {
      currentPage++;
      fetchStudents();
    }
  });

  exportButton.addEventListener("click", exportStudentList);

  // Modal event listeners
  closeDeleteModalBtn.addEventListener("click", () =>
    hideModal("delete-student-modal")
  );
  cancelDeleteBtn.addEventListener("click", () =>
    hideModal("delete-student-modal")
  );
  confirmDeleteBtn.addEventListener("click", deleteStudent);

  // Search on Enter key press
  searchInput.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
      searchButton.click();
    }
  });

  // Add event listener for reset all sessions button
  document
    .getElementById("reset-all-sessions-btn")
    .addEventListener("click", function () {
      if (
        confirm("Are you sure you want to reset sessions for all students?")
      ) {
        fetch("/admin/reset-all-sessions", {
          method: "POST",
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              alert(data.message);
              fetchStudents(); // Refresh the list
            } else {
              alert("Error: " + data.message);
            }
          })
          .catch((error) => {
            console.error("Error resetting sessions:", error);
            alert("An error occurred while resetting sessions");
          });
      }
    });

  // Functions
  function fetchStudents() {
    const loader = `<tr><td colspan="7" class="text-center py-4">Loading students...</td></tr>`;
    studentsTableBody.innerHTML = loader;

    const url = `/admin/get-students?page=${currentPage}&per_page=${studentsPerPage}&search=${encodeURIComponent(
      currentSearchTerm
    )}&course=${encodeURIComponent(currentCourseFilter)}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          renderStudents(data.students);
          updatePagination(data.page, data.total_pages, data.total);
        } else {
          showError("Failed to fetch students: " + data.message);
        }
      })
      .catch((error) => {
        console.error("Error fetching students:", error);
        showError("An error occurred while fetching students");
      });
  }

  function renderStudents(students) {
    if (students.length === 0) {
      studentsTableBody.innerHTML = `<tr><td colspan="7" class="text-center py-4">No students found</td></tr>`;
      return;
    }

    let html = "";
    students.forEach((student) => {
      html += `
        <tr>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            ${student.idno}
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="h-8 w-8 rounded-full overflow-hidden bg-gray-100 mr-3">
                <img src="${student.photo_url}" alt="${student.name}" class="h-full w-full object-cover">
              </div>
              <div class="text-sm font-medium text-gray-900">${student.name}</div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${student.course}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${student.year_level}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${student.email}
          </td>
          <td class=" px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${student.student_session}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <div class="flex  space-x-2">
              <a href="/admin/sit-in-form?student=${student.idno}" class="bg-green-500 text-white hover:bg-green-400 cursor-pointer rounded-md px-2 py-0.5">
                New Sit-in
              </a>
              <button class="cursor-pointer bg-red-600 text-white font-switzer hover:bg-red-500 rounded-md px-2 py-0.5 delete-student-btn" data-id="${student.idno}" data-name="${student.name}">
                Remove
              </button>
              <button class="cursor-pointer bg-blue-600 hover:bg-blue-500 text-white font-switzer rounded-md px-2 py-0.5 reset-session-btn" data-id="${student.idno}" data-name="${student.name}">
                Reset Session
              </button>
            </div>
          </td>
        </tr>
      `;
    });

    studentsTableBody.innerHTML = html;

    // Only keep delete button event listeners
    document.querySelectorAll(".delete-student-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const studentId = this.getAttribute("data-id");
        const studentName = this.getAttribute("data-name");

        selectedStudentId = studentId;
        deleteStudentName.textContent = studentName;

        showModal("delete-student-modal");
      });
    });

    // Add event listeners for reset session buttons
    document.querySelectorAll(".reset-session-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const studentId = this.getAttribute("data-id");
        const studentName = this.getAttribute("data-name");

        if (
          confirm(
            `Are you sure you want to reset sessions for student: ${studentName}?`
          )
        ) {
          const formData = new FormData();
          formData.append("student_id", studentId); // Fix: Create FormData correctly

          fetch("/admin/reset-session", {
            method: "POST",
            body: formData,
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                alert(data.message);
                fetchStudents(); // Refresh the list
              } else {
                alert("Error: " + data.message);
              }
            })
            .catch((error) => {
              console.error("Error resetting session:", error);
              alert("An error occurred while resetting session");
            });
        }
      });
    });
  }

  function updatePagination(page, pages, total) {
    currentPage = page;
    totalPages = pages;

    // Update text indicators
    const start = (page - 1) * studentsPerPage + 1;
    const end = Math.min(page * studentsPerPage, total);

    pageStart.textContent = total > 0 ? start : 0;
    pageEnd.textContent = end;
    totalStudents.textContent = total;

    // Enable/disable prev/next buttons
    prevPageBtn.disabled = page <= 1;
    nextPageBtn.disabled = page >= pages;
    prevPageMobileBtn.disabled = page <= 1;
    nextPageMobileBtn.disabled = page >= pages;

    // Update page number buttons
    pageNumbersContainer.innerHTML = "";

    // Determine range of page numbers to show
    const maxPages = 5;
    let startPage = Math.max(1, page - Math.floor(maxPages / 2));
    let endPage = Math.min(pages, startPage + maxPages - 1);

    if (endPage - startPage + 1 < maxPages) {
      startPage = Math.max(1, endPage - maxPages + 1);
    }

    // Add first page if not in range
    if (startPage > 1) {
      addPageButton(1);
      if (startPage > 2) {
        addEllipsis();
      }
    }

    // Add page numbers
    for (let i = startPage; i <= endPage; i++) {
      addPageButton(i);
    }

    // Add last page if not in range
    if (endPage < pages) {
      if (endPage < pages - 1) {
        addEllipsis();
      }
      addPageButton(pages);
    }
  }

  function addPageButton(pageNum) {
    const button = document.createElement("button");
    button.textContent = pageNum;
    button.className =
      pageNum === currentPage
        ? "z-10 bg-violet-50 border-violet-500 text-violet-600 relative inline-flex items-center px-4 py-2 border text-sm font-medium"
        : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50 relative inline-flex items-center px-4 py-2 border text-sm font-medium";

    button.addEventListener("click", function () {
      currentPage = pageNum;
      fetchStudents();
    });

    pageNumbersContainer.appendChild(button);
  }

  function addEllipsis() {
    const span = document.createElement("span");
    span.className =
      "relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700";
    span.textContent = "...";
    pageNumbersContainer.appendChild(span);
  }

  function showError(message) {
    studentsTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="px-6 py-4 text-center text-red-500">
          ${message}
        </td>
      </tr>
    `;
  }

  function deleteStudent() {
    const formData = new FormData();
    formData.append("student_id", selectedStudentId);

    fetch("/admin/delete-student", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          alert(data.message);
          hideModal("delete-student-modal");
          fetchStudents(); // Refresh the list
        } else {
          alert("Error: " + data.message);
        }
      })
      .catch((error) => {
        console.error("Error deleting student:", error);
        alert("An error occurred while deleting the student");
      });
  }

  function exportStudentList() {
    // Construct URL with current filters
    const url = `/admin/get-students?per_page=1000&search=${encodeURIComponent(
      currentSearchTerm
    )}&course=${encodeURIComponent(currentCourseFilter)}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.students.length > 0) {
          // Convert to CSV
          let csv =
            "ID Number,Name,Course,Year Level,Email,Remaining Sessions\n";

          data.students.forEach((student) => {
            csv += `${student.idno},"${student.name}",${student.course},${student.year_level},${student.email},${student.student_session}\n`;
          });

          // Create download link
          const blob = new Blob([csv], { type: "text/csv" });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.setAttribute("hidden", "");
          a.setAttribute("href", url);
          a.setAttribute("download", "student-list.csv");
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        } else {
          alert("No students to export");
        }
      })
      .catch((error) => {
        console.error("Error exporting students:", error);
        alert("An error occurred while exporting the student list");
      });
  }

  // Show/hide modal functions
  function showModal(modalId) {
    document.getElementById(modalId).style.display = "flex";
  }

  function hideModal(modalId) {
    document.getElementById(modalId).style.display = "none";
  }
});
