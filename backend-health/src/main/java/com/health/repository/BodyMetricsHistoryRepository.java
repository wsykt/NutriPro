package com.health.repository;

import com.health.entity.BodyMetricsHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface BodyMetricsHistoryRepository extends JpaRepository<BodyMetricsHistory, Integer> {

    List<BodyMetricsHistory> findByUserIdOrderByRecordDateDesc(Integer userId);

    List<BodyMetricsHistory> findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(
            Integer userId, String startDate, String endDate);

    Optional<BodyMetricsHistory> findByUserIdAndRecordDate(Integer userId, String recordDate);

    void deleteByUserIdAndRecordDate(Integer userId, String recordDate);

    @Modifying
    @Query("DELETE FROM BodyMetricsHistory b WHERE b.userId = :userId")
    int deleteByUserId(@Param("userId") Integer userId);
}
