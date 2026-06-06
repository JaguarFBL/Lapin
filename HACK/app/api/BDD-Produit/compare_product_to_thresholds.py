def compare_value_to_threshold(product_row, threshold_row):
    unit = product_row["declared_unit"]
    if unit != threshold_row["unit"]:
        return "unit_mismatch"

    product_lower = product_row.get("value_exact")
    if product_lower is None:
        product_lower = product_row.get("value_min")

    product_upper = product_row.get("value_exact")
    if product_upper is None:
        product_upper = product_row.get("value_max")

    if threshold_row.get("min_value") is not None:
        if product_lower is None:
            return "missing_lower_bound"
        if product_lower < threshold_row["min_value"]:
            return "below_min"

    if threshold_row.get("max_value") is not None:
        if product_upper is None:
            return "cannot_confirm_upper_bound"
        if product_upper > threshold_row["max_value"]:
            return "above_max"

    return "ok"
