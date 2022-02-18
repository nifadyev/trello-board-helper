"""
Script for parsing data from Trello boards using Trello API.

Use for constructing weekly reports containing list of done tickets
and story points for each of them.
"""

import argparse
from typing import Optional, Any
import datetime
from itertools import chain
import requests


# Credentials
CREDENTIALS = f'key={API_KEY}&token={API_TOKEN}'


class TrelloAPI():
    def __init__(self, args, api_key=API_KEY, api_token=API_TOKEN):
        self.args = TrelloAPI.parse_arguments(args)
        self.api_key = api_key
        self.api_token = api_token
        self.tickets = self.get_tickets_information()

    def get_list_cards(self, list_id: str) -> Optional[tuple[dict[str, str]]]:
        """
        Retrieve tuple of dictionaries,
        containing `card's ID, ticket's name and ticket's story point`.
        """

        response = requests.get(
            f'{URL}lists/{list_id}/cards?fields=name&{CREDENTIALS}')

        if response.status_code != 200:
            print('Could not get list of done tickets')
            return

        return tuple(
            TrelloAPI.parse_card_name(card)
            for card in response.json()
        )

    def show_board(self) -> None:
        """Show all board's lists."""

        print('Hotels board\n')
        for list_title in self.tickets:
            self.show_list_tickets(list_title)

    @staticmethod
    def get_board_information(
            board_id: str = HOTELS_BOARD_ID) -> dict[str, Any]:
        """Return board information, containing its `ID, name and etc."""

        return requests.get(
            f'{URL}boards/{board_id}?fields=id,name,closed,desc,shortUrl,url&{CREDENTIALS}'
        ).json()

    @staticmethod
    def get_lists_information() -> list[dict[str, str]]:
        """Return lists information, containing their `ID and name.`"""

        return requests.get(
            f'{URL}boards/{HOTELS_BOARD_ID}/lists?fields=name&{CREDENTIALS}'
        ).json()

    def show_list_tickets(self, list_name: str) -> None:
        """Get list of tickets with its story points."""

        if list_name not in (
            'In progress', 'Waiting for customer', 'Testing', 'Done'):

            print(f'List {list_name} not found on current board')
            return

        print(list_name)

        start = 0
        if list_name == 'Done':
            start = 1
            print('  - All - contains list of all done tickets')

        for ticket in self.tickets[list_name][start:]:
            print(f"  - {ticket['name']} - {ticket['story points']} points")

    @staticmethod
    def parse_card_name(card: dict[str, str]) -> dict[str, str]:
        """
        Get ticket's name and story points per each card
        from card's name and ID.
        """

        if not card['name']:
            return {'id': '', 'name': '', 'story points': '0'}

        # Only such cards are permitted.
        cards_name = card['name'].split()

        points = '0'
        if len(cards_name) > 1:
            try:
                isinstance(int(cards_name[-1]), str)
            except ValueError:
                points = '0'
            else:
                points = cards_name[-1]

        return {
            'id': card['id'],
            'name': cards_name[0],
            'story points': points
        }

    def delete_card(self, card_name: str) -> int:
        """Remove card from board using `card name`."""

        card_id = self.get_card_id(card_name) or self.get_card_id(card_name.split()[0])

        status_code = requests.delete(
            url=f'{URL}/cards/{card_id}?{CREDENTIALS}',
        ).status_code

        return status_code

    @staticmethod
    def create_card(card_name: str, list_name: str) -> int:
        """Create card with specific name onto specified list."""

        list_id = TrelloAPI.get_list_id(list_name)

        status_code = requests.post(
            url=f'{URL}lists/{list_id}/cards?{CREDENTIALS}',
            data={'name': card_name}
        ).status_code

        return status_code

    def move_card(self, full_card_name: str, list_name: str) -> int:
        """Move card from one list to another one on the same board."""

        card_id = self.get_card_id(full_card_name)
        if card_id:
            # if move card only by it's `name`, without `story points`
            # `story points` are not saved
            for card in chain(*self.tickets.values()):
                if card['id'] == card_id:
                    card_name = f"{card['name']} - {card['story points']}"
                    break
            else:
                card_name = full_card_name
        else:
            card_name = full_card_name.split()[0]

        if (
                self.delete_card(card_name) == 200 and
                TrelloAPI.create_card(card_name, list_name) == 200
        ):
            return 200
        return 400

    def update_card(self, full_card_name: str, new_name: str) -> int:
        """
        Replace card's name with new one.
        Usually used to add story points to done ticket
        """

        # * This method could be converted to update any card's field
        card_id = self.get_card_id(full_card_name) or self.get_card_id(full_card_name.split()[0])

        response = requests.put(
            url=f'{URL}cards/{card_id}?{CREDENTIALS}',
            data={'name': new_name}
        )

        return response.status_code

    def get_tickets_information(self) -> dict[str, Optional[tuple[dict[str, str]]]]:
        """
        Retrive all necessary information about current situation on board
        to create report template.
        """

        return {
            'In progress': self.get_list_cards(IN_PROGRESS_LIST_ID),
            'Waiting for customer': self.get_list_cards(WAITING_LIST_ID),
            'Testing': self.get_list_cards(TESTING_LIST_ID),
            'Done': self.get_list_cards(DONE_LIST_ID)
        }

    @staticmethod
    def get_week() -> str:
        """Get week's start and week's end dates."""

        # ! Week might be not full or it can contain holidays
        today = datetime.datetime.today()
        # If today is not Monday then use day difference
        # Between today and Monday
        # Otherwise use previous Monday date
        diff = datetime.timedelta(days=(today.weekday() or 7))
        monday = today - diff
        friday = monday + datetime.timedelta(days=4)

        return f"Неделя {monday.strftime('%d.%m.%Y')} - {friday.strftime('%d.%m.%Y')}"

    def create_letter_template(self) -> str:
        """Create weekly report template."""

        # Previous week on report's top
        template = [f'{TrelloAPI.get_week()}:\n\n', ]

        for tickets_list in self.tickets:
            template.append(f'{tickets_list}:\n')
            template.extend(
                f"  - {JIRA_URL}{ticket['name']} - {ticket['story points']} points\n"
                for ticket in self.tickets[tickets_list]
            )

        template.remove('  - https://gojira.skyscanner.net/browse/All - 0 points\n')
        template.append(f'SP per week: {self.get_weekly_story_points()}\n')

        # TODO: '\n'.join(template) instead of current version
        return ''.join(template)

    def get_weekly_story_points(self):
        return sum(int(card['story points']) for card in self.get_list_cards(DONE_LIST_ID)[1:])

    def move_cards_name_to_comments(self) -> int:
        """Move previously done cards to `All` card on `Done` list."""

        # First ticket in `Done` list is skipped
        # Because done ticket are moved into it.
        for ticket in self.tickets['Done'][1:]:
            status_code = requests.post(
                url=f'{URL}cards/{ALL_DONE_TICKETS_CARD_ID}/actions/comments?{CREDENTIALS}',
                data={'text': f"{ticket['name']} - {ticket['story points']}"}
            ).status_code
            if status_code != 200:
                return status_code

        return 200

    @staticmethod
    def parse_arguments(args: list[str]) -> argparse.Namespace():
        """
        Handle command line arguments using argparse.

        Method's name is required.
        Method's arguments could be passed after method's name
        if they are required.
        """

        argument_parser = argparse.ArgumentParser(
            description='Trello automation')

        argument_parser.add_argument(
            'method',
            help='desired method to run'
        )
        argument_parser.add_argument(
            "-arg1",
            help="First method's argument"
        )
        argument_parser.add_argument(
            "-arg2",
            help="Second method's argument"
        )

        return argument_parser.parse_args(args)

    def run(self) -> None:
        """Run specified method with specified arguments."""

        if self.args.method == 'monday':
            print(self.create_letter_template())

            move_cards_status_code = self.move_cards_name_to_comments()
            if move_cards_status_code != 200:
                print("Failed to move recently done cards to `All' comments\n")
                return

            for card in self.tickets['Done'][1:]:
                status_code = self.delete_card(card['name'])
                if status_code != 200:
                    print(f"Failed to delete card {card['name']}\n")
                    return

            print('Recently done cards has been successfully archived.')

        elif self.args.method == 'show_board':
            self.show_board()
        elif self.args.method == 'show_list':
            self.show_list_tickets(self.args.arg1)

        elif self.args.method == 'create_card':
            status_code = TrelloAPI.create_card(self.args.arg1, self.args.arg2)
            TrelloAPI.show_reply(status_code, 'create')
        elif self.args.method == 'delete_card':
            status_code = self.delete_card(self.args.arg1)
            TrelloAPI.show_reply(status_code, 'delete')
        elif self.args.method == 'move_card':
            status_code = self.move_card(self.args.arg1, self.args.arg2)
            TrelloAPI.show_reply(status_code, 'move')
        elif self.args.method == 'update_card':
            status_code = self.update_card(self.args.arg1, self.args.arg2)
            TrelloAPI.show_reply(status_code, 'update')

        else:
            print('There is no method with such name')

    @staticmethod
    def show_reply(status_code: int, operation: str) -> None:
        """
        Show operation status.
        Available operations: create, delete, update, move.
        """

        if status_code == 200:
            print(f'Card has been successfully {operation}d.')
        else:
            print(
                f'Card has not been {operation}d.'
                "Please check card's name and list's name (if required).\n"
                f"Operation failed with {status_code} error."
            )

    def get_card_id(self, card_name: str) -> str:
        """Return card ID by it's name."""

        for card in chain(*self.tickets.values()):
            if card['name'] == card_name:
                return card['id']

        return ''

    @staticmethod
    def get_list_id(list_name: str) -> str:
        """Return list ID by list's name."""

        if list_name == 'In progress':
            return IN_PROGRESS_LIST_ID
        if list_name == 'Testing':
            return TESTING_LIST_ID
        if list_name == 'Waiting for customer':
            return WAITING_LIST_ID
        if list_name == 'Done':
            return DONE_LIST_ID

        return ''
