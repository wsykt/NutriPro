package com.health.repository;

import com.health.entity.SavedRecipe;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SavedRecipeRepository extends JpaRepository<SavedRecipe, Integer> {

    List<SavedRecipe> findByUserIdOrderByCreatedAtDesc(Integer userId);

    boolean existsByIdAndUserId(Integer id, Integer userId);

    void deleteByIdAndUserId(Integer id, Integer userId);

    /** 按来源系统菜谱ID删除收藏（兼容前端只持有系统菜谱ID、映射丢失的场景） */
    void deleteByUserIdAndOriginalRecipeId(Integer userId, Integer originalRecipeId);
}
