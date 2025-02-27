from fastapi import HTTPException
from sqlalchemy import and_, or_, cast, Integer, String, Float
from sqlalchemy.sql import operators
from sqlalchemy.orm import Mapper
from sqlalchemy.orm import RelationshipProperty

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

'''
=====================================================
# Resolves a nested relationship column dynamically.
    Example:
        - `role__name` -> Finds `role.name` from `User` model.
=====================================================
'''
def resolve_nested_column(model, nested_keys):
    current_model = model
    for i, attr in enumerate(nested_keys):
        # Check if the current attribute is a relationship
        relationship = getattr(current_model, attr, None)
        if relationship is not None and isinstance(relationship.property, RelationshipProperty):
            # Move to the related model class
            current_model = relationship.property.mapper.class_
        else:
            # If it's not a relationship, check if it's an attribute of the current model
            if hasattr(current_model, attr):
                # If it's the last key, return the attribute
                if i == len(nested_keys) - 1:
                    return getattr(current_model, attr)
                else:
                    # If it's not the last key, raise an error (invalid nested key)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid filter key: {'.'.join(nested_keys)}. "
                               f"Could not resolve attribute '{attr}' in model '{current_model.__name__}'."
                    )
            else:
                # If the attribute doesn't exist, raise an error
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filter key: {'.'.join(nested_keys)}. "
                           f"Could not resolve attribute '{attr}' in model '{current_model.__name__}'."
                )
    
    # If we reach here, return the final resolved column
    return current_model

'''
=====================================================
# Recursively parse filters into SQLAlchemy expressions, 
# including support for logical ($and, $or) and nested relationships.
=====================================================
'''

def parse_filters(model, filters):
    expressions = []

    if not isinstance(filters, dict):
        raise HTTPException(
            status_code=400, detail="Filters must be a dictionary")

    for key, value in filters.items():
        if key in LOGICAL_OPERATORS:  # Handle logical operators ($and, $or)
            if not isinstance(value, list):
                raise HTTPException(
                    status_code=400, detail=f"Logical operator '{key}' must have a list of conditions")

            sub_expressions = [parse_filters(
                model, sub_filter) for sub_filter in value]
            expressions.append(LOGICAL_OPERATORS[key](*sub_expressions))

        elif isinstance(value, dict):  # Handle field filtering
            nested_keys = key.split("__")  # Supports `role__name`
            column = resolve_nested_column(model, nested_keys)

            sub_expressions = []
            for operator, operand in value.items():
                if operator not in COMPARISON_OPERATORS:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid operator '{operator}' for field '{key}'")

                try:
                    if operator in ["$isempty", "$isnotempty"]:
                        sub_expressions.append(
                            COMPARISON_OPERATORS[operator](column))
                    else:
                        sub_expressions.append(
                            COMPARISON_OPERATORS[operator](column, operand))
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Error processing filter for field '{key}': {e}")

            if len(sub_expressions) > 1:
                expressions.append(and_(*sub_expressions))
            else:
                expressions.extend(sub_expressions)

        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid filter format for key '{key}': {value}")

    return and_(*expressions) if len(expressions) > 1 else expressions[0]