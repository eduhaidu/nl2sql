from sqlalchemy import create_engine, MetaData
from sentence_transformers import SentenceTransformer, util

class SchemaProcessor:
    def __init__(self, db_url='sqlite:///example.db'):
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
    
    def process_schema(self):
        schema_info = {}
        for table_name, table in self.metadata.tables.items():
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key
                })
            schema_info[table_name] = columns
            foreign_keys = []
            for fk in table.foreign_keys:
                foreign_keys.append({
                    'column': fk.parent.name,
                    'references': str(fk.column)
                })
            if foreign_keys:
                schema_info[table_name].append({'foreign_keys': foreign_keys})
        return schema_info
    
    
    def format_schema_for_model(self, schema_info):
        formatted_schema = ""
        for table_name, columns in schema_info.items():
            formatted_schema += f"Table: {table_name}\n"
            for column in columns:
                if 'name' in column:
                    formatted_schema += f"  Column: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Primary Key: {column['primary_key']}\n"
            formatted_schema += "\n"
        return formatted_schema.strip()
        
    
    def print_schema_info(self, schema_info):
        for table_name, columns in schema_info.items():
            print(f"Table: {table_name}")
            for column in columns:
                print(f"  Column: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Primary Key: {column['primary_key']}")
            print()

    def get_schema_keys(self):
        return list(self.metadata.tables.keys())
    
    def write_schema_to_file(self, schema_info, file_path='schema_info.txt'):
        with open(file_path, 'w') as f:
            if file_path.endswith('.json'):
                import json
                json.dump(schema_info, f, indent=4)
            else:
                for table_name, columns in schema_info.items():
                    f.write(f"Table: {table_name}\n")
                    for column in columns:
                        f.write(f"  Column: {column['name']}, Type: {column['type']}, Nullable: {column['nullable']}, Primary Key: {column['primary_key']}\n")
                    f.write("\n")