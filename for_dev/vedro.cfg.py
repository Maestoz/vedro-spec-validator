import vedro
import vedro_spec_validator



class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class SpecValidator(vedro_spec_validator.SpecValidator):
            enabled = True

            skip_if_failed_to_get_spec = True

