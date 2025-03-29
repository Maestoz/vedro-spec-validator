import vedro
import vedro_fn


class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class VedroFn(vedro_fn.VedroFn):
            enabled = True
