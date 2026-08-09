package com.health.service;

import com.health.dto.RegisterRequest;
import com.health.entity.BodyMetricsHistory;
import com.health.entity.User;
import com.health.repository.BodyMetricsHistoryRepository;
import com.health.repository.FamilyRelationRepository;
import com.health.repository.UserRepository;
import com.health.util.NutritionCalculator;
import com.health.vo.UserProfileVO;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import lombok.extern.slf4j.Slf4j;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
public class ProfileService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final BodyMetricsHistoryRepository historyRepository;
    private final FamilyRelationRepository familyRelationRepo;

    public ProfileService(UserRepository userRepository, PasswordEncoder passwordEncoder,
                          BodyMetricsHistoryRepository historyRepository,
                          FamilyRelationRepository familyRelationRepo) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.historyRepository = historyRepository;
        this.familyRelationRepo = familyRelationRepo;
    }

    public User getProfile(Integer userId) {
        return userRepository.findById(userId).orElse(null);
    }

    /**
     * 更新用户资料，并把今天的身高/体重/年龄/BMR 快照到身体指标历史表。
     * 返回值 Map 中包含 updatedUser 和 snapshotHistory。
     */
    @Transactional
    public Map<String, Object> updateProfileWithSnapshot(Integer userId, RegisterRequest request) {
        log.info("开始更新用户资料, userId={}", userId);
        User user = userRepository.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));

        if (request.getGender() != null) user.setGender(request.getGender());
        if (request.getHeight() != null) user.setHeight(request.getHeight());
        if (request.getWeight() != null) user.setWeight(request.getWeight());
        if (request.getAge() != null) user.setAge(request.getAge());
        if (request.getCrowdType() != null) user.setCrowdType(request.getCrowdType());

        user = userRepository.save(user);

        // 快照到历史表，同一天如果已经有就覆盖
        String today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
        Optional<BodyMetricsHistory> existing = historyRepository.findByUserIdAndRecordDate(userId, today);
        BodyMetricsHistory history = existing.orElse(new BodyMetricsHistory());
        history.setUserId(userId);
        history.setRecordDate(today);
        history.setHeight(user.getHeight());
        history.setWeight(user.getWeight());
        history.setAge(user.getAge());
        history.setCrowdType(user.getCrowdType());
        history.setBmr(NutritionCalculator.calculateBMR(user.getWeight(), user.getHeight(), user.getAge(), user.getGender()));
        history = historyRepository.save(history);

        Map<String, Object> result = new HashMap<>();
        result.put("user", user);
        result.put("snapshot", history);
        log.info("用户资料更新完成, userId={}", userId);
        return result;
    }

    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    public Map<String, Object> getUserInfo(Integer userId) {
        User user = getProfile(userId);
        if (user == null) return null;

        Map<String, Object> info = new HashMap<>();
        info.put("userId", user.getUserId());
        info.put("username", user.getUsername());
        info.put("gender", user.getGender());
        info.put("height", user.getHeight());
        info.put("weight", user.getWeight());
        info.put("age", user.getAge());
        info.put("crowdType", user.getCrowdType());
        info.put("role", user.getRole());
        info.put("createdAt", user.getCreatedAt() != null ? user.getCreatedAt().toString() : null);
        info.put("allergicFoods", user.getAllergicFoods());
        info.put("dietaryRestrictions", user.getDietaryRestrictions());
        info.put("tastePreference", user.getTastePreference());
        info.put("elderlyMode", user.getElderlyMode());

        double bmr = NutritionCalculator.calculateBMR(user.getWeight(), user.getHeight(), user.getAge(), user.getGender());
        info.put("bmr", bmr);

        double bmi = NutritionCalculator.calculateBMI(user.getWeight(), user.getHeight());
        info.put("bmi", bmi);
        info.put("bmiStatus", NutritionCalculator.getBMIStatus(bmi));

        return info;
    }

    public UserProfileVO getUserProfileVO(Integer userId) {
        User user = getProfile(userId);
        return UserProfileVO.fromEntity(user);
    }

    @Transactional
    public User updateDietaryProfile(Integer userId, Map<String, Object> dietaryProfile) {
        User user = userRepository.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));
        
        if (dietaryProfile.containsKey("allergicFoods")) {
            user.setAllergicFoods((String) dietaryProfile.get("allergicFoods"));
        }
        if (dietaryProfile.containsKey("dietaryRestrictions")) {
            user.setDietaryRestrictions((String) dietaryProfile.get("dietaryRestrictions"));
        }
        if (dietaryProfile.containsKey("tastePreference")) {
            user.setTastePreference((String) dietaryProfile.get("tastePreference"));
        }
        if (dietaryProfile.containsKey("elderlyMode")) {
            user.setElderlyMode((Integer) dietaryProfile.get("elderlyMode"));
        }
        
        return userRepository.save(user);
    }

    @Transactional
    public void deleteUser(Integer userId) {
        // 先删除关联的身体指标历史
        int metricsDeleted = historyRepository.deleteByUserId(userId);
        if (metricsDeleted > 0) {
            log.info("已删除 {} 条身体指标历史记录", metricsDeleted);
        }

        // 删除关联的亲属关系（作为监护人和作为被监护人）
        familyRelationRepo.deleteByGuardianId(userId);
        familyRelationRepo.deleteByWardId(userId);

        // 最后删除用户
        userRepository.deleteById(userId);
    }


}
