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
            e.preventDefault(); // Prevent default form submission

            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            submitBtn.classList.add('btn-loading');

            // Add visual feedback to the form
            form.classList.add('form-submitting');

            // Show immediate feedback notification
            if (window.notifications) {
                if (document.body.classList.contains('user-authenticated')) {
                    window.notifications.info('Submitting your comment...', 3000);
                } else {
                    window.notifications.info('Submitting comment for moderation...', 3000);
                }
            }

            // Submit form via AJAX
            submitFormAjax(form, submitBtn, originalText);
        }
    });

    // Set up error state removal on input
    setupErrorStateRemoval();
}

function setupErrorStateRemoval() {
    document.addEventListener('input', function (e) {
        if (e.target.classList.contains('form-control') && e.target.classList.contains('error')) {
            // Remove error state
            e.target.classList.remove('error');

            // Remove error message if it exists
            const errorMessage = e.target.parentNode.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
    });

    document.addEventListener('focus', function (e) {
        if (e.target.classList.contains('form-control') && e.target.classList.contains('error')) {
            // Remove error state on focus
            e.target.classList.remove('error');

            // Remove error message if it exists
            const errorMessage = e.target.parentNode.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
    });
}

function submitFormAjax(form, submitBtn, originalText) {
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
        .then(response => response.json())
        .then(data => {
            // Reset form state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            submitBtn.classList.remove('btn-loading');
            form.classList.remove('form-submitting');

            if (data.success) {
                // Show success notification
                if (window.notifications) {
                    if (data.user_authenticated) {
                        window.notifications.success(data.message, 5000);
                    } else {
                        window.notifications.info(data.message, 8000);
                    }
                }

                // Clear form
                form.reset();

                // Reload page after a short delay to show the new comment
                setTimeout(() => {
                    window.location.reload();
                }, 1500);

            } else {
                // Show error notification
                if (window.notifications) {
                    window.notifications.error(data.message || 'An error occurred', 10000);
                }

                // Show field errors if any
                if (data.errors) {
                    Object.keys(data.errors).forEach(field => {
                        const fieldElement = form.querySelector(`[name="${field}"]`);
                        if (fieldElement) {
                            fieldElement.classList.add('error');
                            // Add error message below field
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'error-message';
                            errorDiv.textContent = data.errors[field].join(', ');
                            fieldElement.parentNode.appendChild(errorDiv);
                        }
                    });
                }
            }
        })
        .catch(error => {
            console.error('Form submission error:', error);

            // Reset form state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            submitBtn.classList.remove('btn-loading');
            form.classList.remove('form-submitting');

            // Show error notification
            if (window.notifications) {
                window.notifications.error('Network error. Please try again.', 10000);
            }

            // Fallback to regular form submission
            setTimeout(() => {
                form.submit();
            }, 1000);
        });
}

function setCookie(name, value) {
    try {
        // Don't encode the value - cookies can handle special characters directly
        document.cookie = `${name}=${value};path=/;max-age=31536000`;
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