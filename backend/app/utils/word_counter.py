import re
from typing import Union

def count_words(text: Union[str, None]) -> int:
    """
    Count the number of words in a text string.
    
    Args:
        text: The text to count words in
        
    Returns:
        Number of words in the text
    """
    if not text:
        return 0
    
    # Remove multiple spaces and trim
    text = text.strip()
    if not text:
        return 0
    
    # Split by whitespace and filter out empty strings
    # This handles multiple spaces, tabs, newlines, etc.
    words = re.findall(r'\b\w+\b', text)
    
    return len(words)