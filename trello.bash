#! /bin/bash

function trbrd() {
    # Show `Hotels` board.

    python3 $TRELLO_SCRIPT show_board

    return 0
}

function mnd() {
    # Perform `Monday` process
    # Create report template, move recently done tickets to `All` card's comments
    # Delete these tickets from `Done` list

    python3 $TRELLO_SCRIPT monday

    return 0
}

function trlst() {
    # Show list's information
    # $1 {i/w/t}- list's name
    # If argument is omitted, show `Done` list's cards.

    if [ "$1" == 'i' ]; then
        list_name="In progress"
    elif [ "$1" == 'w' ]; then
        list_name="Waiting for customer"
    elif [ "$1" == 't' ]; then
        list_name="Testing"
    else
        list_name="Done"
    fi

    python3 $TRELLO_SCRIPT show_list -arg1="$list_name"

    return 0
}

function trcc() {
    # Create card
    # $1 - card's name
    # $2 {w/t/d}- list's name
    # If second argument is omitted, create card on `in progress` list.

    if [ "$2" == 'd' ]; then
        list_name="Done"
    elif [ "$2" == 'w' ]; then
        list_name="Waiting for customer"
    elif [ "$2" == 't' ]; then
        list_name="Testing"
    else
        list_name="In progress"
    fi

    python3 $TRELLO_SCRIPT create_card -arg1="$1" -arg2="$list_name" 

    return 0
}

function trdc() {
    # Delete card
    # $1 - card's name

    python3 $TRELLO_SCRIPT delete_card -arg1="$1"

    return 0
}

function trmc() {
    # Move card
    # $1 - card's name
    # $2 {i/w/t}- list's name. Card will be moved onto this list.
    # If second argument is omitted, move card to `Done` list.

    if [ "$2" == 'i' ]; then
        list_name="In progress"
    elif [ "$2" == 'w' ]; then
        list_name="Waiting for customer"
    elif [ "$2" == 't' ]; then
        list_name="Testing"
    else
        list_name="Done"
    fi

    python3 $TRELLO_SCRIPT move_card -arg1="$1" -arg2="$list_name" 

    return 0
}

function truc() {
    # Update card
    # $1 - card's name
    # $2 - new card's name

    python3 $TRELLO_SCRIPT update_card -arg1="$1" -arg2="$2" 

    return 0
}