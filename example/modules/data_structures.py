from enum import Enum
from typing import Any

type Position = tuple[int, int]


class Direction(Enum):
    """Representations of directions on a square grid."""
    UP = (0,-1)
    UP_RIGHT = (1,-1)
    RIGHT = (1,0)
    DOWN_RIGHT = (1,1)
    DOWN = (0,1)
    DOWN_LEFT = (-1,1)
    LEFT = (-1,0)
    UP_LEFT = (-1,-1)


class LinkedListItemSingleLink:
    """Simplified Linked List
    data:           contents of the linked list item.
    link:           next Linked List object."""
    __slots__ = ('data', 'link')
    def __init__(self, data=None, link=None) -> None:
        self.data:Any = data
        self.link:LinkedListItemSingleLink|None = link

    def __str__(self) -> str:
        return f"<LinkedListItemSingleLink:data={self.data},link={self.link}>"
