from app.core.database import Base

def get_models():
    models = []
    for mapper in Base.registry.mappers:
        models.append(mapper.class_)
    return models