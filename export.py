import argparse
import configparser
import logging
from typing import Dict, Iterable, NamedTuple

import logzero
from trello import TrelloClient, Board, List as TrelloList, Card, exceptions as trello_exceptions

logger = logzero.setup_logger(level=logging.INFO)


class CardData(NamedTuple):
    name: str
    desc: str
    comments: str


class ListData(NamedTuple):
    name: str
    cards: Iterable[CardData]


class TrelloExportException(Exception):
    pass


class CredentialsException(TrelloExportException):
    pass


class NoBoardException(TrelloExportException):
    pass


class NoListsException(TrelloExportException):
    pass


config = configparser.ConfigParser()
config.read('real_config.conf')


def trello_credentials() -> Dict:
    try:
        return dict(config['trello'])
    except KeyError:
        logger.error('There’s either no “trello” section in config.conf or no config file at all')
        raise CredentialsException


def setup_client() -> TrelloClient:
    return TrelloClient(**trello_credentials())


def find_board(client: TrelloClient, board_name: str) -> Board:
    try:
        all_boards = client.list_boards()
    except trello_exceptions.Unauthorized:
        logger.error('Invalid API key, secret, or token. Check your config.conf file')
        raise CredentialsException

    matching_boards = [board for board in all_boards
                       if board.name.lower() == board_name.lower()]

    if len(matching_boards) == 1:
        logger.info('Found a board with exactly this name')
        return matching_boards[0]
    if len(matching_boards) > 1:
        logger.error('Found more than one board with this name')
        raise NoBoardException

    logger.info('Didn’t find an exact match')
    inexactly_matching = [board for board in all_boards
                          if board_name.lower() in board.name.lower()]

    if len(inexactly_matching) == 1:
        board = inexactly_matching[0]
        logger.info(f'Found a board with a matching name: {board.name}')
        return board
    if len(inexactly_matching) > 1:
        logger.error('Found more than one board with this name')
        raise NoBoardException

    logger.error('Didn’t find neither an exact match nor a similar name')
    raise NoBoardException


def find_lists(board: Board, lists_names: str) -> Iterable[TrelloList]:
    if lists_names:
        names = lists_names.split(',')
        matching_lists = [list_ for list_ in board.list_lists()
                          if list_.name in names]
    else:
        matching_lists = board.list_lists()

    found = len(matching_lists)

    if found == 0:
        logger.error('No lists with specified names found')
        raise NoListsException

    exported_lists = ', '.join(l.name for l in matching_lists)
    logger.info(f'Exporting lists {exported_lists}')

    if lists_names and found != len(names):
        logger.warning(f'Found only {found} lists out of specified {len(names)}')

    return matching_lists


def extract_comments(card: Card, export_comments: bool) -> str:
    if not export_comments:
        return ''

    comments = card.get_comments()
    comments_str = (f'{c["memberCreator"]["fullName"]}: {c["data"]["text"]}' for c in comments)
    return '\n'.join(comments_str)


def get_data(trello_list: TrelloList, export_comments: bool) -> ListData:
    cards = trello_list.list_cards()
    logger.info('Getting data from cards')
    cards_data = (CardData(card.name,
                           card.description,
                           extract_comments(card, export_comments))
                  for card in cards)
    return ListData(trello_list.name, cards_data)


def format_card(card: CardData, count: int, no_numbering: bool, prefix: str) -> str:
    result = f'{card.name}\n{card.desc}\n'

    if not no_numbering:
        result = f'{prefix} {count}. {result}'

    if card.comments:
        result = f'{result} \n{card.comments}\n\n'

    return result


def save_to_file(data: Iterable[ListData], merge: bool, prefix: str,
                 no_numbering: bool,
                 board_name: str):
    logger.info('Saving to files')
    files = set()
    for list_data in data:
        if merge:
            filename = f'{board_name}.txt'
            mode = 'a'
        else:
            filename = f'{list_data.name}.txt'
            mode = 'w'

        with open(filename, mode) as output:
            cards_formatted = (format_card(card, index, no_numbering, prefix)
                               for index, card in enumerate(list_data.cards, 1))
            output.writelines(cards_formatted)

        files.add(filename)
    logger.info(f'Saved to {files}')


def main(options):
    try:
        client = setup_client()
        board = find_board(client, options.board)
        lists = find_lists(board, options.lists)
        cards_data = (get_data(list_, options.comments) for list_ in lists)
        save_to_file(cards_data, options.merge, options.prefix, options['no-numbering'], board.name)
    except TrelloExportException:
        logger.error('Export failed. See details above')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('board', help='Name of trello board to export',
                        type=str)
    parser.add_argument('--lists', '-l', default=None,
                        help='Name of the list(s) to export')
    parser.add_argument('--prefix', '-p', default='',
                        help='Prefix written before each card’s description')
    parser.add_argument('--comments', '-c', action='store_true',
                        help='Export comments as well')
    parser.add_argument('--merge', '-m', action='store_true',
                        help='Merge all exported lists into one file')
    parser.add_argument('--no-numbering', '-n', action='store_true',
                        help='Do not number exported cards')
    args = parser.parse_args()
    main(args)
