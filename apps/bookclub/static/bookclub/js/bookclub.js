document.addEventListener('DOMContentLoaded', function () {
    const markers = document.querySelectorAll('.progress-marker');
    const timelineBar = document.querySelector('.timeline-bar');

    if (!markers.length || !timelineBar) return;

    const MIN_SPACING = 45; // Minimum pixels between markers to avoid overlap
    const VERTICAL_OFFSET = 80; // Vertical offset for stacked markers

    // Calculate horizontal position in pixels
    function getMarkerPosition(marker) {
        const leftPercent = parseFloat(marker.style.left);
        const barWidth = timelineBar.offsetWidth;
        return (leftPercent / 100) * barWidth;
    }

    // Check if two markers overlap
    function markersOverlap(marker1, marker2) {
        const pos1 = getMarkerPosition(marker1);
        const pos2 = getMarkerPosition(marker2);
        return Math.abs(pos1 - pos2) < MIN_SPACING;
    }

    // Sort markers by horizontal position (left to right)
    const sortedMarkers = Array.from(markers).sort((a, b) => {
        return getMarkerPosition(a) - getMarkerPosition(b);
    });

    // Group overlapping markers - a marker goes into a group if it overlaps with any marker in that group
    const groups = [];

    sortedMarkers.forEach(marker => {
        // Find a group this marker overlaps with
        let addedToGroup = false;
        for (let group of groups) {
            // Check if this marker overlaps with any marker in the group
            for (let groupMarker of group) {
                if (markersOverlap(marker, groupMarker)) {
                    group.push(marker);
                    addedToGroup = true;
                    break;
                }
            }
            if (addedToGroup) break;
        }

        // If no overlap found, start a new group
        if (!addedToGroup) {
            groups.push([marker]);
        }
    });

    // Apply vertical spacing to overlapping markers
    groups.forEach((group, groupIndex) => {
        if (group.length > 1) {
            // Multiple markers in this group - stack them vertically
            group.forEach((marker, markerIndex) => {
                const verticalOffset = (markerIndex - (group.length - 1) / 2) * VERTICAL_OFFSET;
                marker.style.top = `calc(50% + ${verticalOffset}px)`;
                marker.style.zIndex = 10 + markerIndex;
            });
        } else {
            // Single marker - keep default z-index
            group[0].style.zIndex = '10';
        }
    });

    // Add hover event listeners to ensure markers come to front on hover
    markers.forEach(marker => {
        marker.addEventListener('mouseenter', function () {
            this.style.zIndex = '100';
        });
        marker.addEventListener('mouseleave', function () {
            // Reset to original z-index on leave, but keep higher than default if needed
            const markerIndex = Array.from(markers).indexOf(this);
            this.style.zIndex = '10';
        });
    });
});

