from typing import List, Dict, Any, Type
from sqlalchemy.orm import Query
from sqlalchemy import or_

def pick(data: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Pick only specified keys from a dictionary"""
    return {key: data[key] for key in keys if key in data}

def apply_search_filter(query: Query, search_term: str, searchable_fields: List[str], model_class: Type) -> Query:
    """Apply search term filtering across multiple fields"""
    if not search_term or not searchable_fields:
        return query

    search_conditions = []
    for field_name in searchable_fields:
        if hasattr(model_class, field_name):
            field = getattr(model_class, field_name)
            search_conditions.append(field.ilike(f"%{search_term}%"))

    if search_conditions:
        query = query.filter(or_(*search_conditions))

    return query

def apply_dynamic_field_filters(query: Query, filters_data: Dict[str, Any], filterable_fields: List[str], model_class: Type) -> Query:
    """Apply field-specific filters dynamically"""
    if not filters_data:
        return query

    additional_conditions = []

    for field_name, value in filters_data.items():
        if field_name not in filterable_fields or value is None or value == "":
            continue

        if hasattr(model_class, field_name):
            field = getattr(model_class, field_name)

            # Dynamic type conversion
            if field_name.lower().endswith('id') or field_name == 'id':
                processed_value = int(value) if str(value).isdigit() else value
            elif isinstance(value, str) and value.lower() in ['true', 'false']:
                processed_value = value.lower() == 'true'
            else:
                processed_value = value

            additional_conditions.append(field == processed_value)

    if additional_conditions:
        query = query.filter(*additional_conditions)

    return query

def apply_field_filters(query: Query, filters: Dict[str, Any], filterable_fields: List[str], model_class: Type) -> Query:
    """Apply field-specific filters (legacy method for backward compatibility)"""
    filters_data = {k: v for k, v in filters.items() if v is not None}
    return apply_dynamic_field_filters(query, filters_data, filterable_fields, model_class)

def calculate_pagination(page: int, limit: int) -> Dict[str, Any]:
    """Calculate pagination parameters"""
    page = max(1, page)
    limit = max(1, min(100, limit))
    skip = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "skip": skip
    }
