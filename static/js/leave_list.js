
let currentData = [];


document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    loadInitialData();
    attachApproveButtonListeners();
});

function initializePage() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), 0, 1);
    const lastDay = new Date(today.getFullYear(), 11, 31);

    document.getElementById('fromDate').value = firstDay.toISOString().split('T')[0];
    document.getElementById('toDate').value = lastDay.toISOString().split('T')[0];

    document.getElementById('filterForm').addEventListener('submit', function(e) {
        e.preventDefault();
        searchLeaves();
    });

    document.getElementById('statusFilter').addEventListener('change', updateStatusTag);
    updateStatusTag();

    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown-container')) {
            closeAllDropdowns();
        }
    });
}

function loadInitialData() {
    searchLeaves();
}

function updateStatusTag() {
    const statusSelect = document.getElementById('statusFilter');
    const statusTag = document.getElementById('statusTag');
    const selectedText = statusSelect.options[statusSelect.selectedIndex].text;

    statusTag.textContent = selectedText;
    statusTag.style.display = statusSelect.value ? 'inline-block' : 'none';
}

function resetFilters() {
    document.getElementById('filterForm').reset();
    initializePage();
    clearResults();
}

function clearResults() {
    document.getElementById('leaveTableBody').innerHTML = `
        <tr>
            <td colspan="9" class="no-records">
                <div class="no-records-icon">📋</div>
                <div>No leave records found.</div>
                <div style="font-size: 14px; margin-top: 8px;">Use the search filters above to find leave records.</div>
            </td>
        </tr>`;
    document.getElementById('recordCount').textContent = '(0) Records Found';
}

function searchLeaves() {
    const searchBtn = document.getElementById('searchBtn');
    const originalText = searchBtn.innerHTML;
    searchBtn.innerHTML = '<div class="loading-spinner"></div> Searching...';
    searchBtn.disabled = true;

    const formData = new FormData(document.getElementById('filterForm'));
    const params = new URLSearchParams(formData);
    const currentUrl = new URL(window.location);

    for (const [key, value] of params) {
        value ? currentUrl.searchParams.set(key, value) : currentUrl.searchParams.delete(key);
    }

    fetch(currentUrl.toString(), {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            currentData = data.leaves;
            updateTable(data.leaves);
            updateRecordCount(data.leaves.length);
            window.history.pushState({}, '', currentUrl.toString());
            attachApproveButtonListeners();
        } else {
            throw new Error(data.message || 'Search failed');
        }
    })
    .catch(error => {
        console.error('Search error:', error);
        showError('Search failed. Please try again.');
    })
    .finally(() => {
        searchBtn.innerHTML = originalText;
        searchBtn.disabled = false;
    });
}

function updateTable(leaves) {
    const tbody = document.getElementById('leaveTableBody');
    if (!leaves.length) return clearResults();

    tbody.innerHTML = leaves.map(leave => `
        <tr id="leaveRow-${leave.id}" data-leave-id="${leave.id}">
            <td class="checkbox-cell"><input type="checkbox" name="leaveRecord" value="${leave.id}"></td>
            <td>${leave.leave_date}</td>
            <td><a href="#" class="employee-link">${leave.employee_name}</a></td>
            <td>${leave.leave_type}</td>
            <td>${leave.leave_balance ?? '—'}</td>
            <td>${leave.days}</td>
            <td id="status-${leave.id}"><span class="status-badge status-${leave.status.toLowerCase()}">${leave.status}</span></td>
            <td class="comments-cell" title="${leave.reason}">${leave.reason}</td>
            <td>
                <div class="action-buttons">
                    ${getActionButtons(leave)}
                    <div class="dropdown-container">
                        <button class="btn-more" onclick="toggleDropdown(this)">⋯</button>
                        <ul class="dropdown-menu">
                            <li onclick="viewDetails('${leave.id}')">View Details</li>
                            <li onclick="editLeave('${leave.id}')">Edit Leave</li>
                            
                            <li onclick="addComment('${leave.id}')">Add Comment</li>
                           
                        </ul>
                    </div>
                </div>
            </td>
        </tr>`).join('');
}

