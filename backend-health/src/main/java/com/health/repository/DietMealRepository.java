package com.health.repository;

import com.health.entity.DietMeal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DietMealRepository extends JpaRepository<DietMeal, Integer> {
    List<DietMeal> findByUserIdAndEatDate(Integer userId, String eatDate);
    List<DietMeal> findByUserIdOrderByEatDateDesc(Integer userId);
}
