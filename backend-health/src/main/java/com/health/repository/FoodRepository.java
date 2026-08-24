package com.health.repository;

import com.health.entity.Food;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FoodRepository extends JpaRepository<Food, Integer> {
    List<Food> findByStatus(String status);

    @Query("SELECT f FROM Food f WHERE f.foodName LIKE %:keyword% AND f.status = 'approved' ORDER BY f.priority DESC, f.foodId ASC")
    List<Food> searchByName(@Param("keyword") String keyword);

    @Query("SELECT f FROM Food f WHERE f.foodName = :name AND f.status = 'approved' ORDER BY f.priority DESC")
    List<Food> findByNameExact(@Param("name") String name);

    @Query("SELECT f FROM Food f WHERE f.foodCategory = :category AND f.status = 'approved' ORDER BY f.priority DESC, f.foodId ASC")
    List<Food> findByCategory(@Param("category") String category);

    @Query("SELECT f FROM Food f WHERE f.status = 'approved' ORDER BY f.priority DESC, f.foodId ASC")
    List<Food> findAllApproved();
}
