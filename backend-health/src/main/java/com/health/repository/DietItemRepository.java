package com.health.repository;

import com.health.entity.DietItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DietItemRepository extends JpaRepository<DietItem, Integer> {
    List<DietItem> findByMealId(Integer mealId);

    @Query("SELECT di FROM DietItem di WHERE di.mealId IN :mealIds")
    List<DietItem> findByMealIdIn(@Param("mealIds") List<Integer> mealIds);
}
