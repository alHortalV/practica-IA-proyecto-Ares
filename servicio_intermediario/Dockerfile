FROM node:20-alpine

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm install --production

# Copiar codigo fuente
COPY . .

EXPOSE 3000

CMD ["node", "servidor.js"]
