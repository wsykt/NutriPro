package com.health.repository;

import com.health.entity.AiConversationRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AiConversationRecordRepository extends JpaRepository<AiConversationRecord, Integer> {

    List<AiConversationRecord> findByUserIdOrderByCreatedAtDesc(Integer userId);
}
