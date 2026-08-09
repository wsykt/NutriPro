package com.health.repository;

import com.health.entity.PostLike;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PostLikeRepository extends JpaRepository<PostLike, Integer> {

    Optional<PostLike> findByPostIdAndUserId(Integer postId, Integer userId);

    void deleteByPostIdAndUserId(Integer postId, Integer userId);

    long countByPostId(Integer postId);

    List<PostLike> findByUserIdOrderByCreatedAtDesc(Integer userId);
}
