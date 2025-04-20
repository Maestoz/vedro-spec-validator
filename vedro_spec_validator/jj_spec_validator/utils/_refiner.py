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
    """
    if isinstance(schema, DictSchema):
        if schema.props.keys is Nil or not schema.props.keys:
            return False  # Если нет ключей, то нет и Ellipsis

        # Проверяем, есть ли Ellipsis среди ключей
        has_ellipsis_key = any(is_ellipsis(k) for k in schema.props.keys.keys())

        # Если нет Ellipsis в ключах, проверяем все значения
        if not has_ellipsis_key:
            # Все значения должны содержать Ellipsis
            return all(has_ellipsis_in_all_branches(v) for k, (v, _) in schema.props.keys.items())

        return True  # Если есть Ellipsis в ключах, то эта ветвь содержит Ellipsis

    elif isinstance(schema, ListSchema):
        if schema.props.elements is not Nil and schema.props.elements:
            # Все элементы списка должны содержать Ellipsis
            return all(has_ellipsis_in_all_branches(element) for element in schema.props.elements)
        elif schema.props.type is not Nil:
            # Проверяем тип списка
            return has_ellipsis_in_all_branches(schema.props.type)
        return False  # Если нет ни элементов, ни типа, то нет и Ellipsis

    elif isinstance(schema, AnySchema):
        if schema.props.types is not Nil and schema.props.types:
            # Все типы должны содержать Ellipsis
            return all(has_ellipsis_in_all_branches(t) for t in schema.props.types)
        return False  # Если нет типов, то нет и Ellipsis

    else:
        # Для других типов - проверяем, является ли сам объект Ellipsis
        return is_ellipsis(schema)
