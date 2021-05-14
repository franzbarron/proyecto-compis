# Semantic cube
# Check that operations can be executed

equality_ops = ['==', '<>']
comparison_ops = ['<', '>', '<=', '>=']
logic_ops = ['&', '|']
arithmetic_ops = ['+', '-', '*', '/']


def checkArithmetic(type1, type2, operator):
    if (operator == '+' or operator == '-' or operator == '*') and type1 == 'int' and type2 == 'int':
        return 'int'
    if (type1 == 'int' or type1 == 'float') and (type2 == 'int' or type2 == 'float'):
        return 'float'
    if type1 == 'string' and type2 == 'string' and operator == '+':
        return 'string'
    raise TypeError(f'{operator} cannot operate between {type1} and {type2}')


def checkEquality(type1, type2, operator):
    if (type1 == 'int' or type1 == 'float') and (type2 == 'int' or type2 == 'float'):
        return 'bool'
    if type1 == type2:
        return 'bool'
    raise TypeError(f'{operator} cannot operate between {type1} and {type2}')


def checkComparison(type1, type2, operator):
    if (type1 == 'int' or type1 == 'float') and (type2 == 'int' or type2 == 'float'):
        return 'bool'
    if type1 == 'string' and type2 == 'string':
        return 'bool'
    raise TypeError(f'{operator} cannot operate between {type1} and {type2}')


def checkLogicOp(type1, type2, operator):
    if type1 == 'bool' and type2 == 'bool':
        return 'bool'
    raise TypeError(f'{operator} cannot operate between {type1} and {type2}')


def checkAssignment(type1, type2, operator):
    if type1 == 'int' and (type2 == 'int' or type2 == 'float'):
        return 'int'
    if type1 == 'float' and (type2 == 'int' or type2 == 'float'):
        return 'float'
    if type1 == type2:
        return type1
    raise TypeError(f'{operator} cannot operate between {type1} and {type2}')


def checkOperation(type1, type2, operator):
    if operator in equality_ops:
        return checkEquality(type1, type2, operator)
    if operator in comparison_ops:
        return checkComparison(type1, type2, operator)
    if operator in logic_ops:
        return checkLogicOp(type1, type2, operator)
    if operator in arithmetic_ops:
        return checkArithmetic(type1, type2, operator)
    if operator == '=':
        return checkAssignment(type1, type2, operator)
    raise Exception(f'Opertator {operator} not defined in specification')
