package com.health.repository;

import com.health.entity.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PostRepository extends JpaRepository<Post, Integer> {

    List<Post> findByUserIdOrderByCreatedAtDesc(Integer userId);

    List<Post> findByTag(String tag);

    List<Post> findAllByOrderByCreatedAtDesc();

    List<Post> findByContentContaining(String keyword);

    List<Post> findByStatus(String status);
}
