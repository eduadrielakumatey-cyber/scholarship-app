# frontend/Dockerfile
#
# Dev-mode image (runs the Vite dev server) used by docker-compose for
# local development. For a real production deploy, build static assets
# instead (`npm run build`) and serve them from a static host (Vercel,
# Netlify, S3+CloudFront, or nginx) -- see README "Deploying to
# production" for the two-path explanation.

FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
