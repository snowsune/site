# Use the official Nginx image
FROM nginx:alpine

# Copy the placeholder HTML and CSS files into the container
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css

# Expose port 80
EXPOSE 80
