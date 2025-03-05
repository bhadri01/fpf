import json
from typing import Dict, Optional, Tuple, Any
from fastapi import HTTPException
from sqlalchemy import and_, or_, DateTime
from sqlalchemy.sql import operators
from sqlalchemy.orm import RelationshipProperty, aliased
from sqlalchemy.sql import Select
from datetime import datetime, timedelta

LOGICAL_OPERATORS = {
    "$and": and_,
    "$or": or_
}

'''
=====================================================
# Parse Datetime
=====================================================
'''
def _parse_datetime(value: str) -> datetime:
    """Convert a string to a datetime object."""
    try:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {value}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date value '{value}': {str(e)}")

'''
=====================================================
# Adjust Date Range
=====================================================
'''
def _adjust_date_range(column, value: str, operator: str) -> Tuple[Any, bool]:
    """
    Adjust date string inputs for range-based comparisons when only a date is provided.
    Returns a tuple of (adjusted_value, is_range_condition).
    """
    if not isinstance(column.type, DateTime) or not isinstance(value, str):
        return value, False

    dt = _parse_datetime(value)
    # Check if the input is a date-only string (no time component)
    if len(value.split("T")) == 1 and " " not in value:
        if operator == "$eq":
            return and_(column >= dt, column < dt + timedelta(days=1)), True
        elif operator == "$ne":
            return or_(column < dt, column >= dt + timedelta(days=1)), True
        elif operator == "$gt":
            return dt + timedelta(days=1), False  # After the end of the day
        elif operator == "$gte":
            return dt, False  # Start of the day
        elif operator == "$lt":
            return dt, False  # Before the start of the day
        elif operator == "$lte":
            return dt + timedelta(days=1), False  # End of the day
    return dt, False

'''
=====================================================
# Comparison Operators
=====================================================
'''
COMPARISON_OPERATORS = {
    "$eq": lambda column, value: (
        column.is_(None) if value == ""
        else (
            adjusted_value if is_range else column == adjusted_value
        )
        if (adjusted_value := _adjust_date_range(column, value, "$eq")[0]) is not None and (is_range := _adjust_date_range(column, value, "$eq")[1]) is not None
        else column == value
    ),
    "$ne": lambda column, value: (
        column.is_not(None) if value == ""
        else (
            adjusted_value if is_range else column != adjusted_value
        )
        if (adjusted_value := _adjust_date_range(column, value, "$ne")[0]) is not None and (is_range := _adjust_date_range(column, value, "$ne")[1]) is not None
        else column != value
    ),
    "$gt": lambda column, value: operators.gt(column, _adjust_date_range(column, value, "$gt")[0]),
    "$gte": lambda column, value: operators.ge(column, _adjust_date_range(column, value, "$gte")[0]),
    "$lt": lambda column, value: operators.lt(column, _adjust_date_range(column, value, "$lt")[0]),
    "$lte": lambda column, value: operators.le(column, _adjust_date_range(column, value, "$lte")[0]),
    "$in": lambda column, value: (
        or_(*[
            _adjust_date_range(column, v, "$eq")[0] if isinstance(v, str) and isinstance(column.type, DateTime) else column == v
            for v in value
        ])
    ),
    "$contains": lambda column, value: column.ilike(f"%{value}%"),
    "$ncontains": lambda column, value: ~column.ilike(f"%{value}%"),
    "$startswith": lambda column, value: column.ilike(f"{value}%"),
    "$endswith": lambda column, value: column.ilike(f"%{value}"),
    "$isnotempty": lambda column: column.is_not(None),
    "$isempty": lambda column: column.is_(None),
    "$isanyof": lambda column, value: (
        or_(*[
            _adjust_date_range(column, v, "$eq")[0] if isinstance(v, str) and isinstance(column.type, DateTime) else column == v
            for v in value
        ])
    )
}

'''
=====================================================
# Resolve and Join Column
=====================================================
'''
def resolve_and_join_column(model, nested_keys: list[str], query: Select, joins: dict) -> Tuple[Any, Select]:
    current_model = model
    alias = None

    for i, attr in enumerate(nested_keys):
        relationship = getattr(current_model, attr, None)

        if relationship is not None and isinstance(relationship.property, RelationshipProperty):
            related_model = relationship.property.mapper.class_

            if related_model not in joins:
                alias = aliased(related_model)
                joins[related_model] = alias
                query = query.outerjoin(alias, getattr(current_model, attr))
            else:
                alias = joins[related_model]

            current_model = alias
        else:
            if hasattr(current_model, attr):
                return getattr(current_model, attr), query
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filter key: {'.'.join(nested_keys)}. "
                           f"Could not resolve attribute '{attr}' in model '{current_model.__name__}'."
                )

    raise HTTPException(
        status_code=400,
        detail=f"Could not resolve relationship for {'.'.join(nested_keys)}."
    )

'''
=====================================================
# Parse Filters
=====================================================
'''
def parse_filters(model, filters: dict, query: Select) -> Tuple[Optional[Any], Select]:
    expressions = []
    joins = {}

    if not isinstance(filters, dict):
        raise HTTPException(status_code=400, detail="Filters must be a dictionary")

    for key, value in filters.items():
        if key in LOGICAL_OPERATORS:
            if not isinstance(value, list):
                raise HTTPException(
                    status_code=400, detail=f"Logical operator '{key}' must have a list of conditions"
                )

            sub_expressions = []
            for sub_filter in value:
                sub_expr, updated_query = parse_filters(model, sub_filter, query)
                query = updated_query
                if sub_expr is not None:
                    sub_expressions.append(sub_expr)

            if sub_expressions:
                expressions.append(LOGICAL_OPERATORS[key](*sub_expressions))

        elif isinstance(value, dict):
            nested_keys = key.split("__")
            column, query = resolve_and_join_column(model, nested_keys, query, joins)

            for operator, operand in value.items():
                if operator not in COMPARISON_OPERATORS:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid operator '{operator}' for field '{key}'"
                    )

                try:
                    if operator in ["$isempty", "$isnotempty"]:
                        expressions.append(COMPARISON_OPERATORS[operator](column))
                    else:
                        expressions.append(COMPARISON_OPERATORS[operator](column, operand))
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Error processing filter for field '{key}': {e}"
                    )

        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid filter format for key '{key}': {value}"
            )

    return and_(*expressions) if expressions else None, query

'''
=====================================================
# Parse Filter Query
=====================================================
'''
def parse_filter_query(filters: Optional[str]) -> Optional[Dict]:
    if not filters:
        return None
    try:
        parsed_filters = json.loads(filters)
        if not isinstance(parsed_filters, dict):
            raise ValueError("Filters should be a valid JSON object (dictionary).")
        return parsed_filters
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter JSON: {str(e)}")