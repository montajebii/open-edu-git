# Use official Node.js image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm install --frozen-lockfile

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Command to run the application with hot-reload
CMD ["npm", "run", "dev"]