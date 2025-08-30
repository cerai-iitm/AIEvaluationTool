# @author: Sudarsun S
# @date: 2025-06-10
# @version: 1.0.0
# @description: This module defines the Language class, which represents an Indian language with its name and code.

class Language:

    autodetect:int = 1  # Default language ID for "Auto" identification of language.

    def __init__(self, name: str, code: int):
        self.name = name
        self.code = code

    def __repr__(self):
        # Developer-friendly representation of the object
        return f"Language(name={self.name}, code={self.code})"

    def __str__(self):
        # User-friendly string representation of the object
        return f"{self.name} ({self.code})"

    def __eq__(self, other):
        if isinstance(other, Language):
            return self.name == other.name and self.code == other.code
        
        return False
    def __hash__(self):
        return hash((self.name, self.code))
