from ._config import Config


def output(func_name: str = "", text: str = None, e: Exception = None, ) -> None:
    if Config.OUTPUT_FUNCTION is None:
        if text and e:
            print(f"{text}\nException: {str(e)}\n")
            # print(f"⚠️ ⚠️ ⚠️ {text} in {func_name} :\n{str(e)}\n")
        elif e:
            print(f"\nException: {str(e)}\n")
            # print(f"⚠️ ⚠️ ⚠️ There are some mismatches in {func_name} :\n{str(e)}\n")
        else:
            print(f"text\n")
    else:
        Config.OUTPUT_FUNCTION(func_name, e, text)