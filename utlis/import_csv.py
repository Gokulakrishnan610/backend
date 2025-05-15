from import_export import resources
from import_export.formats import base_formats
from io import TextIOWrapper
import tablib

def import_from_csv(resource_class, file, dry_run=False):
    try:
        csv_format = base_formats.CSV()
        dataset = csv_format.create_dataset(TextIOWrapper(file, encoding='utf-8'))
        resource = resource_class()
        
        result = resource.import_data(dataset, dry_run=dry_run, raise_errors=False)
        
        errors = []
        
        for row in result.invalid_rows:
            errors.append({
                'row': row.number,
                'errors': row.error_dict,
                'values': row.values
            })
        
        if result.has_errors():
            for row_idx, row_errors in result.row_errors():
                if row_idx < len(dataset.dict):
                    row_values = dataset.dict[row_idx]
                else:
                    row_values = "Row data not available"
                
                for error in row_errors:
                    errors.append({
                        'row': row_idx + 1,
                        'errors': str(error.error),
                        'values': row_values
                    })
        
        return result, errors
        
    except Exception as e:
        import traceback
        print(f"Error during import processing: {str(e)}")
        print(traceback.format_exc())
        raise