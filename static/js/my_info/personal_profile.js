    document.addEventListener("DOMContentLoaded", function () {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll(".nav-link");

        navLinks.forEach(link => {
            const linkPath = link.getAttribute("href");
            if (linkPath === currentPath) {
                link.classList.add("active", "text-primary");
                link.classList.remove("text-dark");
            } else {
                link.classList.remove("active", "text-primary");
                link.classList.add("text-dark");
            }
        });
    });
