// Timeout to hide flash messages
setTimeout(function () {
  var flashMessages = document.getElementById("flash-messages");
  if (flashMessages) {
    flashMessages.style.display = "none";
  }
}, 3000);

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

// Function to open reservation modal
function openReservationModal() {
  const modal = document.getElementById("reservationModal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

// Function to close reservation modal
function closeReservationModal() {
  const modal = document.getElementById("reservationModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}

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
