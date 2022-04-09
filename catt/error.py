class CattError(Exception):
    """Base exception for catt."""

    pass


class CattUserError(CattError):
    """
    Messages from exceptions that inherit from this class,
    are transformed into error messages to the cli user.
    """

    pass


class StateFileError(CattError):
    """When a requested state file contains invalid data or nothing."""

    pass


class ListenerError(CattError):
    """When invalid data is passed to a listener class initializer."""

    pass


class AppSelectionError(CattError):
    """When invalid data is passed to the app selection mechanism."""

    pass


class PlaylistError(CattError):
    """When playlist specific operations are attempted with non-playlist info."""

    pass


class APIError(CattError):
    # The scope of this exception is probably going to be a bit broad.
    # We can split it into more exceptions once the api is more mature.
    pass


class SubtitlesError(CattUserError):
    """When a specified subtitles file cannot be found or its encoding cannot be determined."""

    pass


class CliError(CattUserError):
    """When the cli user passes invalid commands/options/arguments to catt."""

    pass


class CastError(CattUserError):
    """When operations are attempted with non-existent or inactive devices."""

    pass


class ControllerError(CattUserError):
    """When a controller is incapable of the requested action."""

    pass


class ExtractionError(CattUserError):
    """When the requested media cannot be found or processed by yt-dlp."""

    pass


class FormatError(CattUserError):
    """When the supplied format filter is invalid or excludes all available formats."""

    pass
