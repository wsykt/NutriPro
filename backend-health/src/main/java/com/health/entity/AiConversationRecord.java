package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "ai_conversation_record")
public class AiConversationRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "model")
    private String model;

    @Column(name = "question", columnDefinition = "TEXT")
    private String question;

    @Column(name = "reply", columnDefinition = "TEXT")
    private String reply;

    @Column(name = "health_snapshot_json", columnDefinition = "TEXT")
    private String healthSnapshotJson;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public AiConversationRecord() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }

    public String getModel() { return model; }
    public void setModel(String model) { this.model = model; }

    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }

    public String getReply() { return reply; }
    public void setReply(String reply) { this.reply = reply; }

    public String getHealthSnapshotJson() { return healthSnapshotJson; }
    public void setHealthSnapshotJson(String healthSnapshotJson) { this.healthSnapshotJson = healthSnapshotJson; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
