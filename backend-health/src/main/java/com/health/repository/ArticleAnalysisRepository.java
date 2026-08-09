package com.health.repository;

import com.health.entity.ArticleAnalysis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ArticleAnalysisRepository extends JpaRepository<ArticleAnalysis, Long> {
    List<ArticleAnalysis> findByArticleIdOrderByCreatedAtDesc(Integer articleId);
    ArticleAnalysis findTopByArticleIdOrderByCreatedAtDesc(Integer articleId);
    List<ArticleAnalysis> findByStatus(String status);
    long countByStatus(String status);
}
