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
    var lastCheckId = parseInt(dashboard.getAttribute('data-latest-comment-id')) || 0;

    function checkForNewComments() {
        let url = `/commorganizer/api/new_comments/?commission_name=${encodeURIComponent(commissionName)}`;
        if (lastCheckId) {
            url += `&since_id=${encodeURIComponent(lastCheckId)}`;
        }
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.comments && data.comments.length > 0) {
                    // Show desktop notification
                    if ("Notification" in window && Notification.permission === "granted") {
                        new Notification('New comments received! Refreshing…');
                    }
                    // Refresh after short delay
                    setTimeout(() => { window.location.reload(); }, 2000);
                    // Update lastCheckId to the highest returned comment ID
                    lastCheckId = Math.max(...data.comments.map(c => c.id));
                }
            });
    }

    setInterval(checkForNewComments, 30000);
}); 