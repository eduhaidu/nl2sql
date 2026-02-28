class DescriptionHeuristics:
    def __init__(self):
        self.table_patterns = {
            r'.*order.*': 'Transaction or order records',
            r'.*customer.*|.*client.*|.*user.*': 'Customer or user account information',
            r'.*product.*|.*item.*': 'Product catalog information',
            r'.*invoice.*|.*payment.*': 'Payment and billing records',
            r'.*employee.*|.*staff.*': 'Employee or staff information',
            r'.*address.*': 'Address or location data',
            r'.*log.*|.*audit.*': 'Activity logs or audit trail'
        }

        self.column_patterns = {
            r'.*_id$|^id$': 'Unique identifier',
            r'.*_at$': 'Timestamp',
            r'.*_date$|^date$': 'Date field',
            r'.*name.*': 'Name or label',
            r'.*email.*': 'Email address',
            r'.*phone.*|.*tel.*': 'Phone number',
            r'.*status.*': 'Status or state indicator',
            r'.*price.*|.*amount.*|.*total.*': 'Monetary value',
            r'.*qty.*|.*quantity.*': 'Quantity or count',
            r'.*description.*|.*desc.*': 'Detailed description text'
        }

    def guess_table_description(self, table_name):
        import re
        table_lower = table_name.lower()

        for pattern, description in self.table_patterns.items():
            if re.match(pattern, table_lower):
                return description
        
        return f"Storage for {table_name.replace('_', ' ')} data"
    
    def guess_column_description(self, column_name, column_type=None):
        import re
        column_lower = column_name.lower()

        for pattern, description in self.column_patterns.items():
            if re.match(pattern, column_lower):
                return description

        type_lower = column_type.lower() if column_type else ""
        if "timestamp" in type_lower or "date" in type_lower or "datetime" in type_lower:
            return "Date or time information"
        elif "int" in type_lower or "numeric" in type_lower or "decimal" in type_lower:
            return "Numeric value"
        elif "char" in type_lower or "text" in type_lower or "string" in type_lower or "varchar" in type_lower:
            return "Textual information"
        
        return f"Data field for {column_name.replace('_', ' ')}"
    
    def enrich_schema_with_descriptions(self, schema_info):
        enriched_schema = {}
        for table_name, columns in schema_info.items():
            table_desc = self.guess_table_description(table_name)
            enriched_columns = []
            for column in columns:
                # Skip entries that aren't column definitions (e.g., foreign_keys)
                if 'name' not in column:
                    enriched_columns.append(column)  # Keep as-is
                    continue
                    
                col_name = column['name']
                col_type = column.get('type', '')
                col_desc = self.guess_column_description(col_name, col_type)
                enriched_columns.append({
                    'name': col_name,
                    'type': col_type,
                    'description': col_desc,
                    'nullable': column.get('nullable'),
                    'primary_key': column.get('primary_key')
                })
            enriched_schema[table_name] = {
                'description': table_desc,
                'columns': enriched_columns
            }
        return enriched_schema