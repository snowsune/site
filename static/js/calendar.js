/**
 * Centralized calendar initialization for FullCalendar
 * Supports both full calendar view and day view widget
 */

function transformEvents(data, filterFn) {
    let filteredData = data;
    if (filterFn) {
        filteredData = data.filter(filterFn);
    }

    return filteredData.map(event => ({
        title: event.title,
        start: event.start,
        end: event.end,
        allDay: event.allDay || false,
        description: event.description,
        location: event.location,
        url: event.url,
        backgroundColor: event.color,
        borderColor: event.color,
        textColor: '#ffffff',
        extendedProps: {
            calendar: event.calendar,
            description: event.description,
            location: event.location,
        }
    }));
}

function createEventsFunction(filterFn) {
    return function (fetchInfo, successCallback, failureCallback) {
        // Fetch events from our API endpoint
        fetch(window.calendarEventsApiUrl || '/api/calendar/events/')
            .then(response => response.json())
            .then(data => {
                // Apply filter if provided
                const filter = filterFn ? (event) => {
                    const eventStart = new Date(event.start);
                    return filterFn(eventStart, fetchInfo.start, fetchInfo.end);
                } : null;

                const events = transformEvents(data, filter);
                successCallback(events);
            })
            .catch(error => {
                console.error('Error fetching calendar events:', error);
                failureCallback(error);
            });
    };
}

function createEventClickHandler() {
    return function (info) {
        // Show event details
        let details = '<strong>' + info.event.title + '</strong>';
        if (info.event.extendedProps.description) {
            details += '<br>' + info.event.extendedProps.description;
        }
        if (info.event.extendedProps.location) {
            details += '<br><em>Location: ' + info.event.extendedProps.location + '</em>';
        }
        if (info.event.url) {
            details += '<br><a href="' + info.event.url + '" target="_blank">More info →</a>';
        }
        alert(details);
    };
}

function initCalendar(elementId, options) {
    const calendarEl = document.getElementById(elementId);
    if (!calendarEl) {
        return null;
    }

    // Default options
    const defaultOptions = {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        height: 'auto',
        aspectRatio: 1.8,
        events: createEventsFunction(),
        eventClick: createEventClickHandler(),
    };

    // Merge user options with defaults
    const config = Object.assign({}, defaultOptions, options);

    // If custom events function not provided, use default with optional filter
    if (!config.events && options.filterFn) {
        config.events = createEventsFunction(options.filterFn);
    } else if (!config.events) {
        config.events = createEventsFunction();
    }

    // If custom eventClick not provided, use default
    if (!config.eventClick) {
        config.eventClick = createEventClickHandler();
    }

    const calendar = new FullCalendar.Calendar(calendarEl, config);
    calendar.render();
    return calendar;
}

// Initialize calendar when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Full calendar page
    if (document.getElementById('calendar')) {
        initCalendar('calendar', {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
            },
            height: 'auto',
            aspectRatio: 1.8,
        });
    }

    // Homepage day view widget
    if (document.getElementById('homepage-calendar')) {
        initCalendar('homepage-calendar', {
            initialView: 'timeGridDay',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: ''
            },
            height: 'auto',
            aspectRatio: 1.35,
            filterFn: function (eventStart, viewStart, viewEnd) {
                // Filter events for the visible day range
                return eventStart >= viewStart && eventStart < viewEnd;
            },
        });
    }
});

