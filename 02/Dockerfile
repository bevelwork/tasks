FROM node AS base
ENV NEXT_TELEMETRY_DISABLED 1 

WORKDIR /app
COPY package.json package-lock.json ./
COPY tsconfig.json ./
RUN --mount=type=cache,target=/app/.npm \
    npm set cache .npm
RUN npm install
COPY . .
RUN npm run build
COPY .env* ./

CMD ["npm", "run", "start"]
