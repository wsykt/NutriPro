package com.health.repository;

import com.health.entity.Recipe;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RecipeRepository extends JpaRepository<Recipe, Integer> {
    List<Recipe> findByRecipeNameContaining(String name);
    List<Recipe> findByTagsContaining(String tag);
    List<Recipe> findByRecipeNameContainingOrTagsContaining(String name, String tags);
}