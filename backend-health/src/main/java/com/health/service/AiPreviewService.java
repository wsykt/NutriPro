package com.health.service;

import com.health.entity.AiPreviewSnapshot;
import com.health.repository.AiPreviewSnapshotRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * AI 产出快照（ai_preview_snapshot）统一服务层。
 *
 * <p>收敛「先预览后发布」与「流水线演示」各控制器对
 * {@link AiPreviewSnapshotRepository} 的直接依赖，统一快照读写入口。</p>
 */
@Service
public class AiPreviewService {

    private final AiPreviewSnapshotRepository repo;

    public AiPreviewService(AiPreviewSnapshotRepository repo) {
        this.repo = repo;
    }

    public AiPreviewSnapshot save(AiPreviewSnapshot snap) {
        return repo.save(snap);
    }

    public Optional<AiPreviewSnapshot> findById(Integer id) {
        return repo.findById(id);
    }

    public List<AiPreviewSnapshot> findBySessionIdOrderByIdDesc(String sessionId) {
        return repo.findBySessionIdOrderByIdDesc(sessionId);
    }

    public Optional<AiPreviewSnapshot> findByPreviewTokenAndTokenExpireAtAfter(String previewToken, LocalDateTime now) {
        return repo.findByPreviewTokenAndTokenExpireAtAfter(previewToken, now);
    }
}
