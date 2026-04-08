# syntax=docker/dockerfile:1

ARG NODE_VERSION=24.12.0

FROM node:${NODE_VERSION}-alpine as base

FROM base as deps

RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=package-lock.json,target=package-lock.json \
    --mount=type=cache,target=/root/.npm \
    npm ci

FROM deps as build

COPY . .

RUN npm run build

################################################################################
FROM base as final

USER node

COPY package.json .

COPY --from=deps node_modules ./node_modules
COPY --from=build dist ./dist

EXPOSE 5173

CMD npm run dev
