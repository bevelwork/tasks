FROM node AS base
ENV NEXT_TELEMETRY_DISABLED 1 

WORKDIR /app
COPY package.json package-lock.json ./
COPY tsconfig.json ./
RUN --mount=type=cache,target=/app/.npm \
    npm set cache .npm
RUN npm install
COPY . .
# This generates a ./.next folder that's required to run `npm run start`
RUN npm run build 
COPY .env* ./

CMD ["npm", "run", "start"]
