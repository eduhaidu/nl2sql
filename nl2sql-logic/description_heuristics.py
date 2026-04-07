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
    
    def guess_table_role(self, table_name, columns):
        import re

        table_lower = table_name.lower()
        column_names = [c.get('name', '').lower() for c in columns if 'name' in c]
        pk_columns = [c.get('name', '').lower() for c in columns if c.get('primary_key')]

        foreign_keys = []
        for col in columns:
            if 'foreign_keys' in col and isinstance(col['foreign_keys'], list):
                foreign_keys.extend(col['foreign_keys'])

        # Pattern sets
        detail_name_patterns = [r'line', r'detail', r'item', r'entry', r'entries']
        header_name_patterns = [r'order', r'invoice', r'sale', r'purchase', r'transaction']
        lookup_name_patterns = [r'type', r'status', r'category', r'code', r'lookup', r'reference']

        header_cols = {'customer_id', 'client_id', 'user_id', 'order_date', 'invoice_date', 'status', 'total', 'subtotal'}
        detail_cols = {'product_id', 'item_id', 'sku', 'quantity', 'qty', 'unit_price', 'line_total', 'price'}
        lookup_cols = {'code', 'name', 'label', 'description'}

        # Scores for each role
        scores = {
            'header': 0.0,
            'detail': 0.0,
            'lookup': 0.0,
            'bridge': 0.0,
            'unknown': 0.0
        }
        reasons = []

        # Name-based hints
        if any(re.search(p, table_lower) for p in detail_name_patterns):
            scores['detail'] += 0.45
            reasons.append('table name resembles detail/line-item entity')

        if any(re.search(p, table_lower) for p in header_name_patterns):
            scores['header'] += 0.25
            reasons.append('table name resembles document/header entity')

        if any(re.search(p, table_lower) for p in lookup_name_patterns):
            scores['lookup'] += 0.35
            reasons.append('table name resembles lookup/reference entity')

        # Column-content hints
        column_set = set(column_names)
        if column_set.intersection(header_cols):
            scores['header'] += 0.35
            reasons.append('contains header-style columns (customer/date/status/total)')

        if column_set.intersection(detail_cols):
            scores['detail'] += 0.40
            reasons.append('contains detail-style columns (product/qty/price)')

        # Lookup: small table + code/name style columns + low transactional signals
        if len(column_names) <= 6 and column_set.intersection(lookup_cols):
            scores['lookup'] += 0.35
            reasons.append('small schema with code/name style columns suggests lookup table')

        # Bridge table: many foreign keys, very few non-key attributes
        fk_count = len(foreign_keys)
        non_key_columns = [c for c in column_names if c not in pk_columns]
        if fk_count >= 2 and len(non_key_columns) <= 3:
            scores['bridge'] += 0.55
            reasons.append('multiple foreign keys with few non-key attributes suggest bridge table')

        # Detail tables usually reference parent/header
        if fk_count >= 1 and scores['detail'] > 0:
            scores['detail'] += 0.15
            reasons.append('foreign key linkage supports detail-table role')

        # Reduce header score if strongly detail-like
        if scores['detail'] >= 0.55 and scores['header'] > 0:
            scores['header'] -= 0.10

        # Choose best role
        best_role = max(scores, key=scores.get)
        confidence = round(max(0.0, min(1.0, scores[best_role])), 2)

        if confidence < 0.3:
            best_role = 'unknown'
            confidence = 0.3
            reasons.append('insufficient discriminative schema signals')

        role_labels = {
            'header': 'Header/master table',
            'detail': 'Detail/line-item table',
            'lookup': 'Lookup/reference table',
            'bridge': 'Bridge/association table',
            'unknown': 'General entity table'
        }

        return {
            'role': best_role,
            'label': role_labels[best_role],
            'confidence': confidence,
            'reason': '; '.join(reasons[:3]) if reasons else 'role inferred from naming and schema shape'
        }
        
    def enrich_schema_with_descriptions(self, schema_info):
        enriched_schema = {}
        for table_name, columns in schema_info.items():
            table_desc = self.guess_table_description(table_name)
            role_info = self.guess_table_role(table_name, columns)
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
                'role': role_info['role'],
                'role_label': role_info['label'],
                'role_confidence': role_info['confidence'],
                'role_reason': role_info['reason'],
                'columns': enriched_columns
            }
        return enriched_schema