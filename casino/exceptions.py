
class BotNotAuthenticatedError(Exception):
  """
  Raise when information is accessed or a bot action attempted that requires
  authentication, but the bot is not logged in.
  """
  def __init__(self, message: str) -> None:
    super().__init__(message)


class SqlError(Exception):
  """
  Generic error to raise due when SQL goes awry.
  """
  def __init__(self, message: str) -> None:
    super().__init__(message)


class BungoError(Exception):
  """
  An error message that can be returned to Discord directly via bungo
  """
  def __init__(self, message: str) -> None:
    super().__init__(message)


class UnknownEntityError(Exception):
  """
  Thrown when encountering an entity that is unknown, such as a
  mentioned user not found in the database.
  """
  def __init__(self, message: str) -> None:
    super().__init__(message)
