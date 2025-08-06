FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"] 