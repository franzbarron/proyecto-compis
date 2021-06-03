from lexer_parser.domas_errors import CompilationError
from lexer_parser.domas_lexer import DomasLexer
from lexer_parser.domas_parser import DomasParser
# from domas_parser import DomasParser
import sys
import traceback
import json


def parse_func_dir(func_dir, outfile):
    for func_name in func_dir:
        parsed_str = func_name + ' '
        for key in func_dir[func_name]:
            if key == 'params' and func_dir[func_name][key] == '':
                func_dir[func_name][key] = '-'
            if key == 'return_type':
                types = [None, 'int', 'float', 'string', 'bool', 'void']
                func_dir[func_name][key] = types.index(
                    func_dir[func_name][key]) - 1
            parsed_str += str(func_dir[func_name][key]) + ' '
        outfile.write(parsed_str + '\n')


def parse_class_dir(class_dir, outfile):
    for class_name in class_dir:
        outfile.write(class_name + ' ' +
                      class_dir[class_name]['num_types'] + '\n')
        for key in class_dir[class_name]:
            parsed_str = key + ' '
            if key == 'num_types':
                continue
            for cosa in class_dir[class_name][key]:
                if cosa == 'params' and class_dir[class_name][key][cosa] == '':
                    class_dir[class_name][key][cosa] = '-'
                if cosa == 'return_type':
                    types = [None, 'int', 'float', 'string', 'bool', 'void']
                    class_dir[class_name][key][cosa] = types.index(
                        class_dir[class_name][key][cosa]) - 1
                parsed_str += str(class_dir[class_name][key][cosa]) + ' '
            outfile.write(parsed_str + '\n')
        outfile.write('%\n')


def parse_constant_table(constant_table, outfile):
    for type in constant_table:
        parsed_str = ''
        for num in constant_table[type]:
            parsed_str += str(num) + '\u001f'
        outfile.write(type + '\u001f' + parsed_str + '\n')


if __name__ == '__main__':
    lexer = DomasLexer()
    parser = DomasParser()
    filename = 'tests/test.txt'

    if(len(sys.argv) > 1):
        filename = sys.argv[1]

    with open(filename) as fp:
        try:
            program_name, func_dir, class_dir, constant_table, quads = parser.parse(
                lexer.tokenize(fp.read()))
            outfile = open(program_name + '.domas', 'w')
            parse_func_dir(func_dir, outfile)
            outfile.write('#\n')
            parse_class_dir(class_dir, outfile)
            outfile.write('#\n')
            parse_constant_table(constant_table, outfile)
            outfile.write('#\n')
            for quad in quads:
                outfile.write(str(quad) + '\n')
            print('Code compiled successfully to', program_name + '.domas')
        except EOFError:
            pass
        except SystemError as err:
            print(err)
            exit(2)
        except CompilationError:
            exit(1)
        except Exception as err:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            traceback.print_exception(
                exception_type, exception_object, exception_traceback)
            pass
