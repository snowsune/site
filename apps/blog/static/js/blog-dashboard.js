/**
 * Blog Dashboard JavaScript
 * Handles dashboard interactions and functionality
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize dashboard functionality
    initDashboard();
});

function initDashboard() {
    setupModerationActions();
}

function setupModerationActions() {
    // Use event delegation for moderation buttons
    document.addEventListener('click', function(e) {
        if (e.target.matches('.moderation-action')) {
            e.preventDefault();
            handleModerationAction(e.target);
        }
    });
}

function handleModerationAction(button) {
    const action = button.getAttribute('data-action');
    const commentId = button.getAttribute('data-comment-id');
    
    if (!action || !commentId) {
        console.error('Missing action or comment ID');
        return;
    }
    
    // Disable button and show loading state
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Processing...';
    button.classList.add('btn-loading');
    
    // Make AJAX request
    fetch(`/blog/comment/${commentId}/${action}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const commentRow = document.querySelector(`[data-comment-id="${commentId}"]`);
            if (commentRow) {
                commentRow.remove();
                updateCommentCounts();
            }
            refreshDashboardData();
        } else {
            button.disabled = false;
            button.textContent = originalText;
            button.classList.remove('btn-loading');
        }
    })
    .catch(error => {
        console.error('Moderation action error:', error);
        button.disabled = false;
        button.textContent = originalText;
        button.classList.remove('btn-loading');
    });
}

function updateCommentCounts() {
    // Update pending comments count
    const pendingRows = document.querySelectorAll('.comment-row.pending');
    const pendingCount = pendingRows.length;
    
    // Update rejected comments count
    const rejectedRows = document.querySelectorAll('.comment-row.rejected');
    const rejectedCount = rejectedRows.length;
    
    // Update spam comments count
    const spamRows = document.querySelectorAll('.comment-row.spam');
    const spamCount = spamRows.length;
    
    // Update dashboard stats if they exist
    const pendingStat = document.querySelector('.stat-card-warning .stat-number');
    if (pendingStat) {
        pendingStat.textContent = pendingCount;
    }
    
    // Hide sections if they're empty
    const pendingSection = document.querySelector('[data-moderation-type="pending"]');
    const rejectedSection = document.querySelector('[data-moderation-type="rejected"]');
    const spamSection = document.querySelector('[data-moderation-type="spam"]');
    
    if (pendingCount === 0 && pendingSection) {
        pendingSection.style.display = 'none';
    }
    
    if (rejectedCount === 0 && rejectedSection) {
        rejectedSection.style.display = 'none';
    }
    
    if (spamCount === 0 && spamSection) {
        spamSection.style.display = 'none';
    }
}

function refreshDashboardData() {
    // Optionally refresh the entire dashboard data
    // For now, we'll just update the counts
    // In the future, this could make an AJAX call to get fresh data
    
    // Update total comment count
    const totalComments = document.querySelectorAll('.comment-row').length;
    const totalStat = document.querySelector('.stat-card .stat-number');
    if (totalStat) {
        totalStat.textContent = totalComments;
    }
} 