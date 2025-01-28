from http import HTTPStatus

import jj
import vedro
from jj.http.methods import POST

from for_dev.helpers.mocked_response import mocked_response
from vedro_spec_validator.jj_spec_validator import validate_spec
from jj.mock import Mocked


@vedro.context
@validate_spec(spec_link="https://checkin.web-staging.2gis.ru/docs/swagger.yaml", force_strict=True)
def mocked_debug() -> Mocked:
    matcher = jj.match(POST, "/checkins")
    response_body = {"checkin": {
        "ids": "57609a2a-08dc-4aa8-8375-d6951cbd5954",
        "object_id": "141265771709693",
    }}
    response = jj.Response(status=HTTPStatus.OK, json=response_body)
    return mocked_response(matcher, response)

debug = mocked_debug()
