from d42.declaration.types import AnySchema, DictSchema, GenericSchema, ListSchema
from d42.utils import is_ellipsis
from niltype import Nil

__all__ = ('get_forced_strict_spec', 'has_ellipsis_in_all_branches')


def get_forced_strict_spec(schema: GenericSchema) -> GenericSchema:
    if isinstance(schema, DictSchema):
        if schema.props.keys is not Nil:
            new_keys = {}
            for k, (v, is_optional) in schema.props.keys.items():
                if not is_ellipsis(k):
                    new_keys[k] = (get_forced_strict_spec(v), is_optional)
            return schema.__class__(schema.props.update(keys=new_keys))
        return schema
    elif isinstance(schema, ListSchema):
        if schema.props.elements is not Nil:
            new_elements = [get_forced_strict_spec(element) for element in schema.props.elements]
            return schema.__class__(schema.props.update(elements=new_elements))
        elif schema.props.type is not Nil:
            new_type = get_forced_strict_spec(schema.props.type)
            return schema.__class__(schema.props.update(type=new_type))
        return schema
    elif isinstance(schema, AnySchema):
        if schema.props.types is not Nil:
            new_types = tuple(get_forced_strict_spec(t) for t in schema.props.types)
            return schema.__class__(schema.props.update(types=new_types))
        return schema
    else:
        return schema

def has_ellipsis_in_all_branches(schema: GenericSchema) -> bool:
    """
    Check if all branches of the schema contain an Ellipsis object.
    Returns True if every branch has at least one Ellipsis, False otherwise.
    
    The function recursively traverses the schema structure and checks if each
    DictSchema in the structure contains at least one Ellipsis. If any DictSchema
    without an Ellipsis is found, the function returns False.
    
    NOTE: If no DictSchema is found in the entire structure, the function returns False.
    """
    def _has_ellipsis_recursive(schema, dict_found=None):
        if dict_found is None:
            dict_found = [False]
            
        if is_ellipsis(schema):
            return True
            
        if isinstance(schema, DictSchema):
            dict_found[0] = True
            
            if schema.props.keys is Nil or not schema.props.keys:
                return True
                
            has_ellipsis_key = any(is_ellipsis(k) for k in schema.props.keys.keys())
            
            if not has_ellipsis_key:
                return False
                
            for k, (v, _) in schema.props.keys.items():
                if not is_ellipsis(k) and not _has_ellipsis_recursive(v, dict_found):
                    return False
                    
            return True
            
        elif isinstance(schema, ListSchema):
            if schema.props.elements is not Nil and schema.props.elements:
                if not schema.props.elements:
                    return False
                    
                for element in schema.props.elements:
                    if not _has_ellipsis_recursive(element, dict_found):
                        return False
                return True
            elif schema.props.type is not Nil:
                return _has_ellipsis_recursive(schema.props.type, dict_found)
            return False
            
        elif isinstance(schema, AnySchema):
            if schema.props.types is Nil or not schema.props.types:
                return False
                
            for t in schema.props.types:
                if not _has_ellipsis_recursive(t, dict_found):
                    return False
                    
            return True
            
        return True
    
    dict_found = [False]
    result = _has_ellipsis_recursive(schema, dict_found)
    
    if not dict_found[0]:
        return False
        
    return result
