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
    # Используем внутреннюю функцию для отслеживания наличия DictSchema
    def _has_ellipsis_recursive(schema, dict_found=None):
        if dict_found is None:
            dict_found = [False]
            
        # Простой случай - если сама схема это эллипсис
        if is_ellipsis(schema):
            return True
            
        # Для словарей проверяем наличие эллипсиса в каждом из них
        if isinstance(schema, DictSchema):
            # Отмечаем, что нашли DictSchema
            dict_found[0] = True
            
            # Если словарь пустой или ключи не определены - эллипсиса нет
            if schema.props.keys is Nil or not schema.props.keys:
                return False
                
            # Проверяем наличие эллипсиса среди ключей
            has_ellipsis_key = any(is_ellipsis(k) for k in schema.props.keys.keys())
            
            # Если эллипсиса нет в ключах - это ошибка
            if not has_ellipsis_key:
                return False
                
            # Далее рекурсивно проверяем все вложенные схемы
            for k, (v, _) in schema.props.keys.items():
                if not is_ellipsis(k) and not _has_ellipsis_recursive(v, dict_found):
                    return False
                    
            # Если все проверки прошли - в этом DictSchema есть эллипсис и все вложенные схемы тоже имеют эллипсис
            return True
            
        # Для списков проверяем их содержимое
        elif isinstance(schema, ListSchema):
            # Проверяем elements если они есть
            if schema.props.elements is not Nil and schema.props.elements:
                # Для пустого списка элементов считаем, что DictSchema с эллипсисом нет
                if not schema.props.elements:
                    return False
                    
                for element in schema.props.elements:
                    if not _has_ellipsis_recursive(element, dict_found):
                        return False
                # Если все элементы прошли проверку
                return True
            # Проверяем type если он есть
            elif schema.props.type is not Nil:
                return _has_ellipsis_recursive(schema.props.type, dict_found)
            # Если ни elements, ни type не определены - эллипсиса нет
            return False
            
        # Для AnySchema проверяем все типы
        elif isinstance(schema, AnySchema):
            if schema.props.types is Nil or not schema.props.types:
                return False
                
            for t in schema.props.types:
                if not _has_ellipsis_recursive(t, dict_found):
                    return False
                    
            return True
            
        # Для примитивных типов логика должна быть особой:
        # Если это примитивный тип, в нем нет DictSchema без эллипсиса
        return True
    
    # Отслеживаем, был ли найден хотя бы один DictSchema
    dict_found = [False]
    result = _has_ellipsis_recursive(schema, dict_found)
    
    # Костыль: если не было найдено ни одного DictSchema, возвращаем False
    if not dict_found[0]:
        return False
        
    return result
