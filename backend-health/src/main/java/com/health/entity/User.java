package com.health.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "user")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer userId;

    @Column(nullable = false, unique = true)
    private String username;

    @Column(name = "password", nullable = false)
    @com.fasterxml.jackson.annotation.JsonIgnore
    private String password;

    @Column(name = "gender", columnDefinition = "TEXT DEFAULT '男' CHECK(gender IN ('男', '女'))")
    private String gender = "男";

    @Column(name = "height", columnDefinition = "REAL DEFAULT 165 CHECK(height >= 0 AND height <= 300)")
    private Double height = 165.0;

    @Column(name = "weight", columnDefinition = "REAL DEFAULT 65 CHECK(weight >= 0 AND weight <= 300)")
    private Double weight = 65.0;

    @Column(name = "age", columnDefinition = "INTEGER DEFAULT 18 CHECK(age >= 0 AND age <= 150)")
    private Integer age = 18;

    @Column(name = "crowd_type", columnDefinition = "TEXT DEFAULT '普通人' CHECK(crowd_type IN ('普通人', '健身', '老年', '孕妇', '青少年', '糖尿病'))")
    private String crowdType = "普通人";

    @Column(name = "role", columnDefinition = "TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin'))")
    private String role = "user";

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "allergic_foods")
    private String allergicFoods;

    @Column(name = "dietary_restrictions")
    private String dietaryRestrictions;

    @Column(name = "taste_preference", columnDefinition = "TEXT DEFAULT '清淡' CHECK(taste_preference IN ('清淡', '适中', '重口味', '微辣', '辣'))")
    private String tastePreference = "清淡";

    @Column(name = "elderly_mode", columnDefinition = "INTEGER DEFAULT 0 CHECK(elderly_mode IN (0, 1))")
    private Integer elderlyMode = 0;

    @Column(name = "avatar")
    private String avatar;

    public User() {}

    public User(String username, String password) {
        this.username = username;
        this.password = password;
    }

    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }
    public Double getHeight() { return height; }
    public void setHeight(Double height) { this.height = height; }
    public Double getWeight() { return weight; }
    public void setWeight(Double weight) { this.weight = weight; }
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    public String getCrowdType() { return crowdType; }
    public void setCrowdType(String crowdType) { this.crowdType = crowdType; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public String getAllergicFoods() { return allergicFoods; }
    public void setAllergicFoods(String allergicFoods) { this.allergicFoods = allergicFoods; }
    public String getDietaryRestrictions() { return dietaryRestrictions; }
    public void setDietaryRestrictions(String dietaryRestrictions) { this.dietaryRestrictions = dietaryRestrictions; }
    public String getTastePreference() { return tastePreference; }
    public void setTastePreference(String tastePreference) { this.tastePreference = tastePreference; }
    public Integer getElderlyMode() { return elderlyMode; }
    public void setElderlyMode(Integer elderlyMode) { this.elderlyMode = elderlyMode; }
    public String getAvatar() { return avatar; }
    public void setAvatar(String avatar) { this.avatar = avatar; }
}
