package com.health.service;

import com.health.entity.Comment;
import com.health.entity.Post;
import com.health.entity.PostLike;
import com.health.repository.CommentRepository;
import com.health.repository.PostLikeRepository;
import com.health.repository.PostRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;

import java.util.stream.Collectors;

@Slf4j
@Service
@Transactional
public class CommunityService {

    private final PostRepository postRepository;
    private final CommentRepository commentRepository;
    private final PostLikeRepository postLikeRepository;

    public CommunityService(PostRepository postRepository,
                           CommentRepository commentRepository,
                           PostLikeRepository postLikeRepository) {
        this.postRepository = postRepository;
        this.commentRepository = commentRepository;
        this.postLikeRepository = postLikeRepository;
    }

    public List<Post> getAllPosts() {
        return postRepository.findAllByOrderByCreatedAtDesc().stream()
                .filter(p -> "approved".equals(p.getStatus()))
                .collect(Collectors.toList());
    }

    public List<Post> getPostsByTag(String tag) {
        return postRepository.findByTag(tag).stream()
                .filter(p -> "approved".equals(p.getStatus()))
                .collect(Collectors.toList());
    }

    public List<Post> getPostsByUser(Integer userId) {
        return postRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .filter(p -> "approved".equals(p.getStatus()))
                .collect(Collectors.toList());
    }

    public List<Post> getAllPostsForAdmin() {
        return postRepository.findAllByOrderByCreatedAtDesc();
    }

    public List<Post> getPostsByStatus(String status) {
        return postRepository.findByStatus(status);
    }

    public Post getPostById(Integer id) {
        return postRepository.findById(id).orElse(null);
    }

    public Post createPost(Integer userId, String username, String content, String tag) {
        log.info("开始创建社区帖子, userId={}, tag={}", userId, tag);
        Post post = new Post();
        post.setUserId(userId);
        post.setUsername(username);
        post.setContent(content);
        post.setTag(tag);
        return postRepository.save(post);
    }

    public void deletePost(Integer id) {
        commentRepository.deleteByPostId(id);
        postRepository.deleteById(id);
    }

    public List<Comment> getCommentsByPost(Integer postId) {
        return commentRepository.findByPostIdOrderByCreatedAtDesc(postId).stream()
                .filter(c -> "approved".equals(c.getStatus()))
                .collect(Collectors.toList());
    }

    public Comment addComment(Integer postId, Integer userId, String username, String content) {
        Post post = postRepository.findById(postId).orElse(null);
        if (post == null) return null;

        Comment comment = new Comment();
        comment.setPost(post);
        comment.setUserId(userId);
        comment.setUsername(username);
        comment.setContent(content);
        Comment saved = commentRepository.save(comment);

        post.setCommentsCount(post.getCommentsCount() + 1);
        postRepository.save(post);

        return saved;
    }

    public Comment getCommentById(Integer id) {
        return commentRepository.findById(id).orElse(null);
    }

    public void deleteComment(Integer id) {
        Comment comment = commentRepository.findById(id).orElse(null);
        if (comment != null) {
            Post post = comment.getPost();
            if (post != null && post.getCommentsCount() > 0) {
                post.setCommentsCount(post.getCommentsCount() - 1);
                postRepository.save(post);
            }
            commentRepository.deleteById(id);
        }
    }

    public Map<String, Object> toggleLike(Integer postId, Integer userId) {
        Map<String, Object> result = new HashMap<>();
        Post post = postRepository.findById(postId).orElse(null);
        if (post == null) {
            result.put("success", false);
            return result;
        }

        PostLike existingLike = postLikeRepository.findByPostIdAndUserId(postId, userId).orElse(null);
        // 兼容历史数据 likes_count 为 NULL 的情况
        Integer lc = post.getLikesCount();
        int base = lc == null ? 0 : lc;
        if (existingLike != null) {
            postLikeRepository.delete(existingLike);
            post.setLikesCount(Math.max(0, base - 1));
            result.put("liked", false);
        } else {
            PostLike like = new PostLike();
            like.setPost(post);
            like.setUserId(userId);
            postLikeRepository.save(like);
            post.setLikesCount(base + 1);
            result.put("liked", true);
        }

        postRepository.save(post);
        result.put("success", true);
        result.put("likesCount", post.getLikesCount());
        return result;
    }

    public boolean isLiked(Integer postId, Integer userId) {
        return postLikeRepository.findByPostIdAndUserId(postId, userId).isPresent();
    }

    public List<Post> getLikedPostsByUser(Integer userId) {
        List<PostLike> likes = postLikeRepository.findByUserIdOrderByCreatedAtDesc(userId);
        List<Post> result = new java.util.ArrayList<>();
        for (PostLike like : likes) {
            Post post = like.getPost();
            if (post != null) {
                result.add(post);
            }
        }
        return result;
    }

    public List<Comment> getCommentsByUser(Integer userId) {
        return commentRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .filter(c -> "approved".equals(c.getStatus()))
                .collect(Collectors.toList());
    }

    public List<Comment> getAllCommentsForAdmin() {
        return commentRepository.findAll();
    }

    public List<Comment> getCommentsByStatus(String status) {
        return commentRepository.findByStatus(status);
    }

    public Post approvePost(Integer postId) {
        Post post = postRepository.findById(postId).orElse(null);
        if (post != null) {
            post.setStatus("approved");
            return postRepository.save(post);
        }
        return null;
    }

    public Post rejectPost(Integer postId) {
        Post post = postRepository.findById(postId).orElse(null);
        if (post != null) {
            post.setStatus("rejected");
            return postRepository.save(post);
        }
        return null;
    }

    public Comment approveComment(Integer commentId) {
        Comment comment = commentRepository.findById(commentId).orElse(null);
        if (comment != null) {
            comment.setStatus("approved");
            return commentRepository.save(comment);
        }
        return null;
    }

    public Comment rejectComment(Integer commentId) {
        Comment comment = commentRepository.findById(commentId).orElse(null);
        if (comment != null) {
            comment.setStatus("rejected");
            return commentRepository.save(comment);
        }
        return null;
    }

    public List<String> getTags() {
        return java.util.Arrays.asList("饮食分享", "运动打卡", "健康知识", "心得感悟", "求助提问", "食谱推荐");
    }
}
