package com.health.repository;

import com.health.entity.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Integer> {

    List<Comment> findByPostIdOrderByCreatedAtDesc(Integer postId);

    void deleteByPostId(Integer postId);

    List<Comment> findByUserIdOrderByCreatedAtDesc(Integer userId);

    List<Comment> findByStatus(String status);
}
