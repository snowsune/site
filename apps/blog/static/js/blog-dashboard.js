// Comment moderation buttons on the blog dashboard

document.addEventListener('DOMContentLoaded', function () {
    const pendingComments = document.querySelectorAll('[data-moderation-type="pending"] .comment-row');
    if (pendingComments.length > 0 && window.notifications) {
        window.notifications.info(
            `${pendingComments.length} comment(s) to check`,
            8000
        );
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

    if (window.notifications) {
        window.notifications.info(`Processing ${action} action...`, 3000);
    }

    fetch(`/blog/comment/${commentId}/${action}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            if (window.notifications) {
                window.notifications.error(data.message || 'Action failed', 10000);
            }
            resetButton(button, originalText);
            return;
        }

        if (window.notifications) {
            window.notifications.success(data.message, 5000);
        }

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
        if (window.notifications) {
            window.notifications.error('Network error. Please try again.', 10000);
        }
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
