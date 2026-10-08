ARG NODE_VERSION=24.14.1

FROM node:${NODE_VERSION} AS dependencies

WORKDIR /usr/src/nl2sql-interface

COPY package.json package-lock.json ./

RUN npm ci

FROM node:${NODE_VERSION} AS builder

WORKDIR /usr/src/nl2sql-interface

COPY --from=dependencies /usr/src/nl2sql-interface/node_modules ./node_modules

COPY . .

ENV NODE_ENV production

RUN npm run build

FROM node:${NODE_VERSION} AS runner

WORKDIR /usr/src/nl2sql-interface

ENV NODE_ENV production
ENV PORT 3000
ENV HOST="0.0.0.0"

COPY --from=builder /usr/src/nl2sql-interface/node_modules ./node_modules

COPY --from=builder /usr/src/nl2sql-interface/dist ./dist

EXPOSE 3000

CMD ["node", "dist/main.js"]


