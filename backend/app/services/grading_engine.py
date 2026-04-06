from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.models.exam_results import ExamResultStatus
from app.models.grading_schemas import GradingSchemaType


TWO_PLACES = Decimal("0.01")
ONE_HUNDRED = Decimal("100.00")
PRESENT_STATUS = ExamResultStatus.PRESENT.value


def normalize_decimal(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def compute_grading_input_value(exam, grading_schema, exam_result) -> Decimal | None:
    if exam_result.points is None:
        return None

    if exam_result.status != PRESENT_STATUS:
        return None

    points = normalize_decimal(exam_result.points)

    if grading_schema.scheme_type == GradingSchemaType.POINTS:
        return points

    if grading_schema.scheme_type == GradingSchemaType.PERCENTAGE:
        if exam.max_points is None or exam.max_points <= 0:
            return None

        percentage = (points / exam.max_points) * ONE_HUNDRED
        return normalize_decimal(percentage)

    return None


def value_matches_range(value: Decimal, range_rule) -> bool:
    value = normalize_decimal(value)
    min_value = normalize_decimal(range_rule.min_value)
    max_value = normalize_decimal(range_rule.max_value)

    if range_rule.min_inclusive:
        min_ok = value >= min_value
    else:
        min_ok = value > min_value

    if range_rule.max_inclusive:
        max_ok = value <= max_value
    else:
        max_ok = value < max_value

    return min_ok and max_ok


def resolve_grade_for_value(grading_schema, value: Decimal | None) -> str | None:
    if value is None:
        return None

    normalized_value = normalize_decimal(value)

    for override in grading_schema.overrides:
        if normalize_decimal(override.input_value) == normalized_value:
            return override.grade.label

    matching_labels: list[str] = []
    for range_rule in grading_schema.ranges:
        if value_matches_range(normalized_value, range_rule):
            matching_labels.append(range_rule.grade.label)

    if len(matching_labels) == 1:
        return matching_labels[0]

    return None


def resolve_grade_for_exam_result(
    exam, grading_schema, exam_result
) -> tuple[Decimal | None, str | None]:
    input_value = compute_grading_input_value(
        exam=exam,
        grading_schema=grading_schema,
        exam_result=exam_result,
    )
    grade_label = resolve_grade_for_value(
        grading_schema=grading_schema,
        value=input_value,
    )
    return input_value, grade_label
