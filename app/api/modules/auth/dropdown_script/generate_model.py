from pathlib import Path
from typing import List

def generate_models_file(hierarchy_config: dict, output_path: str = None):
    """Generate models.py with implicit ID fields referenced in foreign keys"""
    
    header = """\
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database.base_model import Base

"""
    
    class_template = """\
class {class_name}(Base):
    __tablename__ = "{table_name}"

    name: Mapped[str] = mapped_column(String{unique}, index=True){foreign_key}

    # Relationships
{relationships}
    __allowed__ = True  
"""
    
    relationship_template = "    {rel_name}: Mapped[list[\"{target_class}\"]] = relationship(\"{target_class}\", back_populates=\"{back_populates}\")"
    parent_relationship_template = "    {rel_name}: Mapped[\"{target_class}\"] = relationship(\"{target_class}\", back_populates=\"{back_populates}\")"
    
    classes = []
    relationships = {}
    
    # First pass to collect relationship info
    for i, level in enumerate(hierarchy_config["levels"]):
        class_name = level["name"].title()
        table_name = level["endpoint"]
        unique = ", unique=True" if level.get("unique", False) else ""
        
        classes.append({
            "class_name": class_name,
            "table_name": table_name,
            "unique": unique,
            "parent_field": level["parent_field"],
            "has_children": i < len(hierarchy_config["levels"]) - 1
        })
        
        if level["parent_field"] and level["parent_field"].endswith('_id'):
            parent_class = hierarchy_config["levels"][i-1]["name"].title()
            relationships[class_name] = {
                "parent": {
                    "rel_name": parent_class.lower(),
                    "target_class": parent_class,
                    "back_populates": table_name
                }
            }
    
    # Second pass to generate class definitions
    class_definitions = []
    for i, cls in enumerate(classes):
        foreign_key = ""
        rels = []
        
        # Add parent relationship if exists
        if cls["parent_field"] and cls["parent_field"].endswith('_id'):
            parent_table = hierarchy_config["levels"][i-1]["endpoint"]
            foreign_key = f"\n    {cls['parent_field']}: Mapped[int] = mapped_column(ForeignKey(\"{parent_table}.id\"))"
            
            if cls["class_name"] in relationships:
                rels.append(parent_relationship_template.format(
                    **relationships[cls["class_name"]]["parent"]
                ))
        
        # Add children relationship if exists
        if cls["has_children"]:
            child_class = hierarchy_config["levels"][i+1]["name"].title()
            child_table = hierarchy_config["levels"][i+1]["endpoint"]
            rels.append(relationship_template.format(
                rel_name=child_table,
                target_class=child_class,
                back_populates=cls["class_name"].lower()
            ))
        
        class_def = class_template.format(
            class_name=cls["class_name"],
            table_name=cls["table_name"],
            unique=cls["unique"],
            foreign_key=foreign_key,
            relationships="\n".join(rels) if rels else ""
        )
        class_definitions.append(class_def)
    
    # Create folder name by combining all class names
    folder_name = "_".join([cls["class_name"].lower() for cls in classes])
    output_dir = Path("Dropdown_Models") / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set output path if not provided
    if output_path is None:
        output_path = output_dir / "models.py"
    else:
        output_path = Path(output_path)
    
    # Write to file
    with open(output_path, "w") as f:
        f.write(header)
        f.write("\n\n".join(class_definitions))
    
    print(f"Successfully generated models at {output_path}")

# Configuration
config = {
    "levels": [
        {
            "name": "country",
            "endpoint": "countries",
            "parent_field": None,
            "excel_column": "Country",
            "unique": True
        },
        {
            "name": "state",
            "endpoint": "states",
            "parent_field": "country_id",
            "excel_column": "State",
            "unique": False
        },
        {
            "name": "district",
            "endpoint": "districts",
            "parent_field": "state_id",
            "excel_column": "District",
            "unique": False
        },
       
    ]
}

# Generate the models
generate_models_file(config)