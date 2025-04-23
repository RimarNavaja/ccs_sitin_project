document.addEventListener("DOMContentLoaded", function () {
  // Elements
  const searchInput = document.getElementById("student-search");
  const searchButton = document.getElementById("search-student-btn");
  const searchResults = document.getElementById("search-results");
  const studentInfo = document.getElementById("student-info");
  const sitInForm = document.getElementById("sit-in-form");
  const cancelFormBtn = document.getElementById("cancel-form-btn");

  // Student info elements
  const studentPhoto = document.getElementById("student-photo");
  const studentName = document.getElementById("student-name");
  const studentId = document.getElementById("student-id");
  const studentCourseYear = document.getElementById("student-course-year");
  const studentEmail = document.getElementById("student-email");
  const studentRemainingSessions = document.getElementById(
    "student-remaining-sessions"
  );
  const studentIdField = document.getElementById("student_id");

  // Active sessions element
  const activeSessionsTable = document.getElementById("active-sessions");
  const noSessionsRow = document.getElementById("no-sessions-row");
  const sessionCount = document.getElementById("session-count");

  // Function to check if a student has an active session
  function checkActiveSession(studentId) {
    return fetch("/admin/get-active-sessions")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.sessions.length > 0) {
          return data.sessions.some(
            (session) => session.user_id === studentId // Changed from student_id to user_id
          );
        }
        return false;
      })
      .catch((error) => {
        console.error("Error checking active sessions:", error);
        return false;
      });
  }

  // Function to perform student search
  function searchStudent() {
    const searchTerm = searchInput.value.trim();
    if (!searchTerm) {
      alert("Please enter a search term");
      return;
    }

    // Clear previous results
    searchResults.innerHTML = "";
    searchResults.classList.add("hidden");

    // AJAX request to search for students
    fetch("/admin/search-student", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `student_search=${encodeURIComponent(searchTerm)}`,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Show search results
          searchResults.classList.remove("hidden");

          // Create results list
          const resultsList = document.createElement("div");
          resultsList.className = "divide-y divide-gray-200";

          // Process each student
          const processStudents = async () => {
            for (const student of data.students) {
              // Check if student already has an active session
              const hasActiveSession = await checkActiveSession(student.idno);

              // Ensure photo_url is properly formatted
              const photoUrl =
                student.photo_url.startsWith("http") ||
                student.photo_url.startsWith("/")
                  ? student.photo_url
                  : "/" + student.photo_url.replace(/^\.\//, "");

              const studentItem = document.createElement("div");
              studentItem.className =
                "py-3 px-2 flex justify-between items-center hover:bg-gray-100";

              // Add warning badge if student has active session
              const activeSessionBadge = hasActiveSession
                ? `<span class="mx-2 px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">Active Session</span>`
                : "";

              studentItem.innerHTML = `
                <div class="flex items-center">
                  <div class="h-10 w-10 rounded-full overflow-hidden bg-gray-200 mr-3">
                    <img src="${photoUrl}" alt="${student.name}" class="h-full w-full object-cover">
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">${student.name}</div>
                    <div class="text-sm text-gray-500">${student.idno} • ${student.course}</div>
                  </div>
                  ${activeSessionBadge}
                </div>
                <button class="select-student-btn cursor-pointer px-5 py-1 bg-violet-200 tracking-wide text-violet-800 rounded-md text-sm font-switzer hover:bg-violet-300">
                  Select
                </button>
              `;

              // Add click event to select student
              studentItem
                .querySelector(".select-student-btn")
                .addEventListener("click", function () {
                  selectStudent(student);
                });

              resultsList.appendChild(studentItem);
            }
          };

          processStudents().then(() => {
            searchResults.appendChild(resultsList);
          });
        } else {
          // Show error message
          searchResults.classList.remove("hidden");
          searchResults.innerHTML = `
            <div class="bg-red-50 p-4 rounded-md">
              <p class="text-red-700">${data.message}</p>
            </div>
          `;
        }
      })
      .catch((error) => {
        console.error("Error searching for student:", error);
        searchResults.classList.remove("hidden");
        searchResults.innerHTML = `
          <div class="bg-red-50 p-4 rounded-md">
            <p class="text-red-700">An error occurred while searching. Please try again.</p>
          </div>
        `;
      });
  }

  // Function to select a student
  function selectStudent(student) {
    // Ensure photo_url is properly formatted for the selected student
    const photoUrl =
      student.photo_url.startsWith("http") || student.photo_url.startsWith("/")
        ? student.photo_url
        : "/" + student.photo_url.replace(/^\.\//, "");

    // Fill student info
    studentPhoto.src = photoUrl;
    studentName.textContent = student.name;
    studentId.textContent = `ID: ${student.idno}`;
    studentCourseYear.textContent = `${student.course} - ${student.year_level}`;
    studentEmail.textContent = student.email;
    studentRemainingSessions.textContent = `${student.remaining_sessions} sessions`;

    // Set form field
    studentIdField.value = student.idno;

    // Show student info and sit-in form
    searchResults.classList.add("hidden");
    studentInfo.classList.remove("hidden");
    sitInForm.classList.remove("hidden");

    // Clear search
    searchInput.value = "";
  }

  // Function to cancel form
  function cancelForm() {
    studentInfo.classList.add("hidden");
    sitInForm.classList.add("hidden");
    searchResults.classList.add("hidden");
    searchInput.value = "";
  }

  // Function to load active sessions
  function loadActiveSessions() {
    fetch("/admin/get-active-sessions")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.sessions.length > 0) {
          // Hide no sessions message
          noSessionsRow.style.display = "none";

          // Clear existing sessions (except the no-sessions-row)
          const existingRows = activeSessionsTable.querySelectorAll(
            "tr:not(#no-sessions-row)"
          );
          existingRows.forEach((row) => row.remove());

          // Add sessions to table
          data.sessions.forEach((session) => {
            const row = document.createElement("tr");

            // Format time from ISO string
            const startTime = new Date(session.start_time);
            const formattedTime = startTime.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            });

            // Calculate duration
            const now = new Date();
            const diffMs = now - startTime;
            const diffMins = Math.floor(diffMs / 60000);
            const duration =
              diffMins < 60
                ? `${diffMins} min`
                : `${Math.floor(diffMins / 60)}h ${diffMins % 60}m`;

            // Ensure photo_url is absolute
            const photoUrl =
              session.photo_url.startsWith("http") ||
              session.photo_url.startsWith("/")
                ? session.photo_url
                : "/" + session.photo_url.replace(/^\.\//, "");

            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="flex-shrink-0 h-8 w-8 rounded-full bg-gray-200 overflow-hidden">
                      <img src="${photoUrl}" alt="Student profile" class="h-8 w-8 rounded-full object-cover">
                    </div>
                    <div class="ml-4">
                      <div class="text-sm font-medium text-gray-900">${
                        session.student_name
                      }</div>
                      <div class="text-sm text-gray-500">${
                        session.student_id // Changed from student_id to user_id
                      }</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${formattedTime}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${duration}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${session.purpose}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${session.lab}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                  <span class="px-4 py-1 inline-flex text-xs leading-4 rounded-full ${
                    session.remaining_sessions < 5
                      ? " bg-red-200 text-red-800"
                      : " bg-blue-200 text-blue-800"
                  }">
                    ${session.remaining_sessions}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div class="flex space-x-2">
                    <form action="/admin/reward-sit-in/${
                      session.id
                    }" method="POST">
                      <button title="Reward student 1 point and end sit-in session." type="submit" class="bg-green-500 text-white rounded-md p-1 px-2 cursor-pointer hover:bg-green-600">
                        Reward
                      </button>
                    </form>
                    <form action="/admin/end-sit-in/${
                      session.id
                    }" method="POST">
                      <button title="End sit-in session with no reward." type="submit" class="bg-red-500 text-white rounded-md p-1 px-2 cursor-pointer hover:bg-red-600">
                        End Session
                      </button>
                    </form>
                  </div>
                </td>
              `;

            activeSessionsTable.appendChild(row);
          });

          // Update session count
          sessionCount.textContent = `${data.sessions.length} active session${
            data.sessions.length !== 1 ? "s" : ""
          }`;
        } else {
          // Show no sessions message
          noSessionsRow.style.display = "table-row";
          sessionCount.textContent = "0 active sessions";
        }
      })
      .catch((error) => {
        console.error("Error loading active sessions:", error);
      });
  }

  // --- NEW: Helper to get query parameter ---
  function getQueryParam(name) {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
  }

  // Event listeners
  searchButton.addEventListener("click", searchStudent);
  searchInput.addEventListener("keyup", function (event) {
    if (event.key === "Enter") {
      searchStudent();
    }
  });

  cancelFormBtn.addEventListener("click", cancelForm);

  // Load active sessions on page load
  loadActiveSessions();

  //  Auto-select student if ?student=IDNO is present ---
  async function autoSelectStudentFromQuery() {
    const studentIdno = getQueryParam("student");
    if (studentIdno) {
      // Clear previous results
      searchResults.innerHTML = "";
      searchResults.classList.add("hidden");

      // Search for the student by ID number
      const response = await fetch("/admin/search-student", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `student_search=${encodeURIComponent(studentIdno)}`,
      });
      const data = await response.json();
      if (data.success && data.students.length > 0) {
        // Find exact match by idno (in case multiple results)
        const student =
          data.students.find((s) => s.idno === studentIdno) || data.students[0];
        selectStudent(student);
      } else {
        // Show error message
        searchResults.classList.remove("hidden");
        searchResults.innerHTML = `
          <div class="bg-red-50 p-4 rounded-md">
            <p class="text-red-700">Student not found for ID: ${studentIdno}</p>
          </div>
        `;
      }
    }
  }

  //  Auto-select student if query param is present
  autoSelectStudentFromQuery();

  // Refresh active sessions every 30 seconds
  setInterval(loadActiveSessions, 30000);
});
