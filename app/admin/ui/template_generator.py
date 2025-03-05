import os
from app.generator.schema.registry import get_schemas
from app.utils.base_path import path_conversion


def generate_template(model, all_models):
    model_name = model.__name__.lower()
    model_tablename = model.__tablename__
    fields = model.__table__.columns.keys()
    template_folder_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "templates"))
    '''
    =====================================================
    # Create templates directory if it does not exist
    =====================================================
    '''
    if not os.path.exists(template_folder_path):
        os.makedirs(template_folder_path)

    model_template_folder_path = os.path.join(
        template_folder_path, model_tablename)
    if not os.path.exists(model_template_folder_path):
        os.makedirs(model_template_folder_path)

    settings_template_folder_path = os.path.join(
        template_folder_path, "settings")
    if not os.path.exists(settings_template_folder_path):
        os.makedirs(settings_template_folder_path)

    '''
    =====================================================
    # Create templates
    # Generate menu bar
    =====================================================
    '''
    menu_bar = f"""
<main style="width:20%" class="d-flex flex-nowrap  border-end  text-light border-light bg-dark sticky-top "> 
  <div class="d-flex flex-column flex-shrink-0 p-3 " style="width: 100%;">
    <ul class="nav nav-pills flex-column mb-auto">
        <h5>Models</h5>
        <li class="nav-item">
        <a href="{path_conversion("/admin")}" class="nav-link active" aria-current="page">Index</a>
        </li>
"""
    for mdl in sorted(all_models, key=lambda x: x.__name__.lower()):
        mdl_name = mdl.__name__.lower()
        mdl_tablename = mdl.__tablename__
        menu_bar += f'''        <li class="nav-item">
        <a href="{path_conversion("/admin/" + mdl_tablename)}" class="nav-link " aria-current="page">{mdl_name.capitalize()}</a>
        </li>\n'''
    menu_bar += f"""
    <hr>
    <h5>Settings</h5>
    <li class="nav-item">
    <a href="{path_conversion("/admin/settings/assign-roles")}" class="nav-link " aria-current="page">Assign Roles</a>
    </li>
    </ul>
        
</div>
</main>
"""
    '''
    =====================================================
    # Index Route
    # Generate index template
    =====================================================
    '''
    index_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Admin Index</title>
     <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
</head>
<body>
<div style="width: 100%" class="d-flex gap-3 bg-dark text-light">
    {menu_bar}
    <div style="width: 80%" class="d-flex flex-column gap-2 mt-5">
    <h1 >Admin Index</h1>
</div>
</div>
</body>
</html>
"""
    with open(f"{template_folder_path}/index.html", "w") as f:
        f.write(index_template_content)

    '''
    =====================================================
    # Post Create Model Route
    # Generate schemas
    =====================================================
    '''
    SchemaCreate, SchemaUpdate, SchemaAllResponse, SchemaIdResponse = get_schemas(model)

    # Generate create template
    create_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Create {model_name.capitalize()}</title>
    <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div style="width: 100%" class="d-flex  gap-3 bg-dark text-light">
    {menu_bar}
    <div style="width: 78%" class="d-flex flex-column gap-2 mt-5 ">
    <h1>Create {model_name.capitalize()}</h1>
    <form action="{path_conversion("/admin/" + model_tablename + "/create")}" method="post" class="needs-validation" novalidate>
        <div class="row">
"""
    for i, field in enumerate(SchemaCreate.__fields__):
        create_template_content += f'''
            <div class="col-md-6 mb-3">
                <label for="{field}" class="form-label">{field.capitalize()}</label>
                <input type="text" class="form-control" id="{field}" name="{field}" placeholder="{field.capitalize()}" >
                <div class="invalid-feedback">
                    Please provide a valid {field}.
                </div>
            </div>
'''
        if (i + 1) % 2 == 0:
            create_template_content += '</div><div class="row">'
    create_template_content += """
        </div>
        <button type="submit" class="btn btn-primary">Create</button>
    </form>
    </div>
</div>
<script>
    (function () {
        'use strict'
        var forms = document.querySelectorAll('.needs-validation')
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    }
                    form.classList.add('was-validated')
                }, false)
            })
    })()
</script>
</body>
</html>
"""
    with open(f"{model_template_folder_path}/create_{model_tablename}.html", "w") as f:
        f.write(create_template_content)

    '''
    =====================================================
    # Post Update Model Route
    # Generate update template
    =====================================================
    '''
    update_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Update {model_name.capitalize()}</title>
    <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<div style="width: 100%" class="d-flex gap-3 bg-dark text-light">
    {menu_bar}
    <div style="width: 78%" class="d-flex flex-column gap-2 p-3">
    <h1>Update {model_name.capitalize()}</h1>
    <form action="{path_conversion("/admin/"+model_tablename+"/update/{{ id }}")}" method="post" class="needs-validation" novalidate>
        <div class="row">
