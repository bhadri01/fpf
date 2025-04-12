import os
import sys
import asyncio
import pandas as pd
import requests
import json
from typing import List, Any, Dict, Optional, Union

# Configuration
EXCEL_FILE_PATH = "/app/app/api/modules/auth/dropdown_script/files/India_States_and_Districts.xlsx"
BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5ZTNjNjc2LWI5MDAtNDRhYi05YzczLTI4N2ExMWE4ZDExYiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3NDQxMDQxODR9.OftqAZQAjWz3sCyLDpc6UOHu9q7svLx48hzSbqs-5dQ"
}

class DynamicHierarchyProcessor:
    def __init__(self, hierarchy_config: Dict):
        self.config = hierarchy_config
        self.df = None
        self.validate_config()
        
    def validate_config(self):
        """Ensure the configuration is valid"""
        if not isinstance(self.config, dict):
            raise ValueError("Config must be a dictionary")
            
        if "levels" not in self.config or not isinstance(self.config["levels"], list):
            raise ValueError("Config must contain 'levels' list")
            
        for i, level in enumerate(self.config["levels"]):
            required_fields = ["name", "endpoint", "parent_field", "excel_column"]
            for field in required_fields:
                if field not in level:
                    raise ValueError(f"Level {i} missing required field: {field}")
                    
            if i == 0 and level["parent_field"] is not None:
                raise ValueError("First level must have parent_field=None")
                
            if i > 0 and level["parent_field"] is None:
                raise ValueError(f"Level {i} must specify a parent_field")

    @staticmethod
    def make_api_call(method: str, url: str, json_data: Any = None, params: Dict = None) -> Any:
        """Reliable API call with comprehensive error handling"""
        try:
            print(f"\n🔹 API Call: {method} {url}")
            if params:
                print(f"🔹 Params: {json.dumps(params, indent=2)}")
            if json_data:
                print(f"🔹 Request Body: {json.dumps(json_data, indent=2)}")
            
            response = requests.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=HEADERS,
                timeout=30
            )
            
            print(f"🔹 Response Status: {response.status_code}")
            if response.text:
                print(f"🔹 Response Body: {response.text[:500]}")
            
            if response.status_code == 409:
                print("ℹ️ Record already exists")
                return None
                
            if response.status_code not in [200, 201]:
                print(f"❌ API Error {response.status_code}")
                return None
                
            return response.json()
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
            return None

    @staticmethod
    async def get_existing_records(endpoint: str, filters: str) -> List[Dict]:
        """Get records with proper pagination and error handling"""
        all_records = []
        page = 1
        size = 100
        
        while True:
            params = {
                "filters": filters,
                "page": page,
                "size": size
            }
            
            response_data = DynamicHierarchyProcessor.make_api_call(
                "GET",
                f"{BASE_URL}/{endpoint}",
                params=params
            )
            
            if not response_data or not isinstance(response_data, dict) or not response_data.get('items'):
                break
                
            all_records.extend(response_data['items'])
            
            if len(response_data['items']) < size:
                break
                
            page += 1
            
        return all_records

    async def process_level(self, level_index: int, parent_info: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Process a single level in the hierarchy
        Returns mapping of names to IDs for the processed level
        
        Args:
            level_index: Index of the level in the hierarchy
            parent_info: Dictionary containing:
                - 'id': The parent ID to use
                - 'name': The parent name to filter by
                - 'column': The parent column name in Excel
        """
        try:
            level_config = self.config["levels"][level_index]
            is_top_level = (level_index == 0)
            
            print(f"\n{'🌍' if is_top_level else '🏙️'} Processing level: {level_config['name']}")
            
            # For top level with predefined name
            if is_top_level and "root_name" in self.config:
                level_name = self.config["root_name"]
                print(f"🔹 Using predefined {level_config['name']}: {level_name}")
                
                # Check if exists
                filter_str = f'{{"name":{{"$eq":"{level_name}"}}}}'
                existing_records = await self.get_existing_records(level_config["endpoint"], filter_str)
                
                if existing_records:
                    print(f"✔️ {level_config['name'].title()} exists with ID: {existing_records[0]['id']}")
                    return {level_name.lower(): existing_records[0]['id']}
                
                # Create if not exists
                print(f"🆕 Creating {level_config['name']}...")
                create_data = [{"name": level_name}]
                response = self.make_api_call(
                    "POST",
                    f"{BASE_URL}/{level_config['endpoint']}",
                    json_data=create_data
                )
                
                if not response:
                    raise Exception(f"Failed to create {level_config['name']}")
                
                # Verify creation
                await asyncio.sleep(1)
                existing_records = await self.get_existing_records(level_config["endpoint"], filter_str)
                
                if not existing_records:
                    raise Exception(f"Verification failed for {level_config['name']}")
                    
                return {level_name.lower(): existing_records[0]['id']}
            
            # For non-top levels
            if self.df is None or not isinstance(self.df, pd.DataFrame):
                raise ValueError("DataFrame not initialized")
            if self.df.empty:
                raise ValueError("DataFrame is empty")
            if level_config["excel_column"] not in self.df.columns:
                raise ValueError(f"Column '{level_config['excel_column']}' not found in Excel data")
            if parent_info is None:
                raise ValueError("Parent info is required for non-top levels")
            
            parent_name = parent_info['name']
            parent_value = parent_info['id']
            parent_column = parent_info['column']
            
            print(f"🔹 Processing for parent {parent_name} (ID: {parent_value})")
            
            # Get unique names for this level under the specific parent
            filtered_df = self.df[
                (self.df[parent_column].astype(str).str.lower().str.strip() == parent_name.lower().strip()) &
                (self.df[level_config["excel_column"]].notna())
            ]
            
            # More robust name cleaning
            unique_names = filtered_df[level_config["excel_column"]].astype(str).apply(
                lambda x: x.strip() if pd.notna(x) else x
            ).unique().tolist()
            
            # Remove any remaining NaN/None values
            unique_names = [name for name in unique_names if name and str(name).lower() != 'nan']
            
            if not unique_names:
                print(f"⚠️ Warning: No {level_config['name']} records found for {parent_name}")
                return {}
            
            print(f"ℹ️ Found {len(unique_names)} {level_config['name']} records for {parent_name}")
            print(f"🔹 Sample {level_config['name']} names: {unique_names[:10]}")
            
            # Check existing records
            if level_config["parent_field"]:
                filter_str = f'{{"{level_config["parent_field"]}":{{"$eq":"{parent_value}"}}}}'
            else:
                filter_str = '{}'
                
            existing_records = await self.get_existing_records(level_config["endpoint"], filter_str)
            
            # More robust comparison
            existing_map = {}
            for r in existing_records:
                clean_name = str(r['name']).strip().lower()
                existing_map[clean_name] = r['id']
            
            # Prepare records to create
            records_to_create = []
            for name in unique_names:
                clean_name = str(name).strip().lower()
                if clean_name not in existing_map:
                    record_data = {"name": str(name).strip()}
                    if level_config["parent_field"]:
                        record_data[level_config["parent_field"]] = parent_value
                    records_to_create.append(record_data)
            
            # Create new records in batches to avoid timeout
            batch_size = 50
            for i in range(0, len(records_to_create), batch_size):
                batch = records_to_create[i:i + batch_size]
                print(f"🆕 Creating batch {i//batch_size + 1} with {len(batch)} {level_config['name']} records")
                response = self.make_api_call(
                    "POST",
                    f"{BASE_URL}/{level_config['endpoint']}",
                    json_data=batch
                )
                
                if response:
                    # Small delay between batches
                    await asyncio.sleep(0.5)
            
            # Final refresh of existing records
            existing_records = await self.get_existing_records(level_config["endpoint"], filter_str)
            existing_map = {str(r['name']).strip().lower(): r['id'] for r in existing_records}
            
            # Return mapping only for the names we actually have in our data
            result_map = {}
            for name in unique_names:
                clean_name = str(name).strip().lower()
                if clean_name in existing_map:
                    result_map[clean_name] = existing_map[clean_name]
                else:
                    print(f"⚠️ Warning: Failed to find/create {level_config['name']}: {name}")
            
            print(f"ℹ️ Total {level_config['name']} records processed: {len(result_map)}")
            return result_map
        
        except Exception as e:
            print(f"❌ Error processing level {level_config['name']}: {str(e)}")
            if hasattr(self, 'df') and self.df is not None:
                print(f"🔹 DataFrame columns: {self.df.columns.tolist()}")
                print(f"🔹 Parent info: {parent_info}")
                print(f"🔹 Sample data for troubleshooting:")
                print(self.df.head())
            raise

    async def process_hierarchy_recursive(self, df: pd.DataFrame, level_index: int = 0, parent_info: Dict = None, parent_map: Dict = None):
        """Recursively process the hierarchy levels"""
        if level_index >= len(self.config["levels"]):
            return
        
        level_config = self.config["levels"][level_index]
        
        # Process current level
        if level_index == 0:
            print(f"\n🔹 Processing {level_config['name']} level...")
            current_map = await self.process_level(level_index, None)
        else:
            print(f"\n🔹 Processing {level_config['name']} level for parent {parent_info['name']}...")
            current_map = await self.process_level(level_index, parent_info)
        
        if not current_map:
            print(f"⚠️ Warning: No {level_config['name']} records processed")
            return
        
        # If this is not the last level, process children
        if level_index < len(self.config["levels"]) - 1:
            next_level_config = self.config["levels"][level_index + 1]
            
            # Get unique parent names for the next level
            parent_names = self.df[level_config["excel_column"]].astype(str).str.strip().unique().tolist()
            parent_names = [name for name in parent_names if name and str(name).lower() != 'nan']
            
            for parent_name in parent_names:
                clean_parent_name = parent_name.strip().lower()
                
                if clean_parent_name not in current_map:
                    print(f"⚠️ Warning: Parent {parent_name} not found in {level_config['name']} records")
                    continue
                
                parent_id = current_map[clean_parent_name]
                
                # Process next level with current parent info
                await self.process_hierarchy_recursive(
                    df,
                    level_index + 1,
                    {
                        'id': parent_id,
                        'name': parent_name,
                        'column': level_config["excel_column"]
                    },
                    current_map
                )

    async def process_hierarchy(self, df: pd.DataFrame):
        """Process the entire hierarchy with proper parent-child relationships"""
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("Invalid DataFrame provided")
        if df.empty:
            raise ValueError("DataFrame is empty")
            
        self.df = df.copy()
        
        print("\n" + "="*50)
        print(f"🏁 Starting {self.config.get('root_name', 'Hierarchical')} Data Import")
        print("="*50)
        
        try:
            # Data validation before processing
            print("\n🔹 Data Validation:")
            print(f"Total rows: {len(df)}")
            print("Null values per column:")
            print(df.isna().sum())
            
            # Clean the dataframe
            for level in self.config["levels"]:
                if level["excel_column"] in df.columns:
                    self.df[level["excel_column"]] = self.df[level["excel_column"]].astype(str).str.strip()
            
            # Verify all required columns exist
            for level in self.config["levels"]:
                if level["excel_column"] not in self.df.columns:
                    raise ValueError(f"Column '{level['excel_column']}' not found in Excel data")
            
            # Start recursive processing
            await self.process_hierarchy_recursive(self.df)
            
            print("\n" + "="*50)
            print("🎉 Data Import Completed Successfully")
            print("="*50)
            
        except Exception as e:
            print("\n" + "❌"*50)
            print(f"Processing Failed: {str(e)}")
            print("❌"*50)
            raise
        finally:
            self.df = None

if __name__ == "__main__":
    try:
        print("\n" + "🚀"*50)
        print("🚀 Dynamic Hierarchical Data Import Script")
        print("🚀"*50)
        
        # Example configuration for 4 levels
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
                 

                # Add more levels as needed
            ],
            "root_name": "India"
        }
        
        # Load data
        try:
            df = pd.read_excel(EXCEL_FILE_PATH)
            print(f"\n🔹 Loaded Excel data with {len(df)} rows")
            print(f"🔹 Columns: {df.columns.tolist()}")
            print(f"🔹 First 5 rows:\n{df.head()}")
            
            # Additional data validation
            print("\n🔹 Checking data quality:")
            for level in config["levels"]:
                if level["excel_column"] in df.columns:
                    print(f"{level['name'].title()}:")
                    print(f"  - Unique values: {df[level['excel_column']].nunique()}")
                    print(f"  - Null values: {df[level['excel_column']].isna().sum()}")
                    print(f"  - Sample: {df[level['excel_column']].dropna().sample(3).tolist()}")
            
        except Exception as e:
            print(f"❌ Failed to load Excel file: {str(e)}")
            sys.exit(1)
        
        # Create processor and run
        processor = DynamicHierarchyProcessor(config)
        asyncio.run(processor.process_hierarchy(df))
        
        print("\n" + "✅"*50)
        print("✅ Script Completed Successfully")
        print("✅"*50)
        
    except KeyboardInterrupt:
        print("\n🛑 Script Interrupted by User")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal Error: {str(e)}")
        sys.exit(1)