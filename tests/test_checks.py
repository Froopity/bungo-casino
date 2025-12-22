import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_ignore_bots_allows_human_users(mock_ctx):
  from casino.checks import ignore_bots

  @ignore_bots
  async def dummy_command(ctx):
    await ctx.channel.send('success')

  mock_ctx.bot = MagicMock()
  mock_ctx.bot.user = MagicMock()
  mock_ctx.bot.user.id = 999999
  mock_ctx.author.id = 12345

  await dummy_command(mock_ctx)
  mock_ctx.channel.send.assert_called_once_with('success')


@pytest.mark.asyncio
async def test_ignore_bots_filters_bot_messages(mock_ctx):
  from casino.checks import ignore_bots

  @ignore_bots
  async def dummy_command(ctx):
    await ctx.channel.send('success')

  mock_ctx.bot = MagicMock()
  mock_ctx.bot.user = MagicMock()
  mock_ctx.bot.user.id = 12345
  mock_ctx.author.id = 12345
  mock_ctx.author = mock_ctx.bot.user

  await dummy_command(mock_ctx)
  mock_ctx.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_is_registered_allows_registered_users(mock_db, mock_ctx):
  from casino.checks import is_registered

  con, cur = mock_db
  cur.execute('INSERT INTO user (id, discord_id, display_name) VALUES (?, ?, ?)',
              ('test-uuid', '12345', 'TestUser'))
  con.commit()

  check = is_registered(cur)
  predicate = check.predicate
  result = await predicate(mock_ctx)
  assert result is True


@pytest.mark.asyncio
async def test_is_registered_rejects_unregistered_users(mock_db, mock_ctx):
  from casino.checks import is_registered, NotRegisteredError

  con, cur = mock_db

  check = is_registered(cur)
  predicate = check.predicate

  with pytest.raises(NotRegisteredError):
    await predicate(mock_ctx)


@pytest.mark.asyncio
async def test_error_handler_registration_check(mock_ctx):
  from casino.bot import on_command_error
  from casino.checks import NotRegisteredError

  error = NotRegisteredError()
  await on_command_error(mock_ctx, error)

  mock_ctx.channel.send.assert_called_once_with(
    'woaah slow down ther cowboy, you gotta say $howdy first'
  )
