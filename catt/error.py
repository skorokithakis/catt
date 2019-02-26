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


class PlaylistError(CattDevError):
    pass


class APIError(CattDevError):
    pass


class SubsEncodingError(CattDevError):
    pass


class CliError(CattUserError):
    pass


class CastError(CattUserError):
    pass


class ControllerError(CattUserError):
    pass


class ExtractionError(CattUserError):
    pass


class FormatError(CattUserError):
    pass