function getActionButtons(leave) {
    switch (leave.status) {
        case 'Pending':
            return `<button class="approve-btn action-btn btn-approve" data-leave-id="${leave.id}">Approve</button><button class="action-btn btn-reject" onclick="rejectLeave(this, '${leave.id}')">Reject</button>`;
        case 'Approved': return '<span style="color: #22543d; font-weight: 600;">✓ Approved</span>';
        case 'Rejected': return '<span style="color: #742a2a; font-weight: 600;">✗ Rejected</span>';
        case 'Cancelled': return '<span style="color: #744210; font-weight: 600;">⊗ Cancelled</span>';
        default: return '';
    }
}

function updateRecordCount(count) {
    document.getElementById('recordCount').textContent = `(${count}) Records Found`;
}

function showError(message) {
    alert(message);
}

function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

function attachApproveButtonListeners() {
    document.querySelectorAll('.approve-btn').forEach(button => {
        button.removeEventListener('click', handleApproveClick);
        button.addEventListener('click', handleApproveClick);
    });
}

function handleApproveClick(event) {
    const button = event.target;
    const leaveId = button.getAttribute('data-leave-id');
    if (confirm('Approve this leave?')) {
        approveLeave(leaveId, button);
    }
}

function approveLeave(leaveId, button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<div class="loading-spinner"></div> Approving...';
    button.disabled = true;

    fetch(`/hrms_app/approve-leave/${leaveId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ action: 'approve', leave_id: leaveId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateLeaveStatus(leaveId, 'Approved');
            showNotification('Leave approved!', 'success');
        } else throw new Error(data.message);
    })
    .catch(err => {
        console.error('Approve error:', err);
        showNotification('Approval failed!', 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

function updateLeaveStatus(id, status) {
    const row = document.querySelector(`#leaveRow-${id}`);
    if (!row) return;

    row.querySelector(`#status-${id}`).innerHTML = `<span class="status-badge status-${status.toLowerCase()}">${status}</span>`;
    const buttons = row.querySelectorAll('.action-btn');
    buttons.forEach(btn => btn.remove());

    const display = document.createElement('span');
    display.style.fontWeight = '600';
    display.textContent = status === 'Approved' ? '✓ Approved' : status;
    row.querySelector('.action-buttons').prepend(display);
}

function toggleDropdown(btn) {
    const menu = btn.nextElementSibling;
    closeAllDropdowns();
    menu.style.display = 'block';
}

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-menu').forEach(menu => menu.style.display = 'none');
}


