from collections import OrderedDict
from typing import List, Dict

from .primitive import Primitive
from .structure import Structure
from .tag import Tag

class Schema(object):

    @classmethod
    def generate_from_file(cls, file_path:str) -> 'Schema':
        return self.generate_from_files([file_path])

    @classmethod
    def generate_from_files(cls, file_paths:List[str]) -> 'Schema':
        schema = cls()
        for file_path in file_paths:
            schema._append_file_definition(file_path)
        return schema
    
    def __init__(self):
        self.filepaths:List[str] = []
        self.structures:Dict[Structure] = OrderedDict()
        self.primitives:Dict[Primitive] = OrderedDict()
        self.tags:Dict[Tag] = OrderedDict()
    
    def _append_file_definition(self, filepath) -> None:
        self.filepaths.append(filepath)
        with open(filepath, 'r') as file_reader:
            current_element = None
            for line_raw in file_reader:
                line_text = line_raw.rstrip("\n\r")
                
                # Check if the line defines a new Structure, Primitive, or Tag.
                # Otherwise, add the line to the last defined element.
                if ":=" not in line_text:
                     current_element.append_line_definition(line_text)
                     continue
                
                # Create the appropriate element for the line.
                if line_text.endswith("}"):
                    current_element = Primitive.create_from_line_definition(line_text, self)
                    self.primitives[current_element.id] = current_element
                elif line_text.endswith("}:="):
                    current_element = Tag.create_from_line_definition(line_text, self)
                    self.tags[current_element.id] = current_element
                else:
                    current_element = Structure.create_from_line_definition(line_text, self)
                    self.structures[current_element.id] = current_element
