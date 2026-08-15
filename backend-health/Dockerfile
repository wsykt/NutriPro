# 后端服务（Spring Boot 2.7 / Java 1.8）
# 构建：maven:3.8-openjdk-8（若拉取失败可换 maven:3.9-eclipse-temurin-8）
# 运行：eclipse-temurin:8-jre
# 说明：项目以 Java 1.8 编译，运行时也需 JRE 8。
FROM maven:3.8-openjdk-8 AS build
WORKDIR /build
COPY pom.xml .
# 预下载依赖（利用层缓存）
RUN mvn -q dependency:go-offline || true
COPY src ./src
RUN mvn -q clean package -Dmaven.test.skip=true

FROM eclipse-temurin:8-jre
WORKDIR /app
# SQLite 数据库目录（数据持久化由 compose 卷挂载 /app/data）
RUN mkdir -p /app/data /app/logs
COPY --from=build /build/target/health-backend-1.0.0.jar /app/app.jar
# AI 服务地址通过 AI_SERVICE_URL 注入（默认指向本机）
ENV AI_SERVICE_URL=http://localhost:8002
ENV JAVA_OPTS="-Xms256m -Xmx512m"
EXPOSE 8082
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