function viewDetails(leaveId) {
    closeAllDropdowns();
    
   
    const modal = document.getElementById('leaveDetailsModal');
    const content = document.getElementById('leaveDetailsContent');
    
    content.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>Loading leave details...</p>
        </div>
    `;
    
    modal.style.display = 'block';
    
    
    fetch(`/hrms_app/detail/${leaveId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const leave = data.leave;
            content.innerHTML = `
               <div class="leave-detail-card">
    <div class="detail-header">
        <h3>Leave Application Details</h3>
        <span class="status-badge status-${leave.status.toLowerCase()}">${leave.status}</span>
    </div>

   <div class="detail-row">
        <label>Employee Name</label>
        <div>${leave.employee}</div>
    </div>

         <div class="detail-row">
        <label>Leave Date</label>
        <div>${formatDate(leave.date)}</div>
    </div>

       <div class="detail-row">
        <label>Leave Type</label>
        <div>${leave.leave_type}</div>
    </div>
     <div class="detail-row">
        <label>Duration</label>
        <div>${leave.Duration || 'N/A'} day(s)</div>
    </div>
      <div class="detail-row">
        <label>Remaining Balance</label>
        <div>${leave.leave_balance || '—'} day(s)</div>
    </div>
    

     ${leave.comments ? `
    <div class="detail-row">
        <label>Comments / Reason</label>
        <div>${leave.comments}</div>
    </div>` : ''}

        

        
      <div class="modal-actions">
       
        <button class="btn btn-secondary" onclick="closeModal()">Close</button>
    </div>
</div>

            `;
        } else {
            content.innerHTML = `
                <div class="error-message">
                    <p>Error loading leave details: ${data.message || 'Unknown error'}</p>
                    <button class="btn btn-secondary" onclick="closeModal()">Close</button>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching leave details:', error);
        content.innerHTML = `
            <div class="error-message">
                <p>Failed to load leave details. Please try again.</p>
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            </div>
        `;
    });
}


function closeModal() {
    document.getElementById('leaveDetailsModal').style.display = 'none';
}


function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}


window.onclick = function(event) {
    const modal = document.getElementById('leaveDetailsModal');
    if (event.target === modal) {
        closeModal();
    }
}


document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

function editLeave(id) { closeAllDropdowns(); window.location.href = `/hrms_app/edit-leave/${id}/`; }
// function cancelLeave(id) { closeAllDropdowns(); if (confirm('Cancel leave?')) fetch(`/hrms_app/cancel-leave/${id}/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken(), 'X-Requested-With': 'XMLHttpRequest' }, body: JSON.stringify({ action: 'cancel', leave_id: id }) }).then(r => r.json()).then(d => d.success && updateLeaveStatus(id, 'Cancelled')); }
function addComment(id) { 
    closeAllDropdowns(); 
    const comment = prompt('Add admin comment:'); 
    if (comment && comment.trim()) {
        fetch(`/hrms_app/add-leave-comment/${id}/`, { 
            method: 'POST', 
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': getCSRFToken(), 
                'X-Requested-With': 'XMLHttpRequest' 
            }, 
            body: JSON.stringify({ comment: comment.trim(), leave_id: id }) 
        })
        .then(r => r.json())
        .then(d => {
            if(d.success) {
                showNotification('Admin comment added successfully!', 'success');
               
                searchLeaves();
            } else {
                showNotification(d.message || 'Failed to add admin comment!', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding comment:', error);
            showNotification('Error adding admin comment!', 'error');
        });
    }
}
// function printLeave(id) { closeAllDropdowns(); window.open(`/hrms_app/print-leave/${id}/`, '_blank'); }

function showNotification(msg, type='info') {
    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.style.cssText = 'position:fixed;top:20px;right:20px;padding:16px 24px;border-radius:12px;color:white;font-weight:600;z-index:10000;box-shadow:0 8px 32px rgba(0,0,0,0.2);cursor:pointer;';
    n.style.background = type === 'success' ? '#68d391' : type === 'error' ? '#fc8181' : '#667eea';
    n.textContent = msg;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 5000);
    n.onclick = () => n.remove();
}

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') searchLeaves();
    if (e.key === 'Escape') closeAllDropdowns();
});

window.addEventListener('popstate', function() {
    const params = new URLSearchParams(window.location.search);
    params.forEach((val, key) => {
        const el = document.querySelector(`[name="${key}"]`);
        if (el) el.value = val;
    });
    updateStatusTag();
    searchLeaves();
});

function attachRejectButtonListeners() {
    document.querySelectorAll('.btn-reject').forEach(button => {
        button.removeEventListener('click', handleRejectClick);
        button.addEventListener('click', handleRejectClick);
    });
}

function handleRejectClick(event) {
    const button = event.target;
    const leaveId = button.getAttribute('data-leave-id');
    const reason = prompt('Enter rejection reason (optional):');
    if (confirm('Reject this leave?')) {
        rejectLeave(button, leaveId, reason);
    }
}

