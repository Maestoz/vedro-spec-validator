[vedro-spec-validator](https://pypi.org/project/vedro-spec-validator/) is a [Vedro](https://vedro.io) plugin that allows to validate mocks via OpenAPI spec/docs.

### Version Compatibility Notice

- For versions of this package **0.1.0 and later**, only version 2 of the [`d42`](https://github.com/d42-schemas/d42) package is compatible.


## Installation

<details open>
<summary>Quick</summary>
<p>

For a quick installation, you can use a plugin manager as follows:

```shell
$ vedro plugin install vedro-spec-validator
```

</p>
</details>

<details>
<summary>Manual</summary>
<p>

To install manually, follow these steps:

1. Install the package using pip:

```shell
$ pip3 install vedro-spec-validator
```

2. Next, activate the plugin in your `vedro.cfg.py` configuration file:

```python
# ./vedro.cfg.py
import vedro
import vedro_spec_validator

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class SpecValidator(vedro_spec_validator.SpecValidator):
            enabled = True
```

</p>
</details>

## Usage

Decorate your [mocked](https://pypi.org/project/jj/) function with `@validate_spec()`, providing a link to a YAML or JSON OpenAPI spec.
```python
import jj
from jj.mock import mocked
from vedro_spec_validator import validate_spec

@validate_spec(spec_link="http://example.com/api/users/spec.yml")
async def your_mocked_function():
    matcher = jj.match("GET", "/users")
    response = jj.Response(status=200, json=[])
    
    mock = await mocked(matcher, response)
```
### Keys 

1. The `is_strict` key allows you to choose between strict and non-strict comparison. Non-strict comparison (`False` by default) allows you to mock only some fields from the spec, even if they are required. Strict validation (`True`) requires you to mock all required fields from the spec.

Example OpenAPI spec with required fields: 
```
openapi: 3.0.0
paths:
  /user:
    get:
      ...
        properties:
          user_name:
            type: string
          email:
            type: string
          age:
            type: integer
        required: 
          - user_name
          - email
          - age
```
With `is_strict=True`:
```python
from vedro_spec_validator import validate_spec

@validate_spec(spec_link="http://example.com/api/users/spec.yml", is_strict=True)
async def your_mocked_function():
    matcher = jj.match("GET", "/user")
    payload = {
        "user_name": "Foo",
        "email": "test@test.com",
        "age": 30  # All required fields from the spec must be present
    }
    response = jj.Response(json=payload)
    return await mocked(matcher, response)
```
With `is_strict=False`:
```python
from vedro_spec_validator import validate_spec

@validate_spec(spec_link="http://example.com/api/users/spec.yml", is_strict=False)
async def your_mocked_function():
    matcher = jj.match("GET", "/user")
    payload = {
        "user_name": "Foo"  # Required fields like "email" and "age" can be omitted
    }
    response = jj.Response(json=payload)
    return await mocked(matcher, response)
```


2. The `prefix` key allows you to specify a path prefix that should be removed from the mock function's paths before they are matched against the OpenAPI spec.
```python
from vedro_spec_validator import validate_spec


@validate_spec(spec_link="http://example.com/api/users/spec.yml", prefix='/__mocked_api__')  # Goes to validate `/user` instead of `/__mocked_api__/user`
async def your_mocked_function():
    matcher = jj.match("GET", "/__mocked_api__/user")
    # The prefix is removed, so the actual path matched against the OpenAPI spec is `/user`
    ...
```

3. The `is_raise_error` key allows you to control whether an error should be raised when a validation mismatch occurs. By default (`False`), no exception is raised, but mismatches will be logged to a file.

With `is_raise_error=False`:
```python
from vedro_spec_validator import validate_spec


@validate_spec(spec_link="http://example.com/api/users/spec.yml", is_raise_error=False)
async def your_mocked_function():
    ...
```
Output will be written to a file:
```text
# /spec_validator/validation_results/your_mocked_function/scenarios/path/to/test/test_scenario.py.txt

subject: scenario subject
valera.ValidationException
- ... # missmatches
```

With `is_raise_error=True`:
```python
from vedro_spec_validator import validate_spec


@validate_spec(spec_link="http://example.com/api/users/spec.yml", is_raise_error=True)
async def your_mocked_function():
    ...
```

An exception will be raised on the first validation error, causing the test to fail with the following trace:
```text
ValidationException: There are some mismatches in your_mocked_function:
valera.ValidationException
- ... # missmatches
 
 
# --seed ...
# 1 scenario, 0 passed, 1 failed, 0 skipped (2.35s)

Process finished with exit code 1
```

4. The `force_strict` key enforces strict validation against the OpenAPI spec, treating all fields as required, even if they are marked as optional in the spec. This is useful in cases where the specification accidentally marks all fields as optional. `False` by default.