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
     * 长文本生成专用 RestTemplate（如科普文章母稿）。
     * 本地 Ollama 生成长文（800~3000字）耗时超过 30s，需要更长读取超时。
     * 5s 连接超时，300s 读取超时（B方案双模型流水线实测约 156s：本地框架+云端外扩+本地校验）。
     */
    @Bean("aiRestTemplateLong")
    public RestTemplate aiRestTemplateLong() {
        RequestConfig requestConfig = RequestConfig.custom()
                .setConnectTimeout(5000)
                .setSocketTimeout(300000)
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
