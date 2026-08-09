package com.health.controller;

import com.health.dto.ApiResponse;
import com.health.entity.Comment;
import com.health.entity.Post;
import com.health.entity.User;
import com.health.repository.UserRepository;
import com.health.service.CommunityService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/community")
@CrossOrigin
public class CommunityController {

    private final UserRepository userRepository;
    private final CommunityService communityService;

    public CommunityController(UserRepository userRepository, CommunityService communityService) {
        this.userRepository = userRepository;
        this.communityService = communityService;
    }

    private User extractUser(Authentication authentication) {
        if (authentication == null) return null;
        if (authentication.getPrincipal() instanceof User) {
            return (User) authentication.getPrincipal();
        }
        try {
            return userRepository.findByUsername(authentication.getName()).orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    @GetMapping("/posts")
    public ResponseEntity<ApiResponse<List<Post>>> getAllPosts(@RequestParam(required = false) String tag) {
        List<Post> posts;
        if (tag != null && !tag.trim().isEmpty()) {
            posts = communityService.getPostsByTag(tag.trim());
        } else {
            posts = communityService.getAllPosts();
        }
        return ResponseEntity.ok(ApiResponse.success(posts));
    }

    @GetMapping("/posts/user/{userId}")
    public ResponseEntity<ApiResponse<List<Post>>> getPostsByUser(@PathVariable Integer userId) {
        List<Post> posts = communityService.getPostsByUser(userId);
        return ResponseEntity.ok(ApiResponse.success(posts));
    }

    @GetMapping("/post/{id}")
    public ResponseEntity<ApiResponse<Post>> getPostById(@PathVariable Integer id) {
        Post post = communityService.getPostById(id);
        if (post == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success(post));
    }

    @PostMapping("/post/create")
    public ResponseEntity<ApiResponse<Post>> createPost(
            Authentication authentication,
            @RequestBody Map<String, Object> postData) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String content = String.valueOf(postData.getOrDefault("content", ""));
        if (content.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请输入内容"));
        }

        String tag = postData.get("tag") != null ? String.valueOf(postData.get("tag")) : null;
        Post post = communityService.createPost(user.getUserId(), user.getUsername(), content.trim(), tag);
        return ResponseEntity.ok(ApiResponse.success("发布成功", post));
    }

    @DeleteMapping("/post/{id}")
    public ResponseEntity<ApiResponse<Void>> deletePost(
            Authentication authentication,
            @PathVariable Integer id) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        Post post = communityService.getPostById(id);
        if (post == null) {
            return ResponseEntity.notFound().build();
        }

        if (!post.getUserId().equals(user.getUserId())) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权删除"));
        }

        communityService.deletePost(id);
        return ResponseEntity.ok(ApiResponse.success("已删除", null));
    }

    @GetMapping("/post/{id}/comments")
    public ResponseEntity<ApiResponse<List<Comment>>> getComments(@PathVariable Integer id) {
        List<Comment> comments = communityService.getCommentsByPost(id);
        return ResponseEntity.ok(ApiResponse.success(comments));
    }

    @PostMapping("/post/{id}/comment")
    public ResponseEntity<ApiResponse<Comment>> addComment(
            Authentication authentication,
            @PathVariable Integer id,
            @RequestBody Map<String, Object> commentData) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        String content = String.valueOf(commentData.getOrDefault("content", ""));
        if (content.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, "请输入评论内容"));
        }

        Comment comment = communityService.addComment(id, user.getUserId(), user.getUsername(), content.trim());
        if (comment == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(ApiResponse.success("评论成功", comment));
    }

    @DeleteMapping("/comment/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteComment(
            Authentication authentication,
            @PathVariable Integer id) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        Comment comment = communityService.getCommentById(id);
        if (comment == null) {
            return ResponseEntity.notFound().build();
        }

        if (!comment.getUserId().equals(user.getUserId())) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error(HttpStatus.FORBIDDEN.value(), "无权删除"));
        }

        communityService.deleteComment(id);
        return ResponseEntity.ok(ApiResponse.success("已删除", null));
    }

    @PostMapping("/post/{id}/like")
    public ResponseEntity<ApiResponse<Map<String, Object>>> toggleLike(
            Authentication authentication,
            @PathVariable Integer id) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        Map<String, Object> result = communityService.toggleLike(id, user.getUserId());
        if ((Boolean) result.get("success")) {
            return ResponseEntity.ok(ApiResponse.success(result));
        }
        return ResponseEntity.notFound().build();
    }

    @GetMapping("/post/{id}/is-liked")
    public ResponseEntity<ApiResponse<Boolean>> isLiked(
            Authentication authentication,
            @PathVariable Integer id) {

        User user = extractUser(authentication);
        if (user == null || user.getUserId() == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.error(HttpStatus.UNAUTHORIZED.value(), "请先登录"));
        }

        boolean liked = communityService.isLiked(id, user.getUserId());
        return ResponseEntity.ok(ApiResponse.success(liked));
    }

    @GetMapping("/tags")
    public ResponseEntity<ApiResponse<List<String>>> getTags() {
        List<String> tags = communityService.getTags();
        return ResponseEntity.ok(ApiResponse.success(tags));
    }

    @GetMapping("/posts/liked/{userId}")
    public ResponseEntity<ApiResponse<List<Post>>> getLikedPostsByUser(@PathVariable Integer userId) {
        List<Post> posts = communityService.getLikedPostsByUser(userId);
        return ResponseEntity.ok(ApiResponse.success(posts));
    }

    @GetMapping("/comments/user/{userId}")
    public ResponseEntity<ApiResponse<List<Comment>>> getCommentsByUser(@PathVariable Integer userId) {
        List<Comment> comments = communityService.getCommentsByUser(userId);
        return ResponseEntity.ok(ApiResponse.success(comments));
    }
}
