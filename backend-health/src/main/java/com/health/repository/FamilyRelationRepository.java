package com.health.repository;

import com.health.entity.FamilyRelation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface FamilyRelationRepository extends JpaRepository<FamilyRelation, Integer> {

    List<FamilyRelation> findByGuardianIdAndStatus(Integer guardianId, String status);

    List<FamilyRelation> findByWardIdAndStatus(Integer wardId, String status);

    Optional<FamilyRelation> findByGuardianIdAndWardId(Integer guardianId, Integer wardId);

    boolean existsByGuardianIdAndWardId(Integer guardianId, Integer wardId);

    boolean existsByGuardianIdAndWardIdAndStatus(Integer guardianId, Integer wardId, String status);

    @Modifying
    @Query("DELETE FROM FamilyRelation f WHERE f.guardianId = :guardianId")
    void deleteByGuardianId(@Param("guardianId") Integer guardianId);

    @Modifying
    @Query("DELETE FROM FamilyRelation f WHERE f.wardId = :wardId")
    void deleteByWardId(@Param("wardId") Integer wardId);
}
