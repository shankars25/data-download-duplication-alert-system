// ------------------------------
// Tab Switching
// ------------------------------
// ------------------------------
// Tab Switching
// ------------------------------
const tabLinks = document.querySelectorAll(".tab-link");
const tabPanes = document.querySelectorAll(".tab-pane");

tabLinks.forEach(link => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        const targetTab = e.target.getAttribute("data-tab");
        tabLinks.forEach(link => link.classList.remove("active"));
        tabPanes.forEach(pane => pane.classList.remove("active"));
        e.target.classList.add("active");
        document.getElementById(targetTab).classList.add("active");
    });
});

if (tabLinks.length > 0 && tabPanes.length > 0) {
    tabLinks[0].classList.add("active");
    tabPanes[0].classList.add("active");
}

// ------------------------------
// DOM Content Loaded
// ------------------------------
document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const logoutBtn = document.getElementById("logoutBtn");
    const errorMessage = document.getElementById("error-message");

    // ------------------------------
    // Handle Login
    // ------------------------------
    if (loginForm) {
        loginForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const data = { email, password };

            try {
                const response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });

                const result = await response.json();

                if (response.ok && result.message === "Login successful") {
                    window.location.href = "/index";
                } else {
                    errorMessage.textContent = result.error || "Invalid credentials";
                }
            } catch (error) {
                console.error("Login Error:", error);
                errorMessage.textContent = "An unexpected error occurred during login.";
            }
        });
    }
    
    // ------------------------------
    // Handle Registration
    // ------------------------------
    if (registerForm) {
        registerForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            const response = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const result = await response.json();
            if (document.getElementById("registerResponse")) {
                document.getElementById("registerResponse").innerText = result.message || result.error;
            }

            if (response.ok && result.message === "Registration successful") {
                window.location.href = "/login";
            }
        });
    }

    // ------------------------------
    // Handle Logout
    // ------------------------------
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async function () {
            const response = await fetch("/logout", { method: "POST" });
            if (response.ok) {
                window.location.href = "/login";
            }
        });
    }
});

// ------------------------------
// File Upload Form Event Listener
// ------------------------------
const uploadForm = document.getElementById("uploadForm");
if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);

        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        const result = await response.json();
        document.getElementById("uploadResponse").textContent = JSON.stringify(result, null, 2);

        alert(result.message || "File uploaded successfully!");
    });
}

// Download by Name Form
document.getElementById("downloadNameForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileName = document.getElementById("fileName").value;
    const userId = document.getElementById("userIdName").value;

    if (!fileName || !userId) {
        alert("Please provide both the file name and your user ID.");
        return;
    }

    try {
        const response = await fetch("/download_by_name", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ file_name: fileName, user_id: userId }),
        });

        if (response.status === 200) {
            const contentDisposition = response.headers.get("Content-Disposition");

            if (contentDisposition && contentDisposition.includes("attachment")) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = fileName;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                alert("File downloaded successfully!");
            } else {
                const result = await response.json();
                document.getElementById("downloadNameResponse").textContent = JSON.stringify(result, null, 2);
            }
        } else {
            const result = await response.json();
            alert(result.error || "An error occurred while downloading the file.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while processing your request.");
    }
});

// Handle downloading from URL
document.getElementById("downloadUrlForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileUrl = document.getElementById("fileUrl").value;
    const userId = document.getElementById("userIdUrl").value;

    if (!fileUrl || !userId) {
        alert("Please provide both the file URL and your user ID.");
        return;
    }

    try {
        const response = await fetch("/download_from_url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ file_url: fileUrl, user_id: userId }),
        });

        const result = await response.json();

        // Exclude the "users" field from the alert
        const { users, ...filteredResult } = result;

        // Display the filtered result (excluding 'users')
        document.getElementById("downloadUrlResponse").textContent = JSON.stringify(filteredResult, null, 2);
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred while processing your request.");
    }
});


// ------------------------------
// Get Files from the Server
// ------------------------------
const getFilesButton = document.getElementById("getFilesButton");

if (getFilesButton) {
    getFilesButton.addEventListener("click", async () => {
        try {
            const response = await fetch("/get_files", { method: "GET" });
            const result = await response.json();
            const databaseContentDiv = document.getElementById("databaseContent");
            databaseContentDiv.innerHTML = '';

            if (result.files && result.files.length > 0) {
                databaseContentDiv.innerHTML = result.files.map(file =>
                    `<div><strong>${file.file_name}</strong><br>Path: ${file.file_path}<br>Uploaded by: ${file.uploaded_by}<br><hr></div>`
                ).join('');
            } else {
                databaseContentDiv.innerHTML = '<p>No files found in the database.</p>';
            }

            // 🔹 Scroll to top after loading content
            window.scrollTo({ top: 0, behavior: 'smooth' });

        } catch (error) {
            console.error("Error fetching files:", error);
            alert("An error occurred while fetching the files.");
        }
    });
}
