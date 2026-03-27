// -------- PAGE LOADED --------
document.addEventListener("DOMContentLoaded", () => {
    console.log("App Loaded 🚀");
});


// -------- SIMPLE SUCCESS ALERT --------
// Shows alert after form submission (basic feedback)
const forms = document.querySelectorAll("form");

forms.forEach(form => {
    form.addEventListener("submit", () => {
        alert("✅ Submitted successfully!");
    });
});


// -------- CONFIRM BEFORE CREATING TIMETABLE --------
const timetableForm = document.querySelector('form[action="/create-timetable"]');

if (timetableForm) {
    timetableForm.addEventListener("submit", (e) => {
        const confirmAction = confirm("Are you sure you want to create this timetable entry?");
        if (!confirmAction) {
            e.preventDefault();
        }
    });
}


// -------- AUTO HIDE ALERT (if you add one later) --------
setTimeout(() => {
    const alertBox = document.getElementById("alert");
    if (alertBox) {
        alertBox.style.display = "none";
    }
}, 3000);


// -------- BASIC FORM VALIDATION --------
function validateForm(form) {
    const inputs = form.querySelectorAll("input[required], select[required]");

    for (let input of inputs) {
        if (!input.value) {
            alert("⚠️ Please fill all required fields!");
            return false;
        }
    }
    return true;
}


// Apply validation to all forms
forms.forEach(form => {
    form.addEventListener("submit", (e) => {
        if (!validateForm(form)) {
            e.preventDefault();
        }
    });
});


// -------- DARK MODE TOGGLE (OPTIONAL COOL FEATURE) --------
function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
}


// -------- HIGHLIGHT TABLE ROW ON HOVER --------
const rows = document.querySelectorAll("table tr");

rows.forEach(row => {
    row.addEventListener("mouseover", () => {
        row.style.backgroundColor = "#e0f2fe";
    });

    row.addEventListener("mouseout", () => {
        row.style.backgroundColor = "";
    });
});