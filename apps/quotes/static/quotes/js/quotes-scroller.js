// Simple quotes scroller for the top bar

class QuotesScroller {
    constructor(containerId) {
        // Get the container element
        this.container = document.getElementById(containerId);
        this.quotes = [];
        this.currentIndex = 0;
        this.isScrolling = false;
        this.tooltip = null;

        // If the container exists, initialize the quotes!
        if (this.container) {
            this.createTooltip();
            this.init();
        }
    }

    createTooltip() {
        // Create tooltip element (For when you mouse over~)
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'quote-tooltip'; // Class for the tooltip (style in .css)
        document.body.appendChild(this.tooltip); // Add the tooltip to the body
    }

    async init() {
        // Load the quotes (in urls.py) 
        await this.loadQuotes();
        // Start the scrolling
        this.startScrolling();
    }

    async loadQuotes() {
        try {
            // Fetch the quotes (in urls.py)
            const response = await fetch('/quotes/api/quotes/');
            const data = await response.json();
            this.quotes = data.quotes || []; // If there are no quotes, show a message

            if (this.quotes.length === 0) {
                this.container.innerHTML = '<span>No quotes yet~</span>';
                return;
            }

            this.displayCurrentQuote();
        } catch (error) {
            console.error('Failed to load quotes:', error);
            this.container.innerHTML = '<span>Failed to load quotes!</span>';
        }
    }

    formatRelativeTime(timestamp) {
        // Format the time (e.g. "1 day ago", "2 hours ago", "3 minutes ago", "Just now")
        const now = new Date(); // Get the current time
        const quoteTime = new Date(timestamp); // Get the quote time
        const diffMs = now - quoteTime; // Get the difference in milliseconds
        const diffSeconds = Math.floor(diffMs / 1000); // Get the difference in seconds
        const diffMinutes = Math.floor(diffSeconds / 60); // Get the difference in minutes
        const diffHours = Math.floor(diffMinutes / 60); // Get the difference in hours
        const diffDays = Math.floor(diffHours / 24); // Get the difference in days

        if (diffDays > 0) { // If the difference in days is greater than 0
            return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`; // Return the difference in days
        } else if (diffHours > 0) { // If the difference in hours is greater than 0
            return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`; // Return the difference in hours
        } else if (diffMinutes > 0) { // If the difference in minutes is greater than 0
            return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`; // Return the difference in minutes
        } else { // If the difference in minutes is 0
            return 'Just now'; // Return "Just now"
        }
    }

    displayCurrentQuote() {
        if (this.quotes.length === 0) return; // If there are no quotes, return

        const quote = this.quotes[this.currentIndex]; // Get the current quote
        const relativeTime = this.formatRelativeTime(quote.created_at); // Get the relative time

        // Display the quote (in the container)
        this.container.innerHTML = `
            <span class="quote-content" data-full-content="${quote.content}">"${quote.content}"</span>
            <span class="quote-author">- ${quote.user}</span>
            <span class="quote-time">${relativeTime}</span>
        `;

        // Add tooltip functionality to quote content
        const contentElement = this.container.querySelector('.quote-content');
        if (contentElement) {
            this.setupTooltip(contentElement, quote.content);
        }

        // Trigger animation after a bit
        setTimeout(() => {
            const content = this.container.querySelector('.quote-content');
            const author = this.container.querySelector('.quote-author');
            const time = this.container.querySelector('.quote-time');
            if (content) content.classList.add('active');
            if (author) author.classList.add('active');
            if (time) time.classList.add('active');
        }, 200); // Delay the animation by 200ms
    }

    setupTooltip(element, fullContent) {
        // Check if content is truncated (Ellipsis)
        const isTruncated = element.scrollWidth > element.clientWidth;

        if (isTruncated) {
            element.addEventListener('mouseenter', (e) => this.showTooltip(e, fullContent));
            element.addEventListener('mouseleave', () => this.hideTooltip());
            element.addEventListener('mousemove', (e) => this.moveTooltip(e));
        }
    }

    showTooltip(event, content) {
        if (!this.tooltip) return;

        this.tooltip.textContent = `"${content}"`;
        this.tooltip.classList.add('show');
        this.moveTooltip(event);
    }

    hideTooltip() {
        if (!this.tooltip) return;
        this.tooltip.classList.remove('show');
    }

    moveTooltip(event) {
        if (!this.tooltip) return;

        const rect = event.target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();

        // Position tooltip above the quote content
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.top - tooltipRect.height - 10;

        // Ensure tooltip stays within viewport
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        if (top < 10) {
            // If tooltip would go above viewport, show it below instead
            top = rect.bottom + 10;
        }

        this.tooltip.style.left = left + 'px';
        this.tooltip.style.top = top + 'px';
    }

    nextQuote() {
        if (this.quotes.length === 0) return;

        // Fade out current quote
        const currentContent = this.container.querySelector('.quote-content');
        const currentAuthor = this.container.querySelector('.quote-author');
        const currentTime = this.container.querySelector('.quote-time');

        if (currentContent) currentContent.classList.remove('active');
        if (currentAuthor) currentAuthor.classList.remove('active');
        if (currentTime) currentTime.classList.remove('active');

        // Wait for fade out, then show next quote
        setTimeout(() => {
            this.currentIndex = (this.currentIndex + 1) % this.quotes.length;
            this.displayCurrentQuote();
        }, 500); // Match the CSS transition duration
    }

    startScrolling() {
        if (this.quotes.length <= 1) return;

        setInterval(() => {
            this.nextQuote();
        }, 12000); // Change quote every 12 seconds
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new QuotesScroller('quotes-scroller');
}); 
