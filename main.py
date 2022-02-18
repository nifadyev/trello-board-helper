import sys
from src.trello import TrelloAPI

trello = TrelloAPI(sys.argv[1:])

trello.run()
