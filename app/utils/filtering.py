from sqlalchemy import and_, or_, cast, Integer, String, Float
from sqlalchemy.sql import operators
from sqlalchemy.orm import Mapper


LOGICAL_OPERATORS = {
    "$and": and_,
    "$or": or_
}

COMPARISON_OPERATORS = {
    "$eq": lambda column, value: column.is_(None) if value == "" else column == cast(value, column.type) if isinstance(value, str) else column == value,
    "$ne": lambda column, value: column.is_not(None) if value == "" else column != cast(value, column.type) if isinstance(value, str) else column != value,
    "$gt": operators.gt,
    "$gte": operators.ge,
    "$lt": operators.lt,
    "$lte": operators.le,
    "$in": operators.in_op,
    "$contains": lambda column, value: column.ilike(f"%{value}%"),
    "$ncontains": lambda column, value: ~column.ilike(f"%{value}%"),
    "$startswith": lambda column, value: column.ilike(f"{value}%"),
    "$endswith": lambda column, value: column.ilike(f"%{value}"),
    "$isnotempty": lambda column: column.is_not(None),
    "$isempty": lambda column: column.is_(None),
    "$isanyof": lambda column, value: column.in_(value)
}


def parse_filters(model, filters):
    """
    Recursively parse filters into SQLAlchemy expressions.
    Includes error handling for type mismatches and ensures valid column types.
    """
    expressions = []
    for key, value in filters.items():
        if key in LOGICAL_OPERATORS:  # Handle logical operators ($and, $or)
            sub_expressions = [
                parse_filters(model, sub_filter) for sub_filter in value
            ]
            expressions.append(LOGICAL_OPERATORS[key](*sub_expressions))

        elif isinstance(value, dict):  # Handle comparison operators
            column = getattr(model, key, None)
            if column is None:
                raise ValueError(f"Invalid filter key: '{key}'")

            for operator, operand in value.items():
                if operator not in COMPARISON_OPERATORS:
                    raise ValueError(f"Invalid operator '{operator}' for field '{key}'")

                try:
                    # Special handling for NULL-like checks
                    if operator in ["$isempty", "$isnotempty"]:
                        expressions.append(COMPARISON_OPERATORS[operator](column))
                    else:
                        # Validate operand type against column type
                        column_type = column.type
                        if isinstance(column_type, (Integer, Float)) and not isinstance(operand, (int, float)):
                            raise ValueError(
                                f"Type mismatch for field '{key}': Expected numeric, got '{operand}'"
                            )
                        if isinstance(column_type, String) and not isinstance(operand, str):
                            raise ValueError(
                                f"Type mismatch for field '{key}': Expected string, got '{operand}'"
                            )

                        # Apply the filter
                        expressions.append(COMPARISON_OPERATORS[operator](column, operand))
                except Exception as e:
                    raise ValueError(
                        f"Error processing filter for field '{key}' with operator '{operator}': {e}"
                    ) from e
        else:
            raise ValueError(f"Invalid filter format for key '{key}': {value}")

    return and_(*expressions) if len(expressions) > 1 else expressions[0]

