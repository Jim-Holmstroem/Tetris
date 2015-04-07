from __future__ import division, print_function

import os
from operator import itemgetter
from itertools import (
    imap,
    product,
    chain,
    ifilterfalse,
    cycle,
    groupby,
)
from functools import (
    partial,
)
from random import (
    sample,
)

def apply(f, *args, **kwargs):
    return f(*args, **kwargs)


width, height = 32, 32


def translation(dx=0, dy=0):
    def translator((x, y)):
        return (x + dx, y + dy)

    return translator


def normalize_bits(bits):
    def upper_left_translation(bits):
        (min_x, _), (_, min_y) = (
            min(bits, key=itemgetter(0)),
            min(bits, key=itemgetter(1)),
        )

        return -min_x, -min_y

    return set(
        map(
            translation(
                *upper_left_translation(bits)
            ),
            bits
        ) if len(bits) > 0 else []
    )


def render_bits(bits, width=width, height=height):
    def render_row(y):
        def render_col(x):
            return '#' if (x, y) in bits else ' '

        return "|{}|\n".format(
            ''.join(
                map(
                    render_col,
                    range(width)
                )
            )
        )

    border = "-" * (1 + width + 1)

    return "{border}\n{body}{border}".format(
        border=border,
        body=''.join(
            map(
                render_row,
                range(height)
            )
        ),
    )


def collision(bits_A, bits_B):
    return len(bits_A & bits_B) > 0


def fall(bits, falling_bits, update=translation(0, 1), height=height):
    """
    Parameters
    ----------
    bits :: {bit}
        static bits
    falling_bits :: {bit}
        falling bits
    update :: bit -> bit
        update the falling bits
    height :: int
        the height of the frame

    Returns
    -------
    result_bits :: {bit}
    """
    fallen_bits = set(map(update, falling_bits))
    bit_collision = collision(bits, fallen_bits)
    frame_collision = not(valid_y(fallen_bits, height=height))

    result_bits = fall(bits, fallen_bits) if not(bit_collision) and not(frame_collision)\
        else bits | falling_bits

    return result_bits


def valid_x(bits, width=width):
    return all(
        imap(
            lambda (x, _): 0 <= x < width,
            bits
        )
    )


def valid_y(bits, height=height):
    return all(
        imap(
            lambda (_, y): 0 <= y < height,
            bits
        )
    )


def valid(bits, width=width, height=height):
    return valid_x(bits, width=width) and valid_y(bits, height=height)


class Block(object):
    def rotations(self):  # TODO function?
        def rotate(bits):
            return normalize_bits(
                map(
                    lambda (x, y): (y, -x),
                    bits
                )
            )

        pos_0 = self.bits  # NOTE scan
        pos_1 = rotate(pos_0)
        pos_2 = rotate(pos_1)
        pos_3 = rotate(pos_2)

        return [
            pos_0,
            pos_1,
            pos_2,
            pos_3,
        ]


class I(Block):
    bits = {
        (0, 0),
        (0, 1),
        (0, 2),
        (0, 3),
    }


class J(Block):
    bits = {
        (0, 2),
        (1, 2),
        (1, 1),
        (1, 0),
    }


class L(Block):
    bits = {
        (1, 2),
        (0, 2),
        (0, 1),
        (0, 0),
    }


class O(Block):
    bits = {
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
    }


class S(Block):
    bits = {
        (0, 1),
        (1, 0),
        (1, 1),
        (2, 0),
    }


class T(Block):
    bits = {
        (0, 1),
        (1, 0),
        (1, 1),
        (2, 1),
    }


class Z(Block):
    bits = {
        (0, 0),
        (1, 0),
        (1, 1),
        (2, 1),
    }


Blocks = [I, J, L, O, S, T, Z]


def choices(block, bits=set(), width=width):
    """
    Parameters
    ----------
    bits :: {bit}
        the static bits on the board
    """
    translators = map(
        partial(partial, map),
        map(
            translation,
            range(width)
        )  # :: [bit -> bit]
    )  # :: [{bit} -> {bit}]

    possible_choices = map(
        set,
        chain.from_iterable(
            map(
                lambda bits: map(
                    lambda translator: translator(bits),
                    translators
                ),
                block.rotations()
            )
        )
    )

    valid_choices = list(ifilterfalse(
        partial(collision, bits),
        filter(
            valid_x,
            possible_choices
        )
    ))

    return valid_choices


def full_rows(bits, width=width):
    rows = groupby(
        sorted(
            bits,
            key=itemgetter(1)
        ),
        itemgetter(1)
    )

    full_row_groups = filter(
        lambda (row, bits): len(list(bits)) == width,
        rows
    )

    full_rows_ = set(map(
        itemgetter(0),
        full_row_groups
    ))

    return full_rows_


def flushed(bits, width=width):
    full_rows_ = full_rows(bits, width=width)
    non_flushed_bits = filter(
        lambda (x, y): y not in full_rows_,
        bits
    )

    def n_rows_below_flushed(row):
        n_flushed = len(
            filter(
                lambda full_row: row < full_row,
                full_rows_
            )
        )

        return n_flushed

    flushed_ = set(map(
        lambda (x, y): (x, y+n_rows_below_flushed(y)),
        non_flushed_bits
    ))

    return flushed_


blocks = map(apply, Blocks)

# random placement of random blocks (simple use to see that it works)
import sys
from time import sleep
while True:
    try:
        board = set()
        while True:
            sys.stderr.write("\x1b[2J\x1b[H")
            moves = choices(sample(blocks, 1)[0], bits=board)  # TODO rename bits to board
            board = fall(board, sample(moves, 1)[0])  # NOTE scan
            print(render_bits(board))
            sleep(0.03)
    except KeyboardInterrupt as ki:
        sys.exit()
    except Exception as e:
        pass
