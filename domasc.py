from lexer_parser.domas_lexer import DomasLexer
from lexer_parser.domas_parser import DomasParser
import sys


if __name__ == '__main__':
    lexer = DomasLexer()
    parser = DomasParser()
    filename = 'tests/test.txt'

    if(len(sys.argv) > 1):
        filename = sys.argv[1]

    with open(filename) as fp:
        try:
            result = parser.parse(lexer.tokenize(fp.read()))
            print(result)
        except EOFError:
            pass
        except Exception as err:
            print(err)
            pass
