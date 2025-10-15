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
        let url = `/api/commorganizer/new_comments/?commission_name=${encodeURIComponent(commissionName)}`;
        if (lastCheckId !== null) {
            url += `&since_id=${encodeURIComponent(lastCheckId)}`;
        }
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.comments && data.comments.length > 0) {
                    if (lastCheckId === null) {
                        // First poll: just update lastCheckId, skip notification/refresh
                        lastCheckId = Math.max(...data.comments.map(c => c.id));
                        return;
                    }
                    // Show desktop notification
                    if ("Notification" in window && Notification.permission === "granted") {
                        new Notification('New comments received! Refreshing…');
                    }
                    setTimeout(() => { window.location.reload(); }, 2000);
                    lastCheckId = Math.max(...data.comments.map(c => c.id));
                } else {
                }
            });
    }

    setInterval(checkForNewComments, 15000);
}); 