import unit_tests
from schema_processor import SchemaProcessor
class TestSchemaProcessor(unit_tests.UnitTests):
    def test_schema_processor(self):
        schema_processor = SchemaProcessor()
        self.assertIsNotNone(schema_processor)

    def test_process_schema(self):
        schema_processor = SchemaProcessor()
        processed_schema = schema_processor.process_schema("CREATE TABLE sales (id INT, amount FLOAT, date DATE);")
        self.assertIsNotNone(processed_schema)

if __name__ == '__main__':    unit_tests.main()