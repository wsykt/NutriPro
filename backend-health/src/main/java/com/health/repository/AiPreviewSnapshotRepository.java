package com.health.repository;

import com.health.entity.AiPreviewSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface AiPreviewSnapshotRepository extends JpaRepository<AiPreviewSnapshot, Integer> {
    List<AiPreviewSnapshot> findBySessionIdOrderByIdDesc(String sessionId);
    Optional<AiPreviewSnapshot> findByPreviewTokenAndTokenExpireAtAfter(String previewToken, LocalDateTime now);
}
