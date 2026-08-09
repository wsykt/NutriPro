package com.health.repository;

import com.health.entity.ExerciseRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface ExerciseRecordRepository extends JpaRepository<ExerciseRecord, Integer> {

    List<ExerciseRecord> findByUserIdOrderByRecordDateDesc(Integer userId);

    List<ExerciseRecord> findByUserIdAndRecordDate(Integer userId, LocalDate recordDate);

    List<ExerciseRecord> findByUserIdAndRecordDateBetweenOrderByRecordDateDesc(Integer userId, LocalDate startDate, LocalDate endDate);

    void deleteByIdAndUserId(Integer id, Integer userId);

    List<ExerciseRecord> findByStatus(String status);
}
