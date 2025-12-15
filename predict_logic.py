import pickle
import numpy as np
import os

# =================================================
# SAFE MODEL LOADING
# =================================================
def safe_load_model(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

cost_model = safe_load_model("cost_model.pkl")
delay_model = safe_load_model("delay_model.pkl")
model_columns = safe_load_model("model_columns.pkl")

# =================================================
# HELPER FUNCTIONS
# =================================================
def calculate_pressure(area, workers, duration):
    return (area / max(workers, 1)) / max(duration, 0.5)

def classify_risk(delay_prob):
    if delay_prob < 30:
        return "Low"
    elif delay_prob < 55:
        return "Medium"
    else:
        return "High"

def generate_recommendations(area, workers, duration, risk):
    recs = []

    ideal_workers = max(5, int(area / 40))
    ideal_duration = max(1.5, area / 120)

    if risk == "High":
        if workers < ideal_workers:
            recs.append(
                f"عدد العمال الحالي أقل من المعتاد لمشاريع بهذا الحجم. "
                f"رفع العدد تدريجيًا ليكون قريبًا من {ideal_workers} عامل قد يحسّن سير العمل."
            )

        if duration < ideal_duration:
            recs.append(
                f"مدة التنفيذ الحالية ضاغطة نسبيًا. "
                f"لو كانت المدة بين {round(ideal_duration,1)} و {round(ideal_duration+1,1)} أشهر "
                f"قد يكون التنفيذ أكثر استقرارًا."
            )

        recs.append(
            "ترتيب الأنشطة الأساسية مبكرًا مثل توريد المواد والموافقات "
            "يساعد في تقليل احتمالية التوقف غير المتوقع."
        )

    elif risk == "Medium":
        recs.append(
            "الوضع الحالي مقبول، لكن المتابعة المنتظمة تساعد في معالجة أي ضغط قبل أن يتفاقم."
        )

        if workers < ideal_workers:
            recs.append(
                "في حال ظهور ضغط في الجدول، دعم الفريق بعدد محدود من العمال خلال المراحل الحساسة "
                "قد يعطي مرونة أفضل."
            )

    else:
        recs.append(
            "الخطة الحالية متوازنة بشكل عام. "
            "الاستمرار بنفس الأسلوب مع متابعة دورية كافٍ للحفاظ على استقرار المشروع."
        )

    return recs

# =================================================
# FALLBACK LOGIC (بدون ML)
# =================================================
def rule_based_cost(area, project_size):
    base_rate = 1200  # ريال/م² (تقريبي واقعي)
    size_factor = {"Small": 0.9, "Medium": 1.0, "Large": 1.15}
    return area * base_rate * size_factor.get(project_size, 1.0)

def rule_based_delay(area, workers, duration):
    pressure = calculate_pressure(area, workers, duration)

    if pressure > 12:
        return 65
    elif pressure > 8:
        return 45
    else:
        return 20

# =================================================
# MAIN PREDICTION FUNCTION
# =================================================
def predict(project_type, project_size, area_m2, duration_months, workers):

    # ---------------------------------
    # COST PREDICTION
    # ---------------------------------
    if cost_model and model_columns:
        X = np.zeros(len(model_columns))
        for i, col in enumerate(model_columns):
            if col == "area_m2":
                X[i] = area_m2
            elif col == "duration_months":
                X[i] = duration_months
            elif col == "workers":
                X[i] = workers
            elif col == f"project_type_{project_type}":
                X[i] = 1
            elif col == f"project_size_{project_size}":
                X[i] = 1

        estimated_cost = float(cost_model.predict([X])[0])
    else:
        # Fallback
        estimated_cost = rule_based_cost(area_m2, project_size)

    # ---------------------------------
    # DELAY PREDICTION
    # ---------------------------------
    if delay_model and model_columns:
        base_delay = float(delay_model.predict_proba([X])[0][1] * 100)
    else:
        base_delay = rule_based_delay(area_m2, workers, duration_months)

    pressure = calculate_pressure(area_m2, workers, duration_months)

    # Hybrid adjustment
    if pressure > 12:
        adjusted_delay = max(base_delay, 60 + (pressure - 12) * 2)
    elif pressure > 8:
        adjusted_delay = max(base_delay, 40 + (pressure - 8) * 2)
    else:
        adjusted_delay = min(base_delay, 25)

    delay_probability = round(min(adjusted_delay, 90), 1)
    risk_level = classify_risk(delay_probability)

    # ---------------------------------
    # RECOMMENDATIONS
    # ---------------------------------
    recommendations = generate_recommendations(
        area_m2, workers, duration_months, risk_level
    )

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": delay_probability,
        "risk_level": risk_level,
        "recommendations": recommendations
    }
