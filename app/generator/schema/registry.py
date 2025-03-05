from .base import auto_generate_schemas
from app.api.schemas import schema_names

'''
=====================================================
# Get schemas for a given model
=====================================================
'''
def get_schemas(model):
    """
    Retrieve schemas for a given model.
    - If user-defined schemas exist in `app.api.schemas`, use them.
    - If not found, auto-generate schemas dynamically.
    """
    model_name = model.__name__

    # Attempt to load user-defined schemas from `app.api.schemas`
    schema_info = schema_names.get(model_name, {})
    create_schema = schema_info[0] if len(schema_info) > 0 else None
    update_schema = schema_info[1] if len(schema_info) > 1 else None
    response_all_schema = schema_info[2] if len(schema_info) > 2 else None
    response_id_schema = schema_info[3] if len(schema_info) > 3 else None

    # If a schema is missing, auto-generate it
    auto_generated_schemas = auto_generate_schemas(model)
    create_schema = create_schema or auto_generated_schemas[0]
    update_schema = update_schema or auto_generated_schemas[1]
    response_all_schema = response_all_schema or auto_generated_schemas[2]
    response_id_schema = response_id_schema or auto_generated_schemas[2]

    return create_schema, update_schema, response_all_schema, response_id_schema
