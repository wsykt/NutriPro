package com.health.entity;

import javax.persistence.*;

@Entity
@Table(name = "body_metrics_history", uniqueConstraints = {
        @UniqueConstraint(columnNames = {"user_id", "record_date"})
})
public class BodyMetricsHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer historyId;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "record_date", nullable = false)
    private String recordDate;

    @Column(name = "height")
    private Double height;

    @Column(name = "weight")
    private Double weight;

    @Column(name = "age")
    private Integer age;

    @Column(name = "bmr")
    private Double bmr;

    @Column(name = "crowd_type")
    private String crowdType;

    public BodyMetricsHistory() {}

    public Integer getHistoryId() { return historyId; }
    public void setHistoryId(Integer historyId) { this.historyId = historyId; }

    public Integer getUserId() { return userId; }
    public void setUserId(Integer userId) { this.userId = userId; }

    public String getRecordDate() { return recordDate; }
    public void setRecordDate(String recordDate) { this.recordDate = recordDate; }

    public Double getHeight() { return height; }
    public void setHeight(Double height) { this.height = height; }

    public Double getWeight() { return weight; }
    public void setWeight(Double weight) { this.weight = weight; }

    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }

    public Double getBmr() { return bmr; }
    public void setBmr(Double bmr) { this.bmr = bmr; }

    public String getCrowdType() { return crowdType; }
    public void setCrowdType(String crowdType) { this.crowdType = crowdType; }
}
