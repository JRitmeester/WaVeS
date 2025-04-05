from typing import List
from pydantic import ValidationError

class ConfigValidationError(Exception):
    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        self.message = self._format_error_message()

    def _format_error_message(self) -> str:
        errors = []
        for error in self.validation_error.errors():
            field = error['loc'][0]  # Get the main field (e.g., 'mappings', 'device', 'settings')
            if len(error['loc']) > 1:
                subfield = error['loc'][1]  # Get the subfield if it exists
                field = f"{field}.{subfield}"
            
            error_type = error['type']
            
            if error_type == 'int_parsing':
                errors.append(f"Invalid value in {field}. Expected a number.")
            elif error_type == 'missing':
                errors.append(f"Missing required field: {field}")
            elif error_type == 'bool_parsing':
                errors.append(f"Invalid value in {field}. Expected 'true' or 'false'.")
            else:
                errors.append(f"Invalid value in {field}: {error['msg']}")
        
        return "\n".join(errors)

    def __str__(self) -> str:
        return self.message 
    
class ConfigFileEmptyError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message

