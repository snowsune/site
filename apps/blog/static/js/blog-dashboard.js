/**
 * Blog Dashboard JavaScript
 * Handles dashboard interactions and functionality
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize dashboard functionality
    initDashboard();
});

function initDashboard() {
    // Show welcome notification if there are pending comments
    const pendingComments = document.querySelectorAll('[data-moderation-type="pending"] .comment-row');
    if (pendingComments.length > 0 && window.notifications) {
        window.notifications.info(
            `You have ${pendingComments.length} comment(s) awaiting moderation`,
            8000
        );
    }

    // Add any dashboard-specific functionality here
    // For now, this is a placeholder for future enhancements

    // Example: Could add comment moderation shortcuts, bulk actions, etc.
    console.log('Blog dashboard initialized');
} 