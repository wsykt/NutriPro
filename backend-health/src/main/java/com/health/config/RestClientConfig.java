package com.health.config;

import org.apache.http.client.config.RequestConfig;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

@Configuration
public class RestClientConfig {

    /** AI 服务 URL，从配置文件读取，默认 localhost:8002 */
    @Value("${health.ai-service.url:http://localhost:8002}")
    private String aiServiceUrl;

    /** API 版本路径，从配置文件读取，默认 /api/v1 */
    @Value("${health.ai-service.api-prefix:/api/v1}")
    private String apiPrefix;

    /**
     * AI 服务专用 RestTemplate Bean。
     * 5s 连接超时，30s 读取超时，适合 AI 长响应场景。
     */
    @Bean("aiRestTemplate")
    public RestTemplate aiRestTemplate() {
        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectTimeout(5000)
                .setSocketTimeout(30000)
                .build();
        CloseableHttpClient httpClient = HttpClientBuilder.create()
                .setDefaultRequestConfig(requestConfig)
                .build();
        return new RestTemplate(new HttpComponentsClientHttpRequestFactory(httpClient));
    }

    /**
     * 获取完整的 AI 服务 API 基础 URL，格式为 http://host:port/apiPrefix。
     */
    public String getAiBaseUrl() {
        return aiServiceUrl + apiPrefix;
    }
}