"""
    for i, field in enumerate(SchemaUpdate.__fields__):
        update_template_content += f'''
            <div class="col-md-6 mb-3">
                <label for="{field}" class="form-label">{field.capitalize()}</label>
                <input type="text" class="form-control" id="{field}" name="{field}" value="{{{{ model.{field} }}}}" placeholder="{field.capitalize()}" >
                <div class="invalid-feedback">
                    Please provide a valid {field}.
                </div>
            </div>
'''
        if (i + 1) % 2 == 0:
            update_template_content += '</div><div class="row">'
    update_template_content += """
        </div>
        <button type="submit" class="btn btn-primary">Update</button>
    </form>
    </div>
</div>
<script>
    (function () {
        'use strict'
        var forms = document.querySelectorAll('.needs-validation')
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    }
                    form.classList.add('was-validated')
                }, false)
            })
    })()
</script>
</body>
</html>
"""
    with open(f"{model_template_folder_path}/update_{model_tablename}.html", "w") as f:
        f.write(update_template_content)

    '''
    =====================================================
    # Post View Model Route
    # Generate view template
    =====================================================
    '''
    view_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>View {model_name.capitalize()}</title>
     <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
</head>
<body>
<div style="width: 100%" class="d-flex gap-3 bg-dark text-light">
    {menu_bar}
    <div style="width: 80%" class="d-flex flex-column gap-2  p-3">
    <h1>View {model_name.capitalize()}</h1>
    <div class="table-responsive">
    <table class="table table-striped table-hover table-bordered table-responsive table-condensed table-sm  table-dark ">
        <tr>
"""
    for field in fields:
        view_template_content += f'<th>{field.capitalize()}</th>\n'
    view_template_content += """
        </tr>
        <tr>
"""
    for field in fields:
        view_template_content += f'<td>{{{{ model.{field} }}}}</td>\n'
    view_template_content += """
        </tr>
    </table>
    </div>
    </div>
    </div>
</body>
</html>
"""
    with open(f"{model_template_folder_path}/view_{model_tablename}.html", "w") as f:
        f.write(view_template_content)

    '''
    =====================================================
    # Post List Model Route
    # Generate list template
    =====================================================
    '''
    list_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>List {model_name.capitalize()}s</title>
     <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
</head>
<body class="bg-dark text-light">
<div style="width: 100%" class="d-flex gap-3">
    {menu_bar}
    <div style="width: 80%" class="d-flex flex-column gap-2 p-3">
    <h1>List {model_name.capitalize()}s</h1>

    <a href="{path_conversion("/admin/" + model_tablename + "/create")}"><button type="button" class="btn btn-primary">Create New {model_name.capitalize()}</button></a>
    <div class="table-responsive">
    <table  class=" table table-striped table-hover table-bordered table-responsive table-condensed table-sm  table-dark "> 
        <tr>
"""
    for field in fields:
        list_template_content += f'<th>{field.capitalize()}</th>\n'
    list_template_content += """
            <th>Actions</th>
        </tr>
        {% for model in models %}
        <tr>
"""
    for field in fields:
        list_template_content += f'<td>{{{{ model.{field} }}}}</td>\n'
    list_template_content += f"""
            <td class="d-flex gap-2">
                <form action="{path_conversion("/admin/"+model_tablename+"/update/{{ model.id }}")}" method="get" style="display:inline;">
                <button type="submit" class="btn btn-primary"><i class="bi bi-pencil-square"></i></button>
                </form>
                <form action="{path_conversion("/admin/"+model_tablename+"/delete/{{model.id}}")}" method="post" style="display:inline;">
                  <button type="submit" class="btn btn-danger"><i class="bi bi-trash"></i></button>
                </form>
                <form action="{path_conversion("/admin/"+model_tablename+"/{{model.id}}")}" method="get" style="display:inline;">
                <button type="submit" class="btn btn-info"><i class="bi bi-box-arrow-up-right"></i></button>
                </form>
            </td>
        </tr>
        {{% endfor %}}
    </table>
        </div>
    </div>
    </div>
