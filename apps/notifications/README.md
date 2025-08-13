# Centralized Notification System

A beautiful, consistent notification system that any Django app can use to show user feedback.

## Features

- 🎨 **Beautiful Design**: Gradient backgrounds, smooth animations, responsive layout
- 🔧 **Easy to Use**: Simple API for both Python and JavaScript
- 📱 **Mobile Friendly**: Responsive design that works on all devices
- ⚡ **Auto-hide**: Smart timing for different notification types
- 🎯 **Centralized**: Consistent styling and behavior across the entire site

## Quick Start

### 1. JavaScript Usage (Any Template)

```javascript
// Show different types of notifications
window.notifications.success("Your comment was posted!");
window.notifications.error("Something went wrong!");
window.notifications.warning("Please check your input");
window.notifications.info("Processing your request...");

// Custom duration (in milliseconds)
window.notifications.success("Quick success!", 3000);

// Custom options
window.notifications.show("Custom message", "info", 5000, {
    className: "my-custom-notification"
});
```

### 2. Django Template Tags

```html
{% load notification_tags %}

<!-- Show notifications with default durations -->
{% show_success_notification "Comment posted successfully!" %}
{% show_error_notification "Please fix the errors below" %}
{% show_warning_notification "Your session expires soon" %}
{% show_info_notification "Processing your request..." %}

<!-- Custom duration (in milliseconds) -->
{% show_notification "Quick message" "success" 3000 %}
```

### 3. Python Views

```python
from apps.notifications.utils import show_success_notification, show_error_notification

def my_view(request):
    if form.is_valid():
        form.save()
        show_success_notification(request, "Data saved successfully!")
    else:
        show_error_notification(request, "Please fix the errors below")
    
    return render(request, "template.html")
```

## Notification Types

| Type | Default Duration | Use Case |
|------|------------------|----------|
| `success` | 5 seconds | Confirmations, successful actions |
| `error` | 15 seconds | Errors, validation failures |
| `warning` | 10 seconds | Warnings, important notices |
| `info` | 8 seconds | General information, tips |

## API Reference

### JavaScript API

```javascript
// Main methods
window.notifications.show(message, type, duration, options)
window.notifications.success(message, duration, options)
window.notifications.error(message, duration, options)
window.notifications.warning(message, duration, options)
window.notifications.info(message, duration, options)

// Utility methods
window.notifications.hide(notification)  // Hide specific notification
window.notifications.hideAll()           // Hide all notifications
```

### Django Template Tags

```html
{% show_notification message type duration %}
{% show_success_notification message duration %}
{% show_error_notification message duration %}
{% show_warning_notification message duration %}
{% show_info_notification message duration %}
```

### Python Utils

```python
from apps.notifications.utils import (
    show_notification,
    show_success_notification,
    show_error_notification,
    show_warning_notification,
    show_info_notification
)

# All functions take: (request, message, duration=default)
show_success_notification(request, "Success!")
show_error_notification(request, "Error occurred", 20000)
```

## Examples

### Blog Comment Success

```python
# In your view
if comment_form.is_valid():
    comment = comment_form.save()
    if request.user.is_authenticated:
        show_success_notification(request, "Comment posted successfully!")
    else:
        show_info_notification(request, "Comment submitted for moderation")
```

### Form Validation Errors

```python
# In your view
if not form.is_valid():
    show_error_notification(request, "Please fix the errors below")
    for field, errors in form.errors.items():
        for error in errors:
            show_error_notification(request, f"{field}: {error}")
```

### User Action Confirmation

```javascript
// In your JavaScript
function deleteItem() {
    if (confirm("Are you sure?")) {
        // Delete logic here
        window.notifications.success("Item deleted successfully!");
    }
}
```

## Styling

The notification system uses CSS custom properties for easy theming:

```css
:root {
    --success-color: #28a745;
    --error-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
}
```

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Graceful fallback for older browsers

## Contributing

To add new notification types or features:

1. Update `notifications.js` with new functionality
2. Add corresponding CSS classes
3. Update template tags and Python utils
4. Test across different devices and browsers
5. Update this README

## License

This notification system is part of the Snowsune site and follows the same license terms. 