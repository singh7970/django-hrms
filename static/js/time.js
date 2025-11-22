document.addEventListener('DOMContentLoaded', function () {
    const formIn = document.getElementById('punch-in-form');
    const formOut = document.getElementById('punch-out-form');
    const formInSubmit = document.getElementById('form-punch-in');  
    const formOutSubmit = document.getElementById('form-punch-out');  
    const statusText = document.getElementById('status-text');
    const status = statusText?.textContent?.trim().toUpperCase() || '';
    
    // Check for weekend restriction
    function isWeekend() {
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0 = Sunday, 6 = Saturday
        return dayOfWeek === 0 || dayOfWeek === 6;
    }
    
    // Function to check if today is holiday (from backend data)
    function isHoliday() {
        // This will be populated from the template context
        return window.holidayRestriction || false;
    }
    
    if (document.getElementById('status-text')?.dataset?.blocked === 'true') {
        if (formIn) formIn.classList.add('d-none');
        if (formOut) formOut.classList.add('d-none');
        alert("You have been punched in for over 40 hours. Please contact HR.");
    }
    if (status === "PUNCHED_IN") {
        formIn.classList.add('d-none');
        formOut.classList.remove('d-none');
    } else {
        formOut.classList.add('d-none');
        formIn.classList.remove('d-none');
    }
  
    function setCurrentDateTime(idPrefix) {
        const now = new Date();
        const date = now.toISOString().split('T')[0];
        const time = now.toTimeString().split(' ')[0];

        const dateInput = document.getElementById(`${idPrefix}-date`);
        const timeInput = document.getElementById(`${idPrefix}-time`);

        if (dateInput && timeInput) {
            dateInput.value = date;
            timeInput.value = time;
        }
    }

    setCurrentDateTime('punch-in');
    setCurrentDateTime('punch-out');
    setInterval(() => {
        setCurrentDateTime('punch-in');
        setCurrentDateTime('punch-out');
    }, 1000);

    function ajaxSubmitForm(form, callback) {
        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => callback(data))
        .catch(err => {
            console.error(err);
            showMessage("Request failed. Try again.", false, form.id === 'form-punch-in' ? 'in' : 'out');
        });
    }

    function showMessage(message, isSuccess = true, target = "in") {
        const box = document.getElementById(target === "in" ? "message-box-in" : "message-box-out");
        if (!box) return;

        box.textContent = message;
        box.classList.remove("d-none");
        box.style.backgroundColor = isSuccess ? "#d4edda" : "#f8d7da";
        box.style.color = isSuccess ? "#155724" : "#721c24";
        box.style.border = isSuccess ? "1px solid #c3e6cb" : "1px solid #f5c6cb";

        setTimeout(() => {
            box.classList.add("d-none");
            box.textContent = "";
        }, 2000);
    }

    if (formInSubmit) {
        formInSubmit.addEventListener('submit', function (e) {
            e.preventDefault();
            
            // Check if today is weekend
            if (isWeekend()) {
                const dayName = new Date().getDay() === 0 ? 'Sunday' : 'Saturday';
                showMessage(`Punch in is not allowed on ${dayName}.`, false, "in");
                return;
            }
            
            // Check if today is holiday
            if (isHoliday()) {
                showMessage(window.holidayMessage || 'Punch in is not allowed on holidays.', false, "in");
                return;
            }
            
            console.log("Intercepted Punch In form");
            ajaxSubmitForm(formInSubmit, function (response) {
                if (response.success) {
                    formIn.classList.add('d-none');
                    formOut.classList.remove('d-none');
                    setCurrentDateTime('punch-out');
                    if (statusText) statusText.textContent = 'PUNCHED_IN';
                }
                showMessage(response.message || 'Punch in successful.', response.success, "out");
            });
        });
    }

    if (formOutSubmit) {
        formOutSubmit.addEventListener('submit', function (e) {
            e.preventDefault();
            
            // Check if today is weekend
            if (isWeekend()) {
                const dayName = new Date().getDay() === 0 ? 'Sunday' : 'Saturday';
                showMessage(`Punch out is not allowed on ${dayName}.`, false, "out");
                return;
            }
            
            // Check if today is holiday
            if (isHoliday()) {
                showMessage(window.holidayMessage || 'Punch out is not allowed on holidays.', false, "out");
                return;
            }
            
            console.log("Intercepted Punch Out form");
            ajaxSubmitForm(formOutSubmit, function (response) {
                if (response.success) {
                    formOut.classList.add('d-none');
                    formIn.classList.remove('d-none');
                    setCurrentDateTime('punch-in');
                    if (statusText) statusText.textContent = 'PUNCHED_OUT';
                    
                    // Show detailed work summary
                    let detailedMessage = response.message;
                    if (response.duration && response.work_type) {
                        detailedMessage += `\n\n📊 Work Summary:\n` +
                                         `⏱️ Duration: ${response.duration}\n` +
                                         `📅 Type: ${response.work_type}\n` +
                                         `🕐 Time: ${response.punch_in} - ${response.punch_out}\n` +
                                         `⏰ Total Hours: ${response.total_hours}h`;
                    }
                    showMessage(detailedMessage, response.success, "in");
                } else {
                    showMessage(response.message || 'Punch out failed.', response.success, "in");
                }
            });
        });
    }
});
