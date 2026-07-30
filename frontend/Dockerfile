FROM node:23-alpine as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Build stage
FROM build AS development

# Expose port that Vite uses by default
EXPOSE 5173

# Command to run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]