from langchain.tools import tool

@tool
def generic_tool():
    """A generic tool for demonstration purposes."""
    return "This is a generic tool."
