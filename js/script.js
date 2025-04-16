function saveUsername() {
    const username = document.getElementById("username").value.trim();
  
    if (!username) {
      alert("Please enter a username.");
      return;
    }
  
    localStorage.setItem("user_id", username);
    // alert(`Welcome, ${username}!`);
    window.location.href = "landing.html"; // Redirect to landing page
    // Redirect to next page if needed:
    // window.location.href = "home.html";
  }
  document.addEventListener("DOMContentLoaded", () => {
    const switcher = document.getElementById("themeSwitcher");
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
      document.body.classList.add("dark-mode");
      switcher.checked = true;
    } else {
      document.body.classList.add("light-mode");
      switcher.checked = false;
    }

    switcher.addEventListener("change", () => {
      if (switcher.checked) {
        document.body.classList.remove("light-mode");
        document.body.classList.add("dark-mode");
        localStorage.setItem("theme", "dark");
      } else {
        document.body.classList.remove("dark-mode");
        document.body.classList.add("light-mode");
        localStorage.setItem("theme", "light");
      }
    });
  });