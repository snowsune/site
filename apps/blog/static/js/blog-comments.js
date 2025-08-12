/**
 * Blog Comments JavaScript
 * Handles comment forms, replies, and cookie management
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize comment functionality
    initCommentSystem();
});

function initCommentSystem() {
    // Set up reply buttons
    setupReplyButtons();

    // Set up cookie saving for comment forms
    setupCommentCookies();

    // Set up form submission feedback
    setupFormFeedback();
}

function setupReplyButtons() {
    // Use event delegation for better performance
    document.addEventListener('click', function (e) {
        if (e.target.matches('.reply-btn')) {
            handleReplyClick(e.target);
        } else if (e.target.matches('.cancel-reply')) {
            handleCancelReply(e.target);
        }
    });
}

function handleReplyClick(button) {
    const commentId = button.getAttribute('data-comment-id');
    const replyForm = document.getElementById(`reply-form-${commentId}`);

    if (!replyForm) {
        console.error(`Reply form not found for comment ${commentId}`);
        return;
    }

    // Hide all other reply forms first
    document.querySelectorAll('[data-reply-form]').forEach(form => {
        form.style.display = 'none';
    });

    // Show this reply form
    replyForm.style.display = 'block';

    // Auto-fill fields for anonymous users from cookies
    if (!document.body.classList.contains('user-authenticated')) {
        autoFillReplyForm(replyForm);
    }

    // Scroll to the reply form
    replyForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function handleCancelReply(button) {
    const commentId = button.getAttribute('data-comment-id');
    const replyForm = document.getElementById(`reply-form-${commentId}`);

    if (replyForm) {
        replyForm.style.display = 'none';
    }
}

function autoFillReplyForm(replyForm) {
    const nameField = replyForm.querySelector('input[name="author_name"]');
    const emailField = replyForm.querySelector('input[name="author_email"]');

    if (nameField) {
        nameField.value = getCookie('commorg_name') || '';
    }
    if (emailField) {
        emailField.value = getCookie('commorg_email') || '';
    }
}

function setupCommentCookies() {
    document.addEventListener('submit', function (e) {
        if (e.target && e.target.classList.contains('comment-form')) {
            // Only save cookies for anonymous users
            if (!document.body.classList.contains('user-authenticated')) {
                saveCommentCookies(e.target);
            }
        }
    });
}

function saveCommentCookies(form) {
    const nameField = form.querySelector('input[name="author_name"]');
    const emailField = form.querySelector('input[name="author_email"]');
    const websiteField = form.querySelector('input[name="author_website"]');

    if (nameField && nameField.value.trim()) {
        setCookie('commorg_name', nameField.value.trim());
    }
    if (emailField && emailField.value.trim()) {
        setCookie('commorg_email', emailField.value.trim());
    }
    if (websiteField && websiteField.value.trim()) {
        setCookie('commorg_website', websiteField.value.trim());
    }
}

function setupFormFeedback() {
    document.addEventListener('submit', function (e) {
        if (e.target && e.target.classList.contains('comment-form')) {
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            submitBtn.classList.add('btn-loading');

            // Add visual feedback to the form
            e.target.classList.add('form-submitting');

            // Re-enable button after a delay (in case of errors)
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                submitBtn.classList.remove('btn-loading');
                e.target.classList.remove('form-submitting');
            }, 10000); // 10 second timeout
        }
    });
}

function setCookie(name, value) {
    try {
        document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=31536000`;
    } catch (error) {
        console.warn(`Failed to set cookie ${name}:`, error);
    }
}

function getCookie(name) {
    try {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    } catch (error) {
        console.warn(`Failed to get cookie ${name}:`, error);
        return '';
    }
} 