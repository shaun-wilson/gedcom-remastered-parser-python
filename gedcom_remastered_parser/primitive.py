import re
from collections import OrderedDict
from typing import List

from functools import update_wrapper
class reify(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        update_wrapper(self, wrapped)
    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
cached_property = reify

from .schema_element import SchemaElement

regex_primitive_header = re.compile('^([A-Z0-9_:]+?):= {Size=(\d+|\d+:\d+)}$')
regex_optionalvalue_components = re.compile('<([^>]+)>|{([^}]+)}|%([^%]+)%|([^{<%]+)')

class Component(object):
    _tag = "Component"
    _format = "{0}"
    def __init__(self, value:str):
        self.value = value
    def __repr__(self):
        return "{0}<{1}>".format(self._tag, self.value)
    def __str__(self):
        return self._format.format(self.value)
class PrimitiveComponent(Component):
    _tag = "Primitive"
    _format = "<{0}>"
class StringComponent(Component):
    _tag = "String"
class TermComponent(StringComponent):
    _tag = "Term"
    _format = "{{{0}}}"
class TagComponent(StringComponent):
    _tag = "Tag"
    _format = "%{0}%"

class OptionalValue(object):

    def __init__(self, definition:str, parent):
        self.definition = definition
        self.parent = parent
    
    def __str__(self):
        return self.definition #todo, this shortcut is cheating

    def __repr__(self):
        return self.components
    
    # The 4 following properties will be populated by a call to components().
    @cached_property
    def has_primitives(self):
        self.components
        return self.__dict__['has_primitives']
    @cached_property
    def has_terms(self):
        self.components
        return self.__dict__['has_terms']
    @cached_property
    def has_tags(self):
        self.components
        return self.__dict__['has_tags']
    @cached_property
    def has_strings(self):
        self.components
        return self.__dict__['has_strings']

    @cached_property
    def components(self):
        self.__dict__.update({key: False for key in ('has_primitives', 'has_terms', 'has_tags', 'has_strings')})
        components = []
        for primitive, term, tag, string in regex_optionalvalue_components.findall(self.definition):
            if primitive:
                components.append(PrimitiveComponent(primitive))
                self.__dict__['has_primitives'] = True
            elif term:
                components.append(TermComponent(term))
                self.__dict__['has_terms'] = True
            elif tag:
                components.append(TagComponent(tag))
                self.__dict__['has_tags'] = True
            elif string:
                components.append(StringComponent(string))
                self.__dict__['has_strings'] = True
            else:
                # Should not have made it to this point.
                raise ValueError("The definition string for the option was malformed.")
        return components

DEFAULT_OPTIONS_DEFINITION = "<TEXT>"

class OptionalValues(list):
    
    @cached_property
    def has_primitives(self):
        return any(ov.has_primitives for ov in self)
    @cached_property
    def has_terms(self):
        return any(ov.has_terms for ov in self)
    @cached_property
    def has_tags(self):
        return any(ov.has_tags for ov in self)
    @cached_property
    def has_strings(self):
        return any(ov.has_strings for ov in self)

class Primitive(SchemaElement):

    def __init__(self, *, label:str, size_min:str, size_max:str=None, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.size_min = int(size_min)
        self.size_max = int(size_max) if size_max else self.size_min
        self.description = ""
        self.terms = None
        # Create the default optional values definition, which may be overriden later.
        self.optional_values = OptionalValues()
        self.optional_values.append(OptionalValue(DEFAULT_OPTIONS_DEFINITION, self))
    
    @property
    def id(self) -> str:
        return self.label

    @classmethod
    def create_from_line_definition(cls, line:str, schema):
        match = regex_primitive_header.match(line)
        if not match:
            raise ValueError("The line was not a properly formed PRIMITIVE header.")
        size_min, size_max = match[2].partition(":")[::2]
        # Make a new tag.
        return cls(label=match[1], size_min=size_min, size_max=size_max, schema=schema)

    def append_line_definition(self, line:str) -> None:
        if line.startswith("["):
            # The line is optional values. Override the existing.
            self.optional_values = OptionalValues()
            line_stripped = line[1:-1] # Safer than using strip("[]"), which can remove required brackets, eg [BC].
            for option_definition in line_stripped.split("|"):
                optional_value = OptionalValue(option_definition, self)
                self.optional_values.append(optional_value)
        elif line == "Where:":
            # The line is the beginning of a term definition.
            self.terms = OrderedDict()
        elif self.terms != None:
            # The line must be an additional term definition.
            key, val = line.partition(" = ")[::2]
            self.terms[key] = val
        else:
            # Add text to the description.
            if self.description: self.description += "\n"
            self.description += line

    def __repr__(self):
        return str(self.__dict__)

    @property
    def txt_definition(self):
        # Create the header line, including the label and size.
        if self.size_max != self.size_min:
            definition_text = f"{self.label}:= {{Size={self.size_min}:{self.size_max}}}"
        else:
            definition_text = f"{self.label}:= {{Size={self.size_min}}}"
        # Optionally add the optional_value line.
        option_text = "|".join(str(o) for o in self.optional_values)
        if option_text != DEFAULT_OPTIONS_DEFINITION:
            definition_text += "\n[" + option_text + "]"
        # Optionally add the description line(s).
        if self.description:
            definition_text += "\n" + self.description
        # Optionally add the terms lines.
        if self.terms:
            definition_text += "\nWhere:\n"
            definition_text += "\n".join(f"{k} = {v}" for k,v in self.terms.items())
        return definition_text
