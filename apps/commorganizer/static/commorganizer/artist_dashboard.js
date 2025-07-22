document.addEventListener('DOMContentLoaded', function () {
    // --- Desktop Notification Permission ---
    if ("Notification" in window && Notification.permission !== "granted") {
        var notifyContainer = document.getElementById('notify-permission-container');
        if (notifyContainer) {
            notifyContainer.style.display = '';
            var notifyBtn = document.getElementById('notify-permission-btn');
            if (notifyBtn) {
                notifyBtn.onclick = function () {
                    Notification.requestPermission().then(function (permission) {
                        if (permission === "granted") {
                            notifyContainer.style.display = 'none';
                        }
                    });
                };
            }
        }
    }

    // --- Polling for New Comments ---
    var dashboard = document.getElementById('artist-dashboard-container');
    if (!dashboard) return;
    var commissionName = dashboard.getAttribute('data-commission-name');
    var debug = false; // Set to true to enable debug logging
    var lastCheckId = null; // Start as null, not 0

    function checkForNewComments() {
        if (debug) console.log('[CommOrganizer] Polling for new comments...');
        let url = `/commorganizer/api/new_comments/?commission_name=${encodeURIComponent(commissionName)}`;
        if (lastCheckId !== null) {
            url += `&since_id=${encodeURIComponent(lastCheckId)}`;
        }
        if (debug) console.log('[CommOrganizer] Fetching URL:', url);
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (debug) console.log('[CommOrganizer] Data received:', data);
                if (data.comments && data.comments.length > 0) {
                    if (debug) console.log('[CommOrganizer] New comments found:', data.comments);
                    if (lastCheckId === null) {
                        // First poll: just update lastCheckId, skip notification/refresh
                        lastCheckId = Math.max(...data.comments.map(c => c.id));
                        if (debug) console.log('[CommOrganizer] First poll, updating lastCheckId but not notifying.');
                        return;
                    }
                    // Show desktop notification
                    if ("Notification" in window && Notification.permission === "granted") {
                        if (debug) console.log('[CommOrganizer] Showing notification for new comments');
                        new Notification('New comments received! Refreshing…');
                    }
                    setTimeout(() => { window.location.reload(); }, 2000);
                    lastCheckId = Math.max(...data.comments.map(c => c.id));
                } else {
                    if (debug) console.log('[CommOrganizer] No new comments found.');
                }
            });
    }

    setInterval(checkForNewComments, 15000);
}); 