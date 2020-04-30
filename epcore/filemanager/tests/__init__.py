from os.path import dirname, join as join_path
from os import listdir
from pytest import main


if __name__ == '__main__':

    tests = []
    for test in listdir(dirname(__file__)):
        if test.endswith(".py"):
            tests.append(join_path(dirname(__file__), test))
    main(tests)
