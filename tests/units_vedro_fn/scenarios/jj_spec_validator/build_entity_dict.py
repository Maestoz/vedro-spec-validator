import string

from d42 import fake, schema
from district42_exp_types.numeric import schema_numeric
from schemax import SchemaData
from vedro_fn import given, scenario, then, when

from vedro_spec_validator.jj_spec_validator.utils._cacheir import _build_entity_dict


def get_random_schema_data_obj() -> SchemaData:
    method = fake(schema.str("get") | schema.str("post") | schema.str("put") | schema.str("delete"))
    path = f"/{fake(schema.str.alphabet(string.ascii_lowercase).len(1, ...))}"
    return SchemaData(
            args=[],
            converted_path=path,
            http_method=method,
            interface_method=method,
            interface_method_humanized=method,
            path=path,
            queries=[],
            request_schema={},
            request_schema_d42=schema.any,
            response_schema={},
            response_schema_d42=schema.dict({}),
            schema_prefix='',
            schema_prefix_humanized='',
            status=fake(schema_numeric.min(200).max(599)),
            tags=[],
        )


@scenario()
def build_entity_dict_with_one_elem():
    with given:
        random_schema_data_obj = get_random_schema_data_obj()

    with when:
        result = _build_entity_dict([random_schema_data_obj])

    with then:
        assert isinstance(result, dict)
        assert len(result) == 1
        key = next(iter(result))
        assert isinstance(key, tuple)
        assert key == (random_schema_data_obj.http_method.upper(),
                       random_schema_data_obj.path,
                       random_schema_data_obj.status)
        assert result[key] == random_schema_data_obj

@scenario()
def build_entity_dict_with_two_elems():
    with given:
        random_schema_data_obj = [get_random_schema_data_obj(), get_random_schema_data_obj()]

    with when:
        result = _build_entity_dict(random_schema_data_obj)

    with then:
        assert isinstance(result, dict)
        assert len(result) == 2
        iterator = iter(result)
        first_key = next(iterator)
        assert isinstance(first_key, tuple)
        assert first_key == (random_schema_data_obj[0].http_method.upper(),
                             random_schema_data_obj[0].path,
                             random_schema_data_obj[0].status)
        assert result[first_key] == random_schema_data_obj[0]
        second_key = next(iterator)
        assert isinstance(second_key, tuple)
        assert second_key == (random_schema_data_obj[1].http_method.upper(),
                              random_schema_data_obj[1].path,
                              random_schema_data_obj[1].status)
        assert result[second_key] == random_schema_data_obj[1]

@scenario()
def try_to_build_entity_dict_with_invalid_type():
    with given:
        random_non_schema_data_obj = {}

    with when:
        try:
            result = _build_entity_dict([random_non_schema_data_obj])
        except Exception as exc:
            caught_exception = exc
        else:
            caught_exception = None

    with then:
        assert isinstance(caught_exception, TypeError)
        assert str(caught_exception) == f"Expected SchemaData, got {type(random_non_schema_data_obj)}"

@scenario()
def try_to_build_entity_dict_with_empty_list():
    with given:
        ...

    with when:
        try:
            result = _build_entity_dict([])
        except Exception as exc:
            caught_exception = exc
        else:
            caught_exception = None

    with then:
        assert isinstance(caught_exception, ValueError)
        assert str(caught_exception) == "Empty list of entities provided."