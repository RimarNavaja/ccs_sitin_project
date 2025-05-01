// Timeout to hide flash messages
setTimeout(function () {
  var flashMessages = document.getElementById("flash-messages");
  if (flashMessages) {
    flashMessages.style.display = "none";
  }
}, 5000);

//toggle dropdown desktop - renamed to toggleProfileDropdown
function toggleProfileDropdown() {
  const dropdown = document.getElementById("user-menu");
  dropdown.classList.toggle("hidden");
}

// Toggle mobile menu
function toggleMobileMenu() {
  const mobileMenu = document.getElementById("mobile-menu");
  mobileMenu.classList.toggle("hidden");
}

// Close the dropdown if the user clicks outside of it
window.onclick = function (event) {
  if (
    !event.target.closest("#user-menu-button") &&
    !event.target.closest("#user-menu")
  ) {
    const dropdown = document.getElementById("user-menu");
    if (dropdown && !dropdown.classList.contains("hidden")) {
      dropdown.classList.add("hidden");
    }
  }
};

//open and close modal in profile.html
function openModal() {
  document.getElementById("editModal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("editModal").classList.add("hidden");
}

// Toggle dropdown function for labrules.html - keep this function name for content dropdowns
function toggleDropdown(contentId) {
  const content = document.getElementById(contentId);
  const button = content.previousElementSibling;
  const icon = button.querySelector("svg");

  // Toggle the content visibility with transitions
  content.classList.toggle("open");

  // Rotate the arrow icon
  if (icon) {
    if (!content.classList.contains("open")) {
      icon.classList.remove("rotate-180");
    } else {
      icon.classList.add("rotate-180");
    }
  }
}

// Admin dashboard specific functions

// Announcement management functions
function openAnnouncementModal() {
  const modal = document.getElementById("announcementModal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeAnnouncementModal() {
  const modal = document.getElementById("announcementModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

function openEditModal(id, title, content, priority, isActive) {
  const form = document.getElementById("editAnnouncementForm");
  if (form) {
    form.action = `/admin/announcements/edit/${id}`;

    document.getElementById("edit-title").value = title;
    document.getElementById("edit-content").value = content.replace(
      /\\n/g,
      "\n"
    );
    document.getElementById("edit-priority").value = priority;
    document.getElementById("edit-is-active").checked = isActive;

    document.getElementById("editAnnouncementModal").classList.remove("hidden");
  }
}

function closeEditModal() {
  const modal = document.getElementById("editAnnouncementModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

// Function to initialize admin dashboard event listeners
function initAdminDashboard() {
  const createReservationBtn = document.querySelector(
    ".admin-create-reservation"
  );
  if (createReservationBtn) {
    createReservationBtn.addEventListener("click", openReservationModal);
  }

  // Add announcement button listener if on announcements page
  const createAnnouncementBtn = document.querySelector(
    "button[onclick='openAnnouncementModal()']"
  );
  if (createAnnouncementBtn) {
    createAnnouncementBtn.addEventListener("click", openAnnouncementModal);
  }
}

// Initialize event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Initialize admin dashboard if we're on that page
  if (window.location.href.includes("/admin/")) {
    initAdminDashboard();
    fetchAdminPendingCount(); // Add this line to fetch count on load
  }

  // Add active class to current page link in navigation
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll("nav a");

  navLinks.forEach((link) => {
    const linkPath = link.getAttribute("href");
    if (linkPath && currentPath.includes(linkPath) && linkPath !== "/") {
      // Add active class to sidebar links
      link.classList.add("bg-violet-700", "text-white");
      link.classList.remove("text-gray-300", "hover:bg-gray-700");
    }
  });
});

//Notification
function fetchReservationNotif() {
  fetch("/api/reservation-notifications")
    .then((res) => res.json())
    .then((data) => {
      // Desktop
      const badge = document.getElementById("notif-badge");
      const list = document.getElementById("notif-list");
      // Mobile
      const badgeMobile = document.getElementById("notif-badge-mobile");
      const listMobile = document.getElementById("notif-list-mobile");
      if (data.count > 0) {
        if (badge) badge.style.display = "";
        if (badgeMobile) badgeMobile.style.display = "";
        let html = "";
        data.notifications.forEach((n) => {
          html += `<div class="p-3 font-switzer border-b last:border-b-0">
            <div class="flex items-center gap-2">
              <span class="font-bold ${
                n.status === "approved" ? "text-green-600" : "text-red-600"
              }">${n.status === "approved" ? "Approved" : "Disapproved"}</span>
              <span class="text-xs text-gray-400">${n.date} ${n.time}</span>
            </div>
            <div class="text-xs text-gray-700">Lab: <b>${
              n.lab
            }</b> | Purpose: <b>${n.purpose}</b></div>
          </div>`;
        });
        if (list) list.innerHTML = html;
        if (listMobile) listMobile.innerHTML = html;
      } else {
        if (badge) badge.style.display = "none";
        if (badgeMobile) badgeMobile.style.display = "none";
        if (list)
          list.innerHTML =
            '<div class="p-3 text-gray-500 text-sm">No new notifications.</div>';
        if (listMobile)
          listMobile.innerHTML =
            '<div class="p-3 text-gray-500 text-sm">No new notifications.</div>';
      }
    });
}

function toggleNotifDropdown() {
  const dd = document.getElementById("notif-dropdown");
  dd.classList.toggle("hidden");
  if (!dd.classList.contains("hidden")) {
    fetchReservationNotif();
  }
}
function toggleNotifDropdownMobile() {
  const dd = document.getElementById("notif-dropdown-mobile");
  dd.classList.toggle("hidden");
  if (!dd.classList.contains("hidden")) {
    fetchReservationNotif();
  }
}

function markNotifRead() {
  fetch("/api/mark-reservation-notif-read", { method: "POST" }).then(() => {
    fetchReservationNotif();
    const badge = document.getElementById("notif-badge");
    if (badge) badge.style.display = "none";
  });
}
function markNotifReadMobile() {
  fetch("/api/mark-reservation-notif-read", { method: "POST" }).then(() => {
    fetchReservationNotif();
    const badgeMobile = document.getElementById("notif-badge-mobile");
    if (badgeMobile) badgeMobile.style.display = "none";
  });
}

// Improved click-away logic for notification dropdowns
document.addEventListener("click", function (e) {
  // Desktop
  const notifBtn = document.getElementById("notif-bell-btn");
  const notifDropdown = document.getElementById("notif-dropdown");
  if (notifBtn && notifDropdown) {
    if (notifBtn.contains(e.target)) return;
    if (
      !notifDropdown.classList.contains("hidden") &&
      !notifDropdown.contains(e.target)
    ) {
      notifDropdown.classList.add("hidden");
    }
  }
  // Mobile
  const notifBtnMobile = document.getElementById("notif-bell-btn-mobile");
  const notifDropdownMobile = document.getElementById("notif-dropdown-mobile");
  if (notifBtnMobile && notifDropdownMobile) {
    if (notifBtnMobile.contains(e.target)) return;
    if (
      !notifDropdownMobile.classList.contains("hidden") &&
      !notifDropdownMobile.contains(e.target)
    ) {
      notifDropdownMobile.classList.add("hidden");
    }
  }

  // Admin Notification Dropdowns
  const adminNotifBtn = document.getElementById("admin-notif-bell-btn");
  const adminNotifDropdown = document.getElementById("admin-notif-dropdown");
  if (
    adminNotifBtn &&
    adminNotifDropdown &&
    !adminNotifDropdown.classList.contains("hidden")
  ) {
    if (
      !adminNotifBtn.contains(e.target) &&
      !adminNotifDropdown.contains(e.target)
    ) {
      adminNotifDropdown.classList.add("hidden");
    }
  }

  const adminNotifBtnMobile = document.getElementById(
    "admin-notif-bell-btn-mobile"
  );
  const adminNotifDropdownMobile = document.getElementById(
    "admin-notif-dropdown-mobile"
  );
  if (
    adminNotifBtnMobile &&
    adminNotifDropdownMobile &&
    !adminNotifDropdownMobile.classList.contains("hidden")
  ) {
    if (
      !adminNotifBtnMobile.contains(e.target) &&
      !adminNotifDropdownMobile.contains(e.target)
    ) {
      adminNotifDropdownMobile.classList.add("hidden");
    }
  }
});

window.addEventListener("DOMContentLoaded", fetchReservationNotif);

// --- All Notifications Modal Logic ---
function openAllNotifModal() {
  const modal = document.getElementById("allNotifModal");
  const list = document.getElementById("all-notif-list");
  modal.classList.remove("hidden");
  list.innerHTML = '<div class="text-gray-500 text-center">Loading...</div>';
  fetch("/api/all-reservation-notifications")
    .then((res) => res.json())
    .then((data) => {
      if (data.count > 0) {
        let html = "";
        data.notifications.forEach((n) => {
          html += `<div class="p-3 border-b last:border-b-0 font-switzer">
            <div class="flex items-center gap-2">
              <span class="font-bold ${
                n.status === "approved"
                  ? "text-green-600"
                  : n.status === "disapproved"
                  ? "text-red-600"
                  : "text-gray-600"
              }">${n.status.charAt(0).toUpperCase() + n.status.slice(1)}</span>
              <span class="text-xs text-gray-400">${n.date} ${n.time}</span>
            </div>
            <div class="text-xs text-gray-700">Lab: <b>${
              n.lab
            }</b> | Purpose: <b>${n.purpose}</b></div>
          </div>`;
        });
        list.innerHTML = html;
      } else {
        list.innerHTML =
          '<div class="text-gray-500 text-center">No notifications found.</div>';
      }
    })
    .catch(() => {
      list.innerHTML =
        '<div class="text-red-500 text-center">Failed to load notifications.</div>';
    });
}
function closeAllNotifModal() {
  document.getElementById("allNotifModal").classList.add("hidden");
}

// --- Admin Notification Functions ---

function fetchAdminPendingCount() {
  fetch("/api/admin/pending-reservations-count")
    .then((res) => res.json())
    .then((data) => {
      const badge = document.getElementById("admin-notif-badge");
      const badgeMobile = document.getElementById("admin-notif-badge-mobile");
      if (data.count > 0) {
        if (badge) badge.style.display = "";
        if (badgeMobile) badgeMobile.style.display = "";
      } else {
        if (badge) badge.style.display = "none";
        if (badgeMobile) badgeMobile.style.display = "none";
      }
    })
    .catch((error) =>
      console.error("Error fetching admin pending count:", error)
    );
}

function fetchAdminPendingList() {
  fetch("/api/admin/pending-reservations-list")
    .then((res) => res.json())
    .then((data) => {
      const list = document.getElementById("admin-notif-list");
      const listMobile = document.getElementById("admin-notif-list-mobile");
      let html = "";

      if (data.reservations && data.reservations.length > 0) {
        data.reservations.forEach((r) => {
          html += `<div class="p-3 font-switzer border-b last:border-b-0">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-gray-800">${r.student_name}</span>
              <span class="text-xs text-gray-400">${r.date} ${r.time}</span>
            </div>
            <div class="text-xs text-gray-600">Lab: <b>${r.lab}</b> | PC: <b>${r.pc_number}</b></div>
          </div>`;
        });
      } else {
        html =
          '<div class="p-3 text-gray-500 text-sm">No pending reservations.</div>';
      }

      if (list) list.innerHTML = html;
      if (listMobile) listMobile.innerHTML = html;
    })
    .catch((error) => {
      console.error("Error fetching admin pending list:", error);
      const errorHtml =
        '<div class="p-3 text-red-500 text-sm">Failed to load reservations.</div>';
      if (list) list.innerHTML = errorHtml;
      if (listMobile) list.innerHTML = errorHtml;
    });
}

function toggleAdminNotifDropdown() {
  const dd = document.getElementById("admin-notif-dropdown");
  if (dd) {
    dd.classList.toggle("hidden");
    if (!dd.classList.contains("hidden")) {
      fetchAdminPendingList();
    }
  }
}

function toggleAdminNotifDropdownMobile() {
  const dd = document.getElementById("admin-notif-dropdown-mobile");
  if (dd) {
    dd.classList.toggle("hidden");
    if (!dd.classList.contains("hidden")) {
      fetchAdminPendingList();
    }
  }
}