function rejectLeave(button, leaveId, reason = '') {
    const originalText = button.innerHTML;
    button.innerHTML = '<div class="loading-spinner"></div> Rejecting...';
    button.disabled = true;

    fetch(`/hrms_app/reject-leave/${leaveId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ reason, leave_id: leaveId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateLeaveStatus(leaveId, 'Rejected');
            showNotification('Leave rejected!', 'success');
        } else throw new Error(data.message);
    })
    .catch(err => {
        console.error('Reject error:', err);
        showNotification('Rejection failed!', 'error');
        button.innerHTML = originalText;
        button.disabled = false;
    });
   
} 
function editLeave(id) {
    closeAllDropdowns();

    const modal = document.getElementById('leaveDetailsModal');
    const content = document.getElementById('leaveDetailsContent');

    content.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>Loading leave for editing...</p>
        </div>
    `;

    modal.style.display = 'block';

    fetch(`/hrms_app/edit-leave/${id}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const leave = data.leave;
            content.innerHTML = `
                <div class="leave-edit-form">
                    <div class="detail-header">
                        <h3>Edit Leave Request</h3>
                        <button class="close-btn" onclick="closeModal()">&times;</button>
                    </div>

                    <!-- Non-editable Employee Name -->
                    <div class="form-row">
                        <label>Employee Name</label>
                        <div class="readonly-field">${leave.employee_name || leave.employee}</div>
                    </div>

                    <!-- Editable Leave Type -->
                    <div class="form-row">
                        <label>Leave Type <span class="required">*</span></label>
                        <select id="editLeaveType" required>
                            <option value="">Select Leave Type</option>
                            ${data.leave_types.map(type =>
                                `<option value="${type.id}" ${leave.leave_type_id == type.id || leave.leave_type === type.name ? 'selected' : ''}>${type.name}</option>`).join('')}
                        </select>
                    </div>

                    <!-- Editable Leave Date -->
                    <div class="form-row">
                        <label>Leave Date <span class="required">*</span></label>
                        <input type="date" id="editLeaveDate" value="${leave.date || leave.leave_date}" required>
                    </div>

                    <!-- Editable Duration -->
                    <div class="form-row">
                        <label>Duration <span class="required">*</span></label>
                        <select id="editDuration" required>
                            ${data.duration_choices.map(choice =>
                                `<option value="${choice.value}" ${leave.duration === choice.value ? 'selected' : ''}>${choice.label}</option>`).join('')}
                        </select>
                    </div>

                    <!-- Editable Reason -->
                    <div class="form-row">
                        <label>Reason <span class="required">*</span></label>
                        <textarea id="editLeaveReason" required placeholder="Enter reason for leave">${leave.reason || leave.comments || ''}</textarea>
                    </div>

                    <!-- Editable Status -->
                    <div class="form-row">
                        <label>Status</label>
                        <select id="editStatus">
                            ${data.status_choices.map(choice =>
                                `<option value="${choice.value}" ${leave.status === choice.value ? 'selected' : ''}>${choice.label}</option>`).join('')}
                        </select>
                    </div>

                       <div class="modal-actions">
                        <button class="btn btn-primary" onclick="saveEditedLeave('${id}')">Save</button>
                        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    </div>
                </div>
            `;
        } else {
            content.innerHTML = `<p>Error: ${data.message}</p>`;
        }
    })
    .catch(error => {
        content.innerHTML = `<p>Failed to load leave data.</p>`;
        console.error('Edit fetch error:', error);
    });
}
function saveEditedLeave(leaveId) {
   
    const leaveTypeId = document.getElementById('editLeaveType').value;
    const leaveDate = document.getElementById('editLeaveDate').value;
    const duration = document.getElementById('editDuration').value;
    const reason = document.getElementById('editLeaveReason').value;
    const status = document.getElementById('editStatus').value;

   
    if (!leaveTypeId || !leaveDate || !duration || !reason) {
        showNotification('Please fill in all required fields!', 'error');
        return;
    }

    
    const saveBtn = document.querySelector('.btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<div class="loading-spinner"></div> Saving...';
    saveBtn.disabled = true;

    const updatedData = {
        leave_type_id: leaveTypeId,
        date: leaveDate,
        duration: duration,
        reason: reason,
        status: status
    };

    fetch(`/hrms_app/edit-leave/${leaveId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification('Leave updated successfully!', 'success');
            closeModal();
            searchLeaves(); 
        } else {
            showNotification('Update failed: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Save error:', error);
        showNotification('Something went wrong while saving.', 'error');
    })
    .finally(() => {
       
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    });
}
