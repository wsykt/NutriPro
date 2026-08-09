package com.health.repository;

import com.health.entity.Article;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ArticleRepository extends JpaRepository<Article, Integer> {

    List<Article> findByStatusOrderByCreatedAtDesc(String status);

    List<Article> findByCategoryOrderByCreatedAtDesc(String category);

    List<Article> findByAudienceOrderByCreatedAtDesc(String audience);

    @Query("SELECT a FROM Article a WHERE a.status = 'published' AND (:category IS NULL OR a.category = :category) AND (:audience IS NULL OR a.audience = :audience) ORDER BY a.createdAt DESC")
    List<Article> findByCategoryAndAudience(@Param("category") String category, @Param("audience") String audience);

    List<Article> findByTopicOrderByCreatedAtDesc(String topic);

    Optional<Article> findByTitle(String title);

    /** 按主题分组ID查询（用于获取同主题不同篇幅的文章） */
    List<Article> findByTopicGroupIdOrderByLengthTypeAsc(String topicGroupId);

    @Query("SELECT a FROM Article a WHERE a.status = 'published' ORDER BY a.viewsCount DESC")
    List<Article> findTopByViews();

    @Query("SELECT a FROM Article a WHERE a.status = 'published' ORDER BY a.likesCount DESC")
    List<Article> findTopByLikes();

    @Query("SELECT DISTINCT a.category FROM Article a WHERE a.status = 'published'")
    List<String> findAllCategories();

    @Query("SELECT DISTINCT a.topic FROM Article a WHERE a.status = 'published'")
    List<String> findAllTopics();

    @Query("SELECT a FROM Article a WHERE a.status = 'published' AND (a.title LIKE %:keyword% OR a.content LIKE %:keyword% OR a.tags LIKE %:keyword%)")
    List<Article> searchByKeyword(@Param("keyword") String keyword);

    List<Article> findTopByStatusOrderByCreatedAtDesc(String status);

    /** 清空所有文章（用于重建 Demo 数据） */
    @org.springframework.data.jpa.repository.Modifying
    @org.springframework.data.jpa.repository.Query("DELETE FROM Article")
    @org.springframework.transaction.annotation.Transactional
    void deleteAllArticles();
}