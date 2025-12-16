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

# =================================================
# SMART & SIMPLE RECOMMENDATIONS
# =================================================
def generate_recommendations(area, workers, duration, risk):
    recs = []

    # قيم مرجعية بسيطة وواضحة
    ideal_workers = area / 40
    ideal_duration = area / 120

    workers_gap = round(ideal_workers - workers)
    duration_gap = round(ideal_duration - duration, 1)

    # -------------------------------
    # HIGH RISK
    # -------------------------------
    if risk == "High":

        if workers_gap > 0 and duration_gap > 0:
            recs.append(
                f"الخطر مرتفع لأن عدد العمال ({workers}) والمدة ({duration} أشهر) أقل من المناسب لحجم المشروع. "
                f"يُفضّل زيادة عدد العمال بحوالي {workers_gap + 2} عمال "
                f"وزيادة المدة بنحو {round(duration_gap + 1,1)} أشهر لتقليل احتمال التأخير."
            )

        elif workers_gap > 0:
            recs.append(
                f"الخطر مرتفع بسبب قلة عدد العمال مقارنة بحجم المشروع. "
                f"زيادة عدد العمال بحوالي {workers_gap + 2} قد تحسّن الالتزام بالجدول."
            )

        elif duration_gap > 0:
            recs.append(
                f"الخطر مرتفع لأن مدة التنفيذ ({duration} أشهر) قصيرة نسبيًا. "
                f"تمديد المدة بحوالي {round(duration_gap + 1,1)} أشهر قد يقلل التأخير."
            )

        else:
            recs.append(
                "الخطر مرتفع بسبب ضغط عام في تنفيذ المشروع، "
                "وتعديل بسيط في الموارد أو المدة قد يساعد على تقليل المخاطر."
            )

    # -------------------------------
    # MEDIUM RISK
    # -------------------------------
    elif risk == "Medium":

        if workers_gap > 0:
            recs.append(
                f"الخطر متوسط لأن عدد العمال قريب من الحد الأدنى. "
                f"إضافة عامل أو عاملين قد تخفّض مستوى الخطر."
            )

        elif duration_gap > 0:
            recs.append(
                f"الخطر متوسط لأن مدة المشروع ({duration} أشهر) ضيقة نسبيًا. "
                f"تمديد المدة بنحو نصف شهر إلى شهر قد يقلل احتمال التأخير."
            )

        else:
            recs.append(
                "الخطر متوسط بسبب توازن محدود بين المدة وعدد العمال. "
                "تحسين بسيط في أيٍ منهما قد يجعل الخطة أكثر استقرارًا."
            )

    # -------------------------------
    # LOW RISK
    # -------------------------------
    else:
        recs.append(
            "الخطة الحالية متوازنة، ولا يظهر خطر تأخير بناءً على البيانات المدخلة."
        )

    return recs

# =================================================
# FALLBACK LOGIC (بدون ML)
# =================================================
def rule_based_cost(area, project_size):
    base_rate = 1200
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

    # ---------------- COST ----------------
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
        estimated_cost = rule_based_cost(area_m2, project_size)

    # ---------------- DELAY ----------------
    if delay_model and model_columns:
        base_delay = float(delay_model.predict_proba([X])[0][1] * 100)
    else:
        base_delay = rule_based_delay(area_m2, workers, duration_months)

    pressure = calculate_pressure(area_m2, workers, duration_months)

    if pressure > 12:
        adjusted_delay = max(base_delay, 60 + (pressure - 12) * 2)
    elif pressure > 8:
        adjusted_delay = max(base_delay, 40 + (pressure - 8) * 2)
    else:
        adjusted_delay = min(base_delay, 25)

    delay_probability = round(min(adjusted_delay, 90), 1)
    risk_level = classify_risk(delay_probability)

    # ---------------- RECOMMENDATIONS ----------------
    recommendations = generate_recommendations(
        area_m2, workers, duration_months, risk_level
    )

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": delay_probability,
        "risk_level": risk_level,
        "recommendations": recommendations
    }
