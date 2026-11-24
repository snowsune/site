/**
 * countdown widget
 */
(function () {
    const DAY_MS = 24 * 60 * 60 * 1000;

    function parseStart(event) {
        if (!event.start) return null;
        // special handling for all day (muddles midnught but i wont use all day tags under mff)
        if (event.allDay && /^\d{4}-\d{2}-\d{2}$/.test(event.start)) {
            const [y, m, d] = event.start.split('-').map(Number);
            return new Date(y, m - 1, d);
        }
        const dt = new Date(event.start);
        return isNaN(dt) ? null : dt;
    }

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function setOptionalText(el, text) {
        el.textContent = text;
        el.hidden = !text;
    }

    // Drop lines that are just the match keyword
    function cleanDescription(description, match) {
        return (description || '')
            .split(/\r?\n/)
            .filter(line => line.trim().toLowerCase() !== match)
            .join('\n')
            .trim();
    }

    function init(widget) {
        const match = (widget.dataset.match || 'MFF').toLowerCase();
        const lookaheadMs = (parseInt(widget.dataset.lookaheadDays, 10) || 14) * DAY_MS;

        fetch(widget.dataset.eventsUrl)
            .then(r => r.json())
            .then(events => {
                const now = Date.now();
                const next = events
                    .filter(e => (e.description || '').toLowerCase().includes(match))
                    .map(e => ({ event: e, start: parseStart(e) }))
                    .filter(x => x.start && x.start > now && x.start - now <= lookaheadMs)
                    .sort((a, b) => a.start - b.start)[0];

                if (!next) return; // Hide if clear for 2w

                widget.querySelector('.mff-countdown-title').textContent = next.event.title;
                setOptionalText(
                    widget.querySelector('.mff-countdown-location'),
                    (next.event.location || '').trim()
                );
                setOptionalText(
                    widget.querySelector('.mff-countdown-description'),
                    cleanDescription(next.event.description, match)
                );
                const units = {};
                widget.querySelectorAll('[data-unit]').forEach(el => {
                    units[el.dataset.unit] = el;
                });

                function tick() {
                    let remaining = Math.max(0, next.start - Date.now());
                    const days = Math.floor(remaining / DAY_MS);
                    remaining %= DAY_MS;
                    units.days.textContent = days;
                    units.hours.textContent = pad(Math.floor(remaining / 3600000));
                    units.minutes.textContent = pad(Math.floor((remaining % 3600000) / 60000));
                    units.seconds.textContent = pad(Math.floor((remaining % 60000) / 1000));
                    if (remaining <= 0 && days === 0) {
                        clearInterval(timer);
                        widget.classList.add('mff-countdown-done');
                    }
                }

                const timer = setInterval(tick, 1000);
                tick();
                widget.hidden = false;
            })
            .catch(err => console.error('MFF countdown: failed to load events', err));
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.mff-countdown-widget').forEach(init);
    });
})();
