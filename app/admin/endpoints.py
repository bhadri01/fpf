from fastapi import APIRouter, Request, Form, Depends, status, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from app.core.database.base_model import Base
from app.core.database.db import get_write_session, get_read_session
from app.core.permissions import load_permissions
from app.admin.routes_filter import get_all_routes
from typing import List

templates = Jinja2Templates(directory="app/admin/ui/templates")

router = APIRouter()

# Dynamically generate the model mapping dictionary
model_mapping = {str(mapper.class_.__tablename__).lower(): mapper.class_ for mapper in Base.registry.mappers}

'''
=====================================================
# Assign Roles (GET) Route              
=====================================================
'''


@router.get("/settings/assign-roles", response_class=HTMLResponse)
async def assign_roles(request: Request, db: AsyncSession = Depends(get_read_session)):
    roles = await db.execute(select(model_mapping['roles']))
    roles = roles.scalars().all()
    routes = get_all_routes()

    # Categorize routes based on tags
    categorized_routes = {}
    for route in routes:
        tags = route.get('tags', ['Uncategorized'])
        for tag in tags:
            if tag not in categorized_routes:
                categorized_routes[tag] = []
            categorized_routes[tag].append(route)

    # Get assigned routes for each role
    assigned_routes = {}
    for role in roles:
        role_permissions = await db.execute(select(model_mapping['role_permissions']).where(model_mapping['role_permissions'].role_id == role.id))
        role_permissions = role_permissions.scalars().all()
        assigned_routes[str(role.id)] = {}
        for perm in role_permissions:
            if perm.route not in assigned_routes[str(role.id)]:
                assigned_routes[str(role.id)][perm.route] = []
            assigned_routes[str(role.id)][perm.route].append(perm.method)

    return templates.TemplateResponse("settings/assign_roles.html", {"request": request, "roles": roles, "categorized_routes": categorized_routes, "assigned_routes": assigned_routes})


'''
=====================================================
# Assign Roles (POST) Route        
=====================================================
'''


@router.post("/settings/assign-roles", response_class=HTMLResponse)
async def assign_roles_post(
    role: str = Form(...),
    routes: List[str] = Form(None),
    db: AsyncSession = Depends(get_write_session)
):
    if role is None:
        return RedirectResponse(url="/admin/settings/assign-roles", status_code=status.HTTP_303_SEE_OTHER)

    # Clear existing permissions for the role
    await db.execute(delete(model_mapping['role_permissions']).where(model_mapping['role_permissions'].role_id == role))
    await db.commit()

    # Add new permissions if routes are provided
    if routes:
        for route in routes:
            path, method = route.split("|")
            permission = model_mapping['role_permissions'](
                role_id=role, route=path, method=method)
            db.add(permission)
        await db.commit()

    # Reload permissions cache
    await load_permissions(db)

    return RedirectResponse(url="/admin/settings/assign-roles", status_code=status.HTTP_303_SEE_OTHER)


async def get_model_instance(model_name: str, db: AsyncSession, id: int = None):
    model_class = model_mapping.get(model_name.lower())
    if model_class:
        if id:
            result = await db.execute(select(model_class).where(model_class.id == id))
            return result.scalars().first()
        else:
            result = await db.execute(select(model_class))
            return result.scalars().all()
    return None


'''
=====================================================
# Index Route                      
=====================================================
'''


@router.get("", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


'''
=====================================================
# Get Create Model Route           
=====================================================
'''


@router.get("/{model_name}/create", tags=["Admin"])
async def get_create_model(model_name: str, request: Request):
    if not model_mapping.get(model_name.lower()):
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(f"{model_name}/create_{model_name}.html", {"request": request})


'''
=====================================================
# Post Create Model Route          
=====================================================
'''


@router.post("/{model_name}/create", tags=["Admin"])
async def post_create_model(model_name: str, request: Request, db: AsyncSession = Depends(get_write_session)):
    model_class = model_mapping.get(model_name.lower())
    if not model_class:
        raise HTTPException(status_code=404, detail="Model not found")

    form_data = await request.form()
    new_instance = model_class(**form_data)
    db.add(new_instance)
    await db.commit()
    return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_303_SEE_OTHER)


'''
=====================================================
# Get Update Model Route           
=====================================================
'''


@router.get("/{model_name}/update/{id}", tags=["Admin"])
async def get_update_model(model_name: str, id: str, request: Request, db: AsyncSession = Depends(get_read_session)):
    model = await get_model_instance(model_name, db, id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(f"{model_name}/update_{model_name}.html", {"request": request, "model": model, "id": id})


'''
=====================================================
# Post Update Model Route          
=====================================================
'''


@router.post("/{model_name}/update/{id}", tags=["Admin"])
async def post_update_model(model_name: str, id: str, request: Request, db: AsyncSession = Depends(get_write_session)):
    model_class = model_mapping.get(model_name.lower())
    if not model_class:
        raise HTTPException(status_code=404, detail="Model not found")

    form_data = await request.form()
    await db.execute(update(model_class).where(model_class.id == id).values(**form_data))
    await db.commit()
    return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_303_SEE_OTHER)


'''
=====================================================
# View Models Route                
=====================================================
'''


@router.get("/{model_name}", tags=["Admin"])
async def view_models(model_name: str, request: Request, db: AsyncSession = Depends(get_read_session)):
    models = await get_model_instance(model_name, db)
    if models == None:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(f"{model_name}/list_{model_name}.html", {"request": request, "models": models})


'''
=====================================================
# View Model by ID Route           
=====================================================
'''


@router.get("/{model_name}/{id}", tags=["Admin"])
async def view_model_by_id(model_name: str, id: str, request: Request, db: AsyncSession = Depends(get_read_session)):
    model = await get_model_instance(model_name, db, id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(f"{model_name}/view_{model_name}.html", {"request": request, "model": model})


'''
=====================================================
# Delete Model Route               
=====================================================
'''


@router.post("/{model_name}/delete/{id}", tags=["Admin"])
async def delete_model(model_name: str, id: str, request: Request, db: AsyncSession = Depends(get_write_session)):
    model_class = model_mapping.get(model_name.lower())
    if not model_class:
        raise HTTPException(status_code=404, detail="Model not found")
    # Fetch the record to delete
    query = select(model_class).where(model_class.id == id)
    result = await db.execute(query)
    db_obj = result.scalar_one_or_none()
    # If the record doesn't exist, raise a 404 error
    if not db_obj:
        raise HTTPException(status_code=404, detail="Data not found")
    # Delete the record and commit the transaction
    await db.delete(db_obj)
    await db.commit()
    return RedirectResponse(url=f"/admin/{model_name}", status_code=status.HTTP_303_SEE_OTHER)
