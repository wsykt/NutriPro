package com.health.dto;

public class RegisterRequest {
    private String username;
    private String password;
    private String gender;
    private Double height;
    private Double weight;
    private Integer age;
    private String crowdType;

    public RegisterRequest() {}

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
}
