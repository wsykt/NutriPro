package com.health.util;

/**
 * 营养计算工具类 —— 集中管理 BMR、TDEE、BMI 等公式，
 * 避免公式散落在 DietService、ProfileService、NutritionReportService 等多处。
 */
public class NutritionCalculator {

    private NutritionCalculator() {}

    /**
     * 基于 Mifflin-St Jeor 公式计算基础代谢率（BMR）。
     * 男性: 10×体重(kg) + 6.25×身高(cm) - 5×年龄 + 5
     * 女性: 10×体重(kg) + 6.25×身高(cm) - 5×年龄 - 161
     */
    public static double calculateBMR(Double weight, Double height, Integer age, String gender) {
        double w = weight != null ? weight : 65;
        double h = height != null ? height : 165;
        int a = age != null ? age : 18;

        if ("女".equals(gender)) {
            return Math.round((10 * w + 6.25 * h - 5 * a - 161) * 10.0) / 10.0;
        } else {
            return Math.round((10 * w + 6.25 * h - 5 * a + 5) * 10.0) / 10.0;
        }
    }

    /**
     * 根据 BMR 和活动水平计算每日总能量消耗（TDEE）。
     *
     * @param bmr          基础代谢率
     * @param activityLevel 活动水平：sedentary=久坐(1.2), light=轻度(1.375),
     *                      moderate=中度(1.55), active=重度(1.725), very_active=极重度(1.9)
     * @return TDEE
     */
    public static double calculateTDEE(double bmr, String activityLevel) {
        double factor;
        switch (activityLevel) {
            case "sedentary":
                factor = 1.2;
                break;
            case "light":
                factor = 1.375;
                break;
            case "moderate":
                factor = 1.55;
                break;
            case "active":
                factor = 1.725;
                break;
            case "very_active":
                factor = 1.9;
                break;
            default:
                factor = 1.2;
        }
        return Math.round(bmr * factor * 10.0) / 10.0;
    }

    /**
     * 计算身体质量指数 BMI = 体重(kg) / (身高(cm)/100)^2
     */
    public static double calculateBMI(Double weight, Double height) {
        double w = weight != null ? weight : 0;
        double h = height != null ? height : 0;
        if (h <= 0) return 0;
        double hm = h / 100.0;
        return Math.round((w / (hm * hm)) * 10.0) / 10.0;
    }

    /**
     * 根据 BMI 值返回中文状态描述。
     */
    public static String getBMIStatus(double bmi) {
        if (bmi <= 0) return "-";
        if (bmi < 18.5) return "偏瘦";
        if (bmi < 24) return "正常";
        if (bmi < 28) return "超重";
        return "肥胖";
    }

    /**
     * 根据热量摄入/BMR 比率判断摄入是否合理。
     *
     * @param bmr      基础代谢率
     * @param bmrRatio 摄入热量 / BMR
     * @return "摄入不足" / "适量" / "摄入超标"
     */
    public static String getBMRStatus(double bmr, double bmrRatio) {
        if (bmrRatio < 0.8) return "摄入不足";
        if (bmrRatio <= 1.2) return "适量";
        return "摄入超标";
    }
}
