from app.core.database.base_model import Base

'''
=====================================================
# Get all models that are allowed to be used in the generator
=====================================================
'''
def get_models():
    models = []
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        if getattr(model_class, '__allowed__', False):
            models.append(model_class)
    return models