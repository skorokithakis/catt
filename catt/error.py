class CattError(Exception):
    pass


class CattDevError(CattError):
    pass


class CattUserError(CattError):
    pass


class StateFileError(CattDevError):
    pass


class ListenerError(CattDevError):
    pass


class AppSelectionError(CattDevError):
    pass


class StreamInfoError(CattDevError):
    pass


class APIError(CattDevError):
    pass


class SubtitleError(CattUserError):
    pass


class CliUserError(CattUserError):
    pass


class CastUserError(CattUserError):
    pass


class InfoUserError(CattUserError):
    pass
