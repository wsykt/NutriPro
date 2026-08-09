package com.health.repository;

import com.health.entity.SavedRecipe;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SavedRecipeRepository extends JpaRepository<SavedRecipe, Integer> {

    List<SavedRecipe> findByUserIdOrderByCreatedAtDesc(Integer userId);

    void deleteByIdAndUserId(Integer id, Integer userId);
}
