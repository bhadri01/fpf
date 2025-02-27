'''
=====================================================
# Filter Routes for admin views
=====================================================
'''

def get_all_routes():
    from main import app
    routes = []
    for route in app.router.routes:
        if (route.path.startswith("/admin") or 
            route.path.startswith("/docs") or 
            route.path.startswith("/redoc") or 
            route.path.startswith("/openapi") or 
            route.path.startswith("/openapi.json") or
            route.path.startswith("/public")):
                continue
        for method in route.methods:
            routes.append({
                "path": route.path,
                "method": method.upper(),
                "tags": [route.name]
            })    
    return routes
