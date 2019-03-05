from abc import ABC, abstractmethod

class SchemaElement(ABC):

    def __init__(self, *, schema):
        self.schema = schema

    @classmethod
    @abstractmethod
    def create_from_line_definition(self, line:str, schema):
        raise NotImplementedError

    @abstractmethod
    def append_line_definition(self, line:str) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def txt_definition(self) -> str:
        raise NotImplementedError
