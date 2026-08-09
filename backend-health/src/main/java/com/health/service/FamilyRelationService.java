package com.health.service;

import com.health.entity.FamilyRelation;
import com.health.entity.User;
import com.health.repository.FamilyRelationRepository;
import com.health.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class FamilyRelationService {

    private final FamilyRelationRepository relationRepository;
    private final UserRepository userRepository;

    public FamilyRelationService(FamilyRelationRepository relationRepository, UserRepository userRepository) {
        this.relationRepository = relationRepository;
        this.userRepository = userRepository;
    }

    /**
     * 当前用户发出邀请："我(guardian) 想要监护 wardUsername 这个亲属"。
     */
    @Transactional
    public FamilyRelation addRelation(Integer guardianUserId, String wardUsername) {
        log.info("开始添加亲属关系, guardianId={}, wardUsername={}", guardianUserId, wardUsername);
        if (wardUsername == null || wardUsername.trim().isEmpty()) {
            throw new RuntimeException("亲属用户名不能为空");
        }
        User ward = userRepository.findByUsername(wardUsername.trim())
                .orElseThrow(() -> new RuntimeException("该用户名不存在"));
        if (ward.getUserId().equals(guardianUserId)) {
            throw new RuntimeException("不能将自己添加为亲属");
        }
        // 禁止双向嵌套：如果 ward 已经把 guardian 加为亲属，则不允许
        Optional<FamilyRelation> reverse = relationRepository.findByGuardianIdAndWardId(
                ward.getUserId(), guardianUserId);
        if (reverse.isPresent() && !"rejected".equals(reverse.get().getStatus())) {
            throw new RuntimeException("对方已将您添加为亲属，不允许建立双向监护关系");
        }
        // 不允许重复添加
        Optional<FamilyRelation> existing = relationRepository.findByGuardianIdAndWardId(
                guardianUserId, ward.getUserId());
        if (existing.isPresent()) {
            FamilyRelation r = existing.get();
            if ("rejected".equals(r.getStatus())) {
                r.setStatus("pending");
                return withNames(relationRepository.save(r));
            }
            return withNames(r);
        }
        FamilyRelation relation = new FamilyRelation();
        relation.setGuardianId(guardianUserId);
        relation.setWardId(ward.getUserId());
        relation.setStatus("pending");
        return withNames(relationRepository.save(relation));
    }

    @Transactional
    public FamilyRelation confirmRelation(Integer userId, Integer relationId) {
        FamilyRelation r = relationRepository.findById(relationId)
                .orElseThrow(() -> new RuntimeException("关系不存在"));
        if (!r.getWardId().equals(userId)) {
            throw new RuntimeException("只有被监护人可以确认邀请");
        }
        if (!"pending".equals(r.getStatus())) {
            throw new RuntimeException("当前状态不可确认");
        }
        r.setStatus("confirmed");
        return withNames(relationRepository.save(r));
    }

    @Transactional
    public FamilyRelation rejectRelation(Integer userId, Integer relationId) {
        FamilyRelation r = relationRepository.findById(relationId)
                .orElseThrow(() -> new RuntimeException("关系不存在"));
        if (!r.getWardId().equals(userId)) {
            throw new RuntimeException("只有被监护人可以拒绝邀请");
        }
        r.setStatus("rejected");
        return withNames(relationRepository.save(r));
    }

    public List<FamilyRelation> getMyWards(Integer guardianId) {
        return withNames(relationRepository.findByGuardianIdAndStatus(guardianId, "confirmed"));
    }

    public List<FamilyRelation> getMyGuardians(Integer wardId) {
        return withNames(relationRepository.findByWardIdAndStatus(wardId, "confirmed"));
    }

    public List<FamilyRelation> getPendingInvitations(Integer userId) {
        return withNames(relationRepository.findByWardIdAndStatus(userId, "pending"));
    }

    @Transactional
    public void deleteRelation(Integer userId, Integer relationId) {
        FamilyRelation r = relationRepository.findById(relationId)
                .orElseThrow(() -> new RuntimeException("关系不存在"));
        if (!r.getGuardianId().equals(userId) && !r.getWardId().equals(userId)) {
            throw new RuntimeException("无权操作此关系");
        }
        relationRepository.delete(r);
    }

    /**
     * 判断 guardianId 是否是 wardId 的已确认监护人。
     */
    public boolean isConfirmedGuardian(Integer guardianId, Integer wardId) {
        if (guardianId == null || wardId == null) return false;
        return relationRepository.existsByGuardianIdAndWardIdAndStatus(guardianId, wardId, "confirmed");
    }

    // —— 工具方法：填充用户名返回前端 ——
    private FamilyRelation withNames(FamilyRelation r) {
        if (r == null) return null;
        userRepository.findById(r.getGuardianId()).ifPresent(u -> r.setGuardianUsername(u.getUsername()));
        userRepository.findById(r.getWardId()).ifPresent(u -> r.setWardUsername(u.getUsername()));
        return r;
    }

    private List<FamilyRelation> withNames(List<FamilyRelation> list) {
        for (FamilyRelation r : list) withNames(r);
        return list;
    }
}
