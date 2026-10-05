"""Default configuration. Override any key with a FLASK_<KEY> environment variable."""


class DefaultConfig:
    # Flask only reads UPPERCASE attributes from config objects.
    LOG_LEVEL = "INFO"
