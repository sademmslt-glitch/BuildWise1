def generate_recommendations(area, workers, duration, risk):
    recs = []

    # القيم المرجعية
    ideal_workers = area / 40
    ideal_duration = area / 120

    workers_gap = round(ideal_workers - workers)
    duration_gap = round(ideal_duration - duration, 1)

    # ===============================
    # HIGH RISK
    # ===============================
    if risk == "High":

        if workers_gap > 0 and duration_gap > 0:
            recs.append(
                f"الخطر مرتفع لأن عدد العمال ({workers}) والمدة ({duration} أشهر) أقل من المطلوب لحجم المشروع. "
                f"يُفضّل رفع عدد العمال بنحو {workers_gap + 2} عمال "
                f"وزيادة المدة بحوالي {round(duration_gap + 1,1)} أشهر لتقليل احتمال التأخير."
            )

        elif workers_gap > 0:
            recs.append(
                f"الخطر مرتفع لأن عدد العمال ({workers}) أقل من المناسب لحجم المشروع. "
                f"زيادة العمال بعدد {workers_gap + 2} قد تساعد في استقرار الجدول."
            )

        elif duration_gap > 0:
            recs.append(
                f"الخطر مرتفع بسبب قصر مدة التنفيذ ({duration} أشهر). "
                f"تمديد المدة بحوالي {round(duration_gap + 1,1)} أشهر قد يقلل التأخير."
            )

        else:
            recs.append(
                "الخطر مرتفع بسبب ضغط عام في تنفيذ المشروع، "
                "وتعديل بسيط في الموارد أو المدة قد يحسن الوضع."
            )

    # ===============================
    # MEDIUM RISK
    # ===============================
    elif risk == "Medium":

        if workers_gap > 0:
            recs.append(
                f"الخطر متوسط لأن عدد العمال قريب من الحد الأدنى. "
                f"إضافة عامل أو عاملين قد تخفّض الخطر إلى مستوى منخفض."
            )

        elif duration_gap > 0:
            recs.append(
                f"الخطر متوسط لأن مدة المشروع ({duration} أشهر) ضيقة نسبيًا. "
                f"تمديد المدة بنحو نصف شهر إلى شهر قد يقلل احتمال التأخير."
            )

        else:
            recs.append(
                "الخطر متوسط بسبب توازن محدود بين المدة والعمال. "
                "تحسين بسيط في أيٍ منهما كافٍ لتقليل المخاطر."
            )

    # ===============================
    # LOW RISK
    # ===============================
    else:
        recs.append(
            "الخطة الحالية مناسبة، ولا يظهر خطر تأخير بناءً على البيانات المدخلة."
        )

    return recs
