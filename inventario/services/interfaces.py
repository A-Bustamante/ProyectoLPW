from abc import ABC, abstractmethod

class ICodeGenerator(ABC):
    @abstractmethod
    def generate_code(self, asset_type: str, next_id: int) -> str:
        """
        Generates a unique internal code based on the asset type and next incremental sequence.
        Example output: LAP-2026-0042
        """
        pass

class IPDFGenerator(ABC):
    @abstractmethod
    def generate_assignment_act(self, assignment) -> str:
        """
        Generates a PDF document for the assignment and returns the path relative to MEDIA_ROOT.
        """
        pass