</body>
</html>
"""
    with open(f"{model_template_folder_path}/list_{model_tablename}.html", "w") as f:
        f.write(list_template_content)

    '''
    =====================================================
    # Assign Roles Route
    # Generate assign_roles template
    =====================================================
    '''
    assign_roles_template_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Assign Roles to Routes</title>
    <link rel="stylesheet" href="{path_conversion("/public/style.css")}"></link>
    <script>
        function updateAssignedRoutes() {{
            var roleSelect = document.getElementById('role');
            var selectedRole = roleSelect.value;
            var assignedRoutes = JSON.parse('{{{{ assigned_routes | tojson | safe }}}}');
            var checkboxes = document.querySelectorAll('input[type="checkbox"].route-checkbox');

            checkboxes.forEach(function (checkbox) {{
                var route = checkbox.value.split('|')[0];
                var method = checkbox.value.split('|')[1];
                if (assignedRoutes[selectedRole] && assignedRoutes[selectedRole][route] && assignedRoutes[selectedRole][route].includes(method)) {{
                    checkbox.checked = true;
                }} else {{
                    checkbox.checked = false;
                }}
            }});

            updateCategoryCheckboxes();
        }}

        function toggleCategory(category) {{
            var checkboxes = document.querySelectorAll('input[type="checkbox"].' + category);
            var categoryCheckbox = document.getElementById('category-' + category);
            checkboxes.forEach(function (checkbox) {{
                checkbox.checked = categoryCheckbox.checked;
            }});
        }}

        function updateCategoryCheckboxes() {{
            var categories = document.querySelectorAll('[id^="category-"]');
            categories.forEach(function (categoryCheckbox) {{
                var category = categoryCheckbox.id.split('-')[1];
                var checkboxes = document.querySelectorAll('input[type="checkbox"].' + category);
                var allChecked = true;
                var noneChecked = true;
                checkboxes.forEach(function (checkbox) {{
                    if (!checkbox.checked) {{
                        allChecked = false;
                    }} else {{
                        noneChecked = false;
                    }}
                }});
                categoryCheckbox.checked = allChecked;
                categoryCheckbox.indeterminate = !allChecked && !noneChecked;
            }});
        }}

        document.addEventListener('DOMContentLoaded', function () {{
            var roleSelect = document.getElementById('role');
            var initialRole = roleSelect.value;

            roleSelect.addEventListener('change', function() {{
                if (!confirm('Do you want to save the changes before switching roles?')) {{
                    roleSelect.value = initialRole;
                }} else {{
                    updateAssignedRoutes();
                    initialRole = roleSelect.value;
                }}
            }});

            updateAssignedRoutes();
        }});
    </script>

    <style>
      .accordion-button {{
        background-color: #212529 !important; /* Dark background */
        color: #f8f9fa !important; /* Light text */
        border: 1px solid #444 !important;
      }}
      .accordion-button:not(.collapsed) {{
        background-color: #343a40 !important;
      }}
      .accordion-body {{
        background-color: #212529 !important;
        color: #f8f9fa !important;
      }}
      .accordion-item {{
        background-color: #343a40 !important;
        border: 1px solid #444 !important;
      }}
    </style>
</head>
<body>
<div style="width: 100%" class="d-flex bg-dark text-light">
     {menu_bar}
     <div style="width: 80%" class="d-flex flex-column gap-2 p-3 ">
    <h1>Assign Roles to Routes</h1>
    <form method="post" action="/admin/settings/assign-roles" class="d-flex flex-column gap-2">
        <div class="d-flex justify-content-between align-items-end gap-2 sticky-top bg-dark pt-1 pb-4" style="top: 0;">
            <div class="flex-grow-1">
                <label for="role">Select Role:</label>
                <select id="role" name="role" class="form-select">
                    {{% for role in roles %}}
                    <option value="{{{{ role.id }}}}">{{{{ role.name }}}}</option>
                    {{% endfor %}}
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Save</button>
        </div>
        <h2>Routes</h2>
        <div class="accordion accordion-flush" id="routesAccordion">
            {{% for tag, routes in categorized_routes|dictsort %}}
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading-{{{{ tag }}}}">
                    <button class="accordion-button collapsed " type="button" data-bs-toggle="collapse" data-bs-target="#collapse-{{{{ tag }}}}" aria-expanded="false" aria-controls="collapse-{{{{ tag }}}}">
                        <input type="checkbox" id="category-{{{{ tag }}}}" onclick="toggleCategory('{{{{ tag }}}}')">
                        <label for="category-{{{{ tag }}}}" class="">{{{{ tag }}}}</label>
                    </button>
                </h2>
                <div id="collapse-{{{{ tag }}}}" class="accordion-collapse collapse" aria-labelledby="heading-{{{{ tag }}}}" data-bs-parent="#routesAccordion">
                    <div class="accordion-body ">
                        {{% for route in routes %}}
                        <div>
                            <input type="checkbox" id="{{{{ route.path }}}}-{{{{ route.method }}}}" name="routes"
                                value="{{{{ route.path }}}}|{{{{ route.method }}}}" class="route-checkbox {{{{ tag }}}}">
                            <label for="{{{{ route.path }}}}-{{{{ route.method }}}}" class="">{{{{ route.method }}}} {{{{ route.path }}}}</label>
                        </div>
                        {{% endfor %}}
                    </div>
                </div>
            </div>
            {{% endfor %}}
        </div>
    </form>
    </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
    with open(f"{settings_template_folder_path}/assign_roles.html", "w") as f:
        f.write(assign_roles_template_content)
