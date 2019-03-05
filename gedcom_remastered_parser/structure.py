from collections import OrderedDict
from typing import List, Union

from .schema_element import SchemaElement

class Structure(SchemaElement):

    def __init__(self, label:str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.description = ""
        self.definitions:List[List[Row]] = []
        self.add_definition()

    @property
    def id(self) -> str:
        return self.label

    @classmethod
    def create_from_line_definition(cls, line:str, schema):
        if line.endswith(":=") == False or " " in line:
            raise ValueError("The line was not a properly formed STRUCTURE header.")
        # Make a new Structure.
        return cls(label=line[:-2], schema=schema)

    def append_line_definition(self, line:str) -> None:
        if line.startswith(("n", "0", "+")):
            self._add_row_from_line_definition(line)
        elif line in ("[","]"):
            pass # Do nothing.
        elif line == "|":
            self.add_definition()
        else:
            # Add text to the description.
            if self.description: self.description += "\n"
            self.description += line

    def add_definition(self):
        self.definitions.append([])

    def _add_row_from_line_definition(self, line):
        cls = None
        kwargs = {}

        line_items = line.split(" ")

        kwargs['level'] = line_items[0]
        kwargs['count_min'], kwargs['count_max'] = line_items[-1].strip("{}").split(":")
        
        sub_line_items = line_items[1:-1]
        
        if sub_line_items[0].startswith("<<"):
            # This row should be a container that holds another structure.
            if len(sub_line_items) != 1:
                raise ValueError("This row has a conflicting defintion, making it's format unknown.")
            cls = SubstructureRow
            kwargs['value'] = sub_line_items[0].strip("<>")
        else:
            i = 0
            if sub_line_items[0].startswith("@"):
                # This row is for a new record. It may optionally have a primitive value, determined later.
                cls = NewRecordRow
                kwargs['xref'] = sub_line_items[0].strip("@<>")
                i = 1
            for sub_spec_item in sub_line_items[i:]:
                # Check if the item is for a primitive value.
                if sub_spec_item.startswith("<"):
                    if not cls:
                        cls = PrimitiveValueRow
                    elif cls == NewRecordRow:
                        # Upgrade this row class when the row has both an xref id and a primitive value.
                        cls = NewRecordWithValueRow
                    else:
                        raise ValueError("This row has a conflicting defintion, making it's format unknown.")
                    kwargs['value'] = sub_spec_item.strip("<>")
                # Check if the item is for a xref pointer value.
                elif sub_spec_item.startswith("@"):
                    if not cls:
                        cls = PointerValueRow
                    else:
                        raise ValueError("This row has a conflicting defintion, making it's format unknown.")
                    kwargs['value'] = sub_spec_item.strip("@<>")
                else:
                    # This item must be a tag, or list of tags.
                    kwargs['tags'] = sub_spec_item.strip("[]").split("|")
            # If a row type has not been determined by this stage, it is because the row does not have a value definition.
            if not cls:
                cls = NoValueRow

        # Make the new row.
        row = cls(structure=self, **kwargs)

        # The row spec get's added to the current working definition, which is the last definition.
        self.definitions[-1].append(row)

    @property
    def txt_definition(self) -> str:
        # Create the header line.
        definition_str = f"{self.label}:="
        # Optionally add the description line(s).
        if self.description:
            definition_str += "\n" + self.description
        # Add the definitions, with wrappers if more than one.
        amount = len(self.definitions)
        if amount:
            definition_str += "\n"
        if amount > 1:
            definition_str += "[\n"
        definition_str += "\n|\n".join("\n".join(row.txt_definition for row in rows) for rows in self.definitions)
        if amount > 1:
            definition_str += "\n]"
        return definition_str

class Unlimited(object):
    def __le__(self, other):
        return True
    def __lt__(self, other):
        return True
    def __repr__(self):
        return "Unlimited"
    def __str__(self):
        return "M"

MANY = Unlimited()

class Row(object):

    _syntax_xref = False
    _syntax_tags = False
    _syntax_value = False

    __abstract__ = True

    def __new__(cls, *args, **kwargs):
        if cls.__abstract__ == True:
            raise TypeError("Cannot initialise this abstract ROW class. Use a specific sub-class that matches the ROW's intention.")
        return super().__new__(cls)

    def __init__(self, structure:Structure, *, level:str, xref:str=None, tags:List[str]=None, value:str=None, count_min:str, count_max:str):
        self.level = level
        self.count_min = int(count_min)
        self.count_max = int(count_max) if count_max != "M" else MANY
        if self._syntax_xref:
            if not xref: raise AttributeError("This class requires an XREF to be specified.")
            self.xref = xref
        elif xref:
            raise AttributeError("This class cannot have an XREF specified.")
        if self._syntax_tags:
            if not tags: raise AttributeError("This class requires a list of TAGS to be specified.")
            self.tags = tags
        elif tags:
            raise AttributeError("This class cannot have any TAGS specified.")
        if self._syntax_value:
            if not value: raise AttributeError("This class requires some type of VALUE to be specified.")
            self.value = value
        elif value:
            raise AttributeError("This class cannot have any type of VALUE specified.")

    @property
    def level(self) -> int:
        return self._level_int

    @level.setter
    def level(self, txt_definition:str):
        if txt_definition == "0":
            self._level_relative = False
            self._level_int = 0
        elif txt_definition == "n":
            self._level_relative = True
            self._level_int = 0
        elif txt_definition.startswith("+"):
            self._level_relative = True
            self._level_int = int(txt_definition[1:])
        else:
            raise ValueError("Row level in a text format not understood.")

    @property
    def txt_definition(self):
        level = self._txt_definition_level
        xref = self._txt_definition_xref
        tags = self._txt_definition_tags
        value = self._txt_definition_value
        size = f"{{{self.count_min}:{self.count_max}}}"
        return " ".join(s for s in [level, xref, tags, value, size] if s)

    @property
    def _txt_definition_level (self):
        if self._level_relative == False:
            return str(self._level_int)
        if self.level == 0:
            return "n"
        return "+" + str(self._level_int)

    @property
    def _txt_definition_xref (self):
        return None

    @property
    def _txt_definition_tags (self):
        return None

    @property
    def _txt_definition_value (self):
        return None

class RowWithTags(Row):
    _syntax_tags = True
    __abstract__ = True

    @property
    def _txt_definition_tags (self):
        return self.tags[0] if len(self.tags) == 1 else "[" + "|".join(self.tags) + "]"

class SubstructureRow(Row):
    """+1 <<NOTE_STRUCTURE>> {0:M}"""
    _syntax_value = True
    __abstract__ = False

    @property
    def substructure (self) -> Structure:
        return structures[self.value]

    @property
    def _txt_definition_value(self):
        substructure_label = self.value # alternative `self.substructure.label`
        return f"<<{substructure_label}>>"

class NoValueRow(RowWithTags):
    """+1 DATA {0:1}"""
    __abstract__ = False

class NewRecordRow(RowWithTags):
    """n @<XREF:OBJE>@ OBJE {1:1}"""
    _syntax_xref = True
    __abstract__ = False

    @property
    def _txt_definition_xref (self):
        return f"@<{self.xref}>@"

class NewRecordWithValueRow(NewRecordRow):
    """n @<XREF:NOTE>@ NOTE <SUBMITTER_TEXT> {1:1}"""
    _syntax_value = True
    __abstract__ = False

    @property
    def primitive(self):
        return self.value
    
    @property
    def _txt_definition_value (self):
        return f"<{self.primitive}>"

class PointerValueRow(RowWithTags):
    """+1 HUSB @<XREF:INDI>@ {0:1}"""
    _syntax_value = True
    __abstract__ = False

    @property
    def pointer(self):
        return self.value

    @property
    def _txt_definition_value (self):
        return f"@<{self.pointer}>@"

class PrimitiveValueRow(RowWithTags):
    """+1 SEX <SEX_VALUE> {0:1}"""
    _syntax_value = True
    __abstract__ = False

    @property
    def primitive(self):
        return self.value

    @property
    def _txt_definition_value (self):
        return f"<{self.primitive}>"
