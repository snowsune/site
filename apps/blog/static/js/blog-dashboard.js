// Comment moderation buttons on the blog dashboard

document.addEventListener('DOMContentLoaded', function () {
    const pendingComments = document.querySelectorAll('[data-moderation-type="pending"] .comment-row');
    if (pendingComments.length > 0) {
        toast(`${pendingComments.length} comment(s) to check`, "info");
    }

    document.addEventListener('click', function (e) {
        if (e.target.matches('.moderation-action')) {
            e.preventDefault();
            handleModerationAction(e.target);
        }
    });
});

function resetButton(button, text) {
    button.disabled = false;
    button.textContent = text;
    button.classList.remove('btn-loading');
}

function handleModerationAction(button) {
    const action = button.getAttribute('data-action');
    const commentId = button.getAttribute('data-comment-id');

    if (!action || !commentId) {
        console.error('Missing action or comment ID');
        return;
    }

    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Processing...';
    button.classList.add('btn-loading');

    toast(`Processing ${action} action...`, "info");

    fetch(`/blog/comment/${commentId}/${action}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            toast(data.message || 'Action failed', "error");
            resetButton(button, originalText);
            return;
        }

        toast(data.message, "success");

        const commentRow = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (commentRow) {
            commentRow.classList.add('removing');
            setTimeout(() => {
                commentRow.remove();
                updateCommentCounts();
            }, 300);
        }

        const totalStat = document.querySelector('.stat-card .stat-number');
        if (totalStat) {
            totalStat.textContent = document.querySelectorAll('.comment-row').length;
        }
    })
    .catch(error => {
        console.error('Moderation action error:', error);
        toast('Network error. Please try again.', "error");
        resetButton(button, originalText);
    });
}

function updateCommentCounts() {
    const pendingStat = document.querySelector('.stat-card-warning .stat-number');
    if (pendingStat) {
        pendingStat.textContent = document.querySelectorAll('.comment-row.pending').length;
    }

    // Hide any section that just got emptied out
    for (const type of ['pending', 'rejected', 'spam']) {
        const section = document.querySelector(`[data-moderation-type="${type}"]`);
        if (section && document.querySelectorAll(`.comment-row.${type}`).length === 0) {
            section.style.display = 'none';
        }
    }
}
