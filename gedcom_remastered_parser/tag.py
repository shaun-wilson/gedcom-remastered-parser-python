import re

from .schema_element import SchemaElement

re_tag_header = re.compile('([A-Z0-9]+) {([A-Z0-9_\-]+)}:=')

class Tag(SchemaElement):

    def __init__(self, *, tag:str, label:str, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.label = label
        self.description = ""

    @property
    def id(self) -> str:
        return self.tag

    @classmethod
    def create_from_line_definition(cls, line:str, schema):
        match = re_tag_header.match(line)
        if not match:
            raise ValueError("The line was not a properly formed TAG header.")
        # Make a new tag.
        return cls(tag=match[1], label=match[2], schema=schema)

    def append_line_definition(self, line:str) -> None:
        # Add text to the description.
        if self.description: self.description += "\n"
        self.description += line

    @property
    def txt_definition(self) -> str:
        # Create the header line.
        definition_str = f"{self.tag} {{{self.label}}}:="
        # Optionally add the description line(s).
        if self.description:
            definition_str += "\n" + self.description
        return definition_str
