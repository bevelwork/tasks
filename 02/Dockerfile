FROM node AS base
ENV NEXT_TELEMETRY_DISABLED 1 
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build 
COPY .env* ./
CMD ["npm", "run", "start"]
