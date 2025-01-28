from d42.utils import is_ellipsis
from d42.declaration.types import AnySchema, DictSchema, ListSchema, GenericSchema


from niltype import Nil

__all__ = ('get_forced_strict_spec', )


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
