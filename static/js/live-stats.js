function updateStats() {
    const now = new Date().getTime();

    const cached = localStorage.getItem('statsCache');
    if (cached) {
        const { activeUsers, serverOffset, koFiProgress, timestamp } = JSON.parse(cached);
        if (now - timestamp < 30000) {
            document.getElementById('active-users-count').textContent = activeUsers;
            document.getElementById('server-offset').textContent = serverOffset ?? '?';
            document.getElementById('ko-fi-progress').textContent = koFiProgress ?? '?';
            return;
        }
    }

    fetch('/api/live/', { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
            const activeUsers = data.active_users ?? 0;
            const serverOffset = data.server_offset ?? '?';
            const koFiProgress = data.ko_fi_progress ?? '?';

            document.getElementById('active-users-count').textContent = activeUsers;
            document.getElementById('server-offset').textContent = serverOffset;
            document.getElementById('ko-fi-progress').textContent = koFiProgress;

            localStorage.setItem('statsCache', JSON.stringify({
                activeUsers,
                serverOffset,
                koFiProgress,
                timestamp: now
            }));
        })
        .catch(() => {
            // leave existing values or fall back to cache on next interval
        });
}

setInterval(updateStats, 30000);
document.addEventListener('DOMContentLoaded', updateStats);

