# Kilkaari/Dockerfile
FROM nginx:alpine

# Remove the default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy the static site in
COPY . /usr/share/nginx/html

EXPOSE 80
