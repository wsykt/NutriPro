package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "family_relation", uniqueConstraints = {
        @UniqueConstraint(columnNames = {"guardian_id", "ward_id"})
})
public class FamilyRelation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer relationId;

    @Column(name = "guardian_id", nullable = false)
    private Integer guardianId;

    @Column(name = "ward_id", nullable = false)
    private Integer wardId;

    @Column(name = "status", columnDefinition = "TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'rejected'))")
    private String status = "pending";

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    // 以下三个字段不存表，仅用于序列化返回前端
    @Transient
    private String guardianUsername;

    @Transient
    private String wardUsername;

    @Transient
    private Boolean isGuardianOfCurrentUser;

    public FamilyRelation() {}

    public Integer getRelationId() { return relationId; }
    public void setRelationId(Integer relationId) { this.relationId = relationId; }

    public Integer getGuardianId() { return guardianId; }
    public void setGuardianId(Integer guardianId) { this.guardianId = guardianId; }

    public Integer getWardId() { return wardId; }
    public void setWardId(Integer wardId) { this.wardId = wardId; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public String getGuardianUsername() { return guardianUsername; }
    public void setGuardianUsername(String guardianUsername) { this.guardianUsername = guardianUsername; }

    public String getWardUsername() { return wardUsername; }
    public void setWardUsername(String wardUsername) { this.wardUsername = wardUsername; }

    public Boolean getIsGuardianOfCurrentUser() { return isGuardianOfCurrentUser; }
    public void setIsGuardianOfCurrentUser(Boolean isGuardianOfCurrentUser) { this.isGuardianOfCurrentUser = isGuardianOfCurrentUser; }
}
