#!/usr/bin/env python3

import util


def main():
    print("I'm in main")

    util.fib(3)


def signal_handler(signal, frame):
    sys.exit(1)


if __name__ == "__main__":
    main()
