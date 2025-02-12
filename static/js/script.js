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

