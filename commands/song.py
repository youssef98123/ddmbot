import discord.ext.commands as dec

import database.song
from commands.common import *


class Song:
    """Song insertion, querying and manipulation"""
    def __init__(self, bot):
        self._bot = bot
        self._db = database.song.SongInterface(bot.loop)

    _help_messages = {
        'group': 'Song information, querying and manipulation',

        'blacklist': '* Puts the specified song to the blacklist\n\n'
        'Song ID can be located in the square brackets just before the title. It is included in the status message '
        'and all the listings.\nThis does not prevent users from including blacklisted song in their playlist, song '
        'is skipped just before playing.',

        'deduplicate': '* Marks a song as a duplicate of another song\n\n'
        'This is a destructive operation. The duplicate is replaced by the "original" just before playing. All tests '
        '(blacklist, length, overplay) are performed on the "original" song.\nThis function is useful for replacing '
        'songs with a bad quality and is necessary for overplay protection to work correctly.\nSong IDs can be located '
        'in the square brackets just before the title. It is included in the status message and all the listings. You '
        'can also use \'search\' command to obtain the IDs.',

        'failed_clear': '* Removes the songs from the failed list\n\n'
        'Songs marked as duplicates are not affected. Individual songs can be removed by specifying their ID. You can '
        'use the command to fix the automatic playlist after a service outage or bot connection problems.',

        'failed_list': 'Lists all the songs that have failed to download\n\n'
        'Up to 20 songs are returned. Songs marked as a duplicate are considered resolved and are excluded from the '
        'list. Songs are automatically removed from this list after a successful download, or manually by using '
        '\'clear\' subcommand.\n\nSongs that are marked as failed to download are excluded from the automatic '
        'playlist. Bot operators are expected to investigate download issues and provide an alternative source for '
        'the songs if necessary.',

        'info': 'Displays information about the song stored in the database\n\n'
        'Mainly for debugging purposes, as an aid for the bot operators.',

        'permit': '* Removes the specified song from the blacklist\n\n'
        'Song ID can be located in the square brackets just before the title. It is included in the status message '
        'and all the listings.',

        'rename': '* Changes the title of a specified song\n\n'
        'This command can be used to rename the song stored in the database. It does not update the status message; '
        'the new name is used next time the song is played.\nSong ID can be located in the square brackets just before '
        'the title. It is included in the status message and all the listings.',

        'search': 'Queries the database for songs\n\n'
        'Title and UURI are matched against the specified keywords. All the keywords must match either the title or '
        'UURI. Up to 20 results are returned.\nThis command can be used to lookup song IDs.',

        'split': '* Marks a given song as an original\n\n'
        'This command can be used to fix duplication status of the song. After this command is issued, the song '
        'specified won\'t be marked as a duplicate anymore.\nThis is the inverse command to the \'deduplicate\'. '
        'Just like the \'deduplicate\', this command does not manipulate with timestamps nor credit counts.\nSong ID '
        'can be located in the square brackets just before the song title. It is included in the status message and '
        'all the listings.'
    }

    @dec.group(invoke_without_command=True, aliases=['s'], help=_help_messages['group'])
    async def song(self, subcommand: str, *arguments: str):
        raise dec.UserInputError('Command *song* has no subcommand named {}. Please use `{}help song` to list all '
                                 'the available subcommands.'
                                 .format(subcommand, self._bot.config['ddmbot']['delimiter']))

    @privileged
    @song.command(ignore_extra=False, help=_help_messages['blacklist'])
    async def blacklist(self, song_id: int):
        await self._db.blacklist(song_id)
        await self._bot.message('Song [{}] has been blacklisted'.format(song_id))

    @privileged
    @song.command(ignore_extra=False, help=_help_messages['deduplicate'])
    async def deduplicate(self, which_id: int, target_id: int):
        await self._db.merge(which_id, target_id)
        await self._bot.message('Song [{}] has been marked as a duplicate of the song [{}]'.format(which_id, target_id))

    @song.group(ignore_extra=False, invoke_without_command=True)
    async def failed(self):
        raise dec.UserInputError('You need to provide a subcommand to the *song failed* command')

    @privileged
    @failed.command(name='clear', ignore_extra=False, help=_help_messages['failed_clear'])
    async def failed_clear(self, song_id: int = None):
        raise dec.UserInputError('You need to provide a subcommand to the *song failed* command')

    @failed.command(name='list', ignore_extra=False, aliases=['l'], help=_help_messages['failed_list'])
    async def failed_list(self):
        items, total = await self._db.list_failed(20)
        if not items:
            await self._bot.whisper('There are no songs flagged because of a download failure')
            return
        reply = '**{} songs (out of {}) flagged because of a download failure:**\n **>** '.format(len(items), total) + \
                '\n **>** '.join(['[{}] {}'.format(*item) for item in items])
        await self._bot.whisper(reply)

    @song.command(ignore_extra=False, aliases=['i'], help=_help_messages['info'])
    async def info(self, song_id: int):
        info = await self._db.get_info(song_id)
        reply = '**Song [{id}] information:**\n' \
                '    **Source URL:** [{url}]\n' \
                '    **Title:** {title}\n' \
                '    **Last played:** {last_played!s}\n' \
                '    **Listener count:** {total_listener_count} ({listener_count})\n' \
                '    **Skip vote count:** {total_skip_vote_count} ({skip_vote_count})\n' \
                '    **Duration:** {duration}s\n' \
                '    **Credits remaining:** {credit_count}\n\n' \
                '    **Blacklisted:** {is_blacklisted}\n' \
                '    **Has failed to download:** {has_failed}\n\n' \
                '    **Marked as a duplicate of:** {duplicates}\n' \
                '    **Is duplicated by:** {duplicated_by}'.format_map(info)
        await self._bot.whisper(reply)

    @privileged
    @song.command(ignore_extra=False, help=_help_messages['permit'])
    async def permit(self, song_id: int):
        await self._db.permit(song_id)
        await self._bot.message('Song [{}] has been removed from blacklist'.format(song_id))

    @privileged
    @song.command(ignore_extra=False, help=_help_messages['rename'])
    async def rename(self, song_id: int, new_title: str):
        await self._db.rename(song_id, new_title)
        await self._bot.message('Song [{}] has been renamed to "{}"'.format(song_id, new_title))

    @song.command(ignore_extra=False, aliases=['s'], help=_help_messages['search'])
    async def search(self, *keywords: str):
        items, total = await self._db.search(keywords, 20)
        if not items:
            await self._bot.whisper('Search for songs with keywords {} has not returned any result'.format(keywords))
            return
        reply = '**{} songs (out of {}) matching the keywords {}:**\n **>** '.format(len(items), total, keywords) + \
                '\n **>** '.join(['[{}] {}'.format(*item) for item in items])
        await self._bot.whisper(reply)

    @privileged
    @song.command(ignore_extra=False, help=_help_messages['split'])
    async def split(self, song_id: int):
        await self._db.merge(song_id, song_id)
        await self._bot.message('Song [{}] has been marked as unique'.format(song_id))
