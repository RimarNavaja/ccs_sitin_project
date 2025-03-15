// Timeout to hide flash messages
setTimeout(function () {
  var flashMessages = document.getElementById("flash-messages");
  if (flashMessages) {
    flashMessages.style.display = "none";
  }
}, 3000);

//toggle dropdown desktop
function toggleDropdown() {
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
    if (!dropdown.classList.contains("hidden")) {
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


// Toggle dropdown function for labrules.html
function toggleDropdown(contentId) {
  const content = document.getElementById(contentId);
  const button = content.previousElementSibling;
  const icon = button.querySelector("svg");

  // Toggle the content visibility with transitions
  content.classList.toggle("open");

  // Rotate the arrow icon
  if (!content.classList.contains("open")) {
    icon.classList.remove("rotate-180");
  } else {
    icon.classList.add("rotate-180");
  }
}

// Function to toggle active class for navigation links
// function toggleActiveLink(event) {
//   const links = document.querySelectorAll("nav a");
//   links.forEach((link) => {
//     link.classList.remove("bg-violet-800", "text-white");
//     link.classList.add(
//       "text-gray-300",
//       "hover:bg-gray-700",
//       "hover:text-white"
//     );
//     link.removeAttribute("aria-current");
//   });
//   event.currentTarget.classList.add("bg-violet-800", "text-white");
//   event.currentTarget.classList.remove(
//     "text-gray-300",
//     "hover:bg-gray-700",
//     "hover:text-white"
//   );
//   event.currentTarget.setAttribute("aria-current", "page");
// }

// // Attach event listeners to navigation links after DOM is fully loaded
// document.addEventListener("DOMContentLoaded", function () {
//   document.querySelectorAll("nav a").forEach((link) => {
//     link.addEventListener("click", toggleActiveLink);
//   });
// });
