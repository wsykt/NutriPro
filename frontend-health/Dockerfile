# 前端服务（Vue3 + Vite）
# 阶段一：构建静态产物；阶段二：nginx 托管 + /api 反向代理到后端
FROM node:20-alpine AS build
WORKDIR /app
# 优先用 package-lock.json 做可复现安装
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
# 构建产物输出到 dist/（.env.production 提供地图 key，已随代码目录携带）
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
