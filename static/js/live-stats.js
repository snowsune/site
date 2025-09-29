function updateStats() {
    // Get current timestamp
    const now = new Date().getTime();

    // Check if we have recent cached data
    const cached = localStorage.getItem('statsCache');
    if (cached) {
        const { activeUsers, pageViews, uniqueVisitors, serverOffset, koFiProgress, timestamp } = JSON.parse(cached);
        const age = now - timestamp;

        // Use cached values if less than 30 seconds old
        if (age < 30000) {
            document.getElementById('active-users-count').textContent = activeUsers;
            if (document.getElementById('page-views-count')) {
                document.getElementById('page-views-count').textContent = pageViews;
            }
            if (document.getElementById('unique-visitors-count')) {
                document.getElementById('unique-visitors-count').textContent = uniqueVisitors;
            }
            document.getElementById('server-offset').textContent = serverOffset;
            document.getElementById('ko-fi-progress').textContent = koFiProgress;
            return;
        }
    }

    // Fetch live status data from single endpoint
    fetch('/api/live/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(response => response.json())
        .then(data => {
            const activeUsers = data.active_users || 0;
            const pageViews = data.page_views || 0;
            const uniqueVisitors = data.unique_visitors || 0;
            const serverOffset = data.server_offset || '?';
            const koFiProgress = data.ko_fi_progress || '?';

            // Update the DOM
            document.getElementById('active-users-count').textContent = activeUsers;
            if (document.getElementById('page-views-count')) {
                document.getElementById('page-views-count').textContent = pageViews;
            }
            if (document.getElementById('unique-visitors-count')) {
                document.getElementById('unique-visitors-count').textContent = uniqueVisitors;
            }
            document.getElementById('server-offset').textContent = serverOffset;
            document.getElementById('ko-fi-progress').textContent = koFiProgress;

            // Cache the results
            localStorage.setItem('statsCache', JSON.stringify({
                activeUsers: activeUsers,
                pageViews: pageViews,
                uniqueVisitors: uniqueVisitors,
                serverOffset: serverOffset,
                koFiProgress: koFiProgress,
                timestamp: now
            }));
        })
        .catch(error => {
            console.log('Failed to fetch stats:', error);
            // Show cached values if available
            const cached = localStorage.getItem('statsCache');
            if (cached) {
                const { activeUsers, pageViews, uniqueVisitors, serverOffset, koFiProgress } = JSON.parse(cached);
                document.getElementById('active-users-count').textContent = activeUsers;
                if (document.getElementById('page-views-count')) {
                    document.getElementById('page-views-count').textContent = pageViews;
                }
                if (document.getElementById('unique-visitors-count')) {
                    document.getElementById('unique-visitors-count').textContent = uniqueVisitors;
                }
                document.getElementById('server-offset').textContent = serverOffset;
                document.getElementById('ko-fi-progress').textContent = koFiProgress;
            }
        });
}

// Update every 30 seconds
setInterval(updateStats, 30000);

// Initial update
document.addEventListener('DOMContentLoaded', updateStats); 