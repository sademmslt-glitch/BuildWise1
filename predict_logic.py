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
# FRIENDLY & CONSISTENT RECOMMENDATIONS
# =================================================

def generate_recommendations(area, workers, duration, risk):
    recs = []

    # حساب القيم المناسبة
    rec_workers_min = int(area / 45)
    rec_workers_max = int(area / 35)

    rec_duration_min = round(area / 130, 1)
    rec_duration_max = round(area / 100, 1)

    workers_low = workers < rec_workers_min
    duration_low = duration < rec_duration_min

    if risk == "High":

        if workers_low and duration_low:
            recs.append(
                f"المشروع معرض للتأخير بسبب قلة العمال ({workers}) وقصر المدة ({duration} أشهر). "
                f"يُفضّل رفع عدد العمال إلى {rec_workers_min}–{rec_workers_max} "
                f"وزيادة المدة إلى {rec_duration_min}–{rec_duration_max} أشهر."
            )

        elif workers_low:
            recs.append(
                f"سبب التأخير المحتمل هو قلة عدد العمال ({workers}). "
                f"يُفضّل زيادتهم ليكونوا بين {rec_workers_min} و {rec_workers_max} عامل."
            )

        elif duration_low:
            recs.append(
                f"مدة المشروع ({duration} أشهر) قصيرة مقارنة بحجمه. "
                f"زيادة المدة إلى {rec_duration_min}–{rec_duration_max} أشهر قد تقلل التأخير."
            )

    elif risk == "Medium":

        if workers_low:
            recs.append(
                f"الخطر متوسط بسبب أن عدد العمال ({workers}) أقل من المناسب. "
                f"زيادة بسيطة في العمال قد تحسن الالتزام بالجدول."
            )

        elif duration_low:
            recs.append(
                f"الخطر متوسط لأن مدة المشروع قريبة من الحد الأدنى. "
                f"تمديد المدة قليلًا قد يعطي مرونة أفضل."
            )

        else:
            recs.append(
                "الخطر متوسط بسبب ضغط العمل، مع أن الوضع الحالي قابل للإدارة."
            )

    else:
        recs.append(
            "عدد العمال ومدة المشروع مناسبين لحجم العمل، ولا يظهر خطر تأخير واضح."
        )

    return recs

# =================================================
# FALLBACK LOGIC (NO ML)
# =================================================
def rule_based_cost(area, project_size):
    base_rate = 1200  # SAR per m² (approximate)
    size_factor = {
        "Small": 0.9,
        "Medium": 1.0,
        "Large": 1.15
    }
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
    if cost_model is not None and model_columns is not None:
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

    # ---------------------------------
    # DELAY PREDICTION
    # ---------------------------------
    if delay_model is not None and model_columns is not None:
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

    # ---------------------------------
    # RECOMMENDATIONS
    # ---------------------------------
    recommendations = generate_recommendations(
        area_m2,
        workers,
        duration_months,
        risk_level
    )

    return {
        "estimated_cost": round(estimated_cost, 0),
        "delay_probability": delay_probability,
        "risk_level": risk_level,
        "recommendations": recommendations
    }
