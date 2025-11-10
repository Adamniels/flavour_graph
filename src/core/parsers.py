"""Parsing utilities for product data.

Functions for parsing and normalizing ingredient statements, EAN codes, etc.
"""
import re
from typing import List, Tuple


def parse_ingredients(ingredient_statement: str) -> List[Tuple[str, float]]:
    """Parse ingredient statement into a list of tuples (name: str, quantity: float).
    
    Extracts ingredient names and quantities (including percentages) from the statement.
    If no quantity is found, defaults to 0.0.
    
    Args:
        ingredient_statement: Raw ingredient statement string
        
    Returns:
        List of tuples (ingredient_name, quantity) where quantity is a float
        
    Examples:
        >>> parse_ingredients("Vatten, socker (20%), salt")
        [('Vatten', 0.0), ('socker', 20.0), ('salt', 0.0)]
        
        >>> parse_ingredients("kokosflingor (4,6%), mjölk")
        [('kokosflingor', 4.6), ('mjölk', 0.0)]
    """
    # Remove common prefixes like "Ingredienser:" or "Ingredients:"
    if ':' in ingredient_statement:
        ingredient_statement = ingredient_statement.split(':', 1)[1]
    
    # Split by commas, but be careful not to split on commas inside parentheses
    parts = []
    current = ""
    paren_depth = 0
    
    for char in ingredient_statement:
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif char == ',' and paren_depth == 0:
            # This comma is a separator, not inside parentheses
            parts.append(current.strip())
            current = ""
        else:
            current += char
    
    # Add the last part
    if current.strip():
        parts.append(current.strip())
    
    # Process each ingredient part
    ingredients = []
    for ing in parts:
        if not ing:
            continue
        
        # Try to extract quantity from parentheses
        # Pattern: ingredient (quantity) or ingredient (percentage%)
        # Examples: "kokosflingor (4,6%)", "taurin (0,4 %)", "russin (13%)"
        quantity = 0.0
        name = ing
        
        # Look for parentheses with numbers/percentages
        paren_match = re.search(r'\(([^)]+)\)', ing)
        if paren_match:
            content = paren_match.group(1).strip()
            
            # Check if it's a percentage or quantity
            # Pattern: number with optional comma as decimal separator, optional %
            # Match numbers with comma or dot as decimal separator
            qty_match = re.search(r'(\d+[,.]?\d*)\s*%?', content)
            if qty_match:
                qty_str = qty_match.group(1)
                # Replace comma with dot for float conversion
                qty_str = qty_str.replace(',', '.')
                try:
                    quantity = float(qty_str)
                except ValueError:
                    quantity = 0.0
                
                # Remove the parentheses content from the name
                name = re.sub(r'\s*\([^)]+\)', '', ing).strip()
            else:
                # Parentheses contain non-quantity info, keep it in the name
                name = ing
        else:
            # No parentheses, just the ingredient name
            name = ing
        
        # Clean up the name (remove extra whitespace)
        name = ' '.join(name.split())
        
        if name:  # Only add if we have a name
            ingredients.append((name, quantity))
    
    return ingredients


def normalize_ean(ean: str, length: int = 14) -> str:
    """Normalize EAN code to a fixed length with leading zeros.
    
    Args:
        ean: EAN code as string
        length: Target length (default: 14)
        
    Returns:
        Normalized EAN string with leading zeros
        
    Examples:
        >>> normalize_ean("12345")
        '00000000012345'
        
        >>> normalize_ean("123456789012", 13)
        '0123456789012'
    """
    try:
        return str(int(ean)).zfill(length)
    except (ValueError, TypeError):
        return ean


def extract_product_name(product_data: dict) -> str:
    """Extract the best available product name from product data.
    
    Tries multiple fields in priority order:
    1. brandName + descriptionShort
    2. descriptionShort only
    3. brandName only
    4. tradeItemDescription
    5. Product ID as fallback
    
    Args:
        product_data: Dictionary with product information
        
    Returns:
        Best available product name string
    """
    brand_name = product_data.get('brandName', '')
    description_short = product_data.get('descriptionShort', '')
    trade_item_desc = product_data.get('tradeItemDescription', '')
    product_id = product_data.get('gtin', product_data.get('id', 'Unknown'))
    
    if brand_name and description_short:
        return f"{brand_name} {description_short}"
    elif description_short:
        return description_short
    elif brand_name:
        return brand_name
    elif trade_item_desc:
        return trade_item_desc
    else:
        return product_id
