package com.health.vo;

import com.health.entity.User;
import com.health.util.NutritionCalculator;

public class UserProfileVO {

    private Integer id;
    private String username;
    private String avatar;
    private String gender;
    private Integer age;
    private Double height;
    private Double weight;
    private String crowdType;
    private Double bmi;
    private String bmiStatus;
    private Double bmr;

    public UserProfileVO() {}

    public static UserProfileVO fromEntity(User user) {
        if (user == null) return null;
        UserProfileVO vo = new UserProfileVO();
        vo.setId(user.getUserId());
        vo.setUsername(user.getUsername());
        vo.setGender(user.getGender());
        vo.setAge(user.getAge());
        vo.setHeight(user.getHeight());
        vo.setWeight(user.getWeight());
        vo.setCrowdType(user.getCrowdType());

        double bmi = NutritionCalculator.calculateBMI(user.getWeight(), user.getHeight());
        vo.setBmi(bmi);
        vo.setBmiStatus(NutritionCalculator.getBMIStatus(bmi));

        double bmr = NutritionCalculator.calculateBMR(user.getWeight(), user.getHeight(), user.getAge(), user.getGender());
        vo.setBmr(bmr);

        return vo;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getAvatar() { return avatar; }
    public void setAvatar(String avatar) { this.avatar = avatar; }
    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    public Double getHeight() { return height; }
    public void setHeight(Double height) { this.height = height; }
    public Double getWeight() { return weight; }
    public void setWeight(Double weight) { this.weight = weight; }
    public String getCrowdType() { return crowdType; }
    public void setCrowdType(String crowdType) { this.crowdType = crowdType; }
    public Double getBmi() { return bmi; }
    public void setBmi(Double bmi) { this.bmi = bmi; }
    public String getBmiStatus() { return bmiStatus; }
    public void setBmiStatus(String bmiStatus) { this.bmiStatus = bmiStatus; }
    public Double getBmr() { return bmr; }
    public void setBmr(Double bmr) { this.bmr = bmr; }
}
