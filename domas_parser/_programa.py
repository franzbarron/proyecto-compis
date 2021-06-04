from sly.yacc import _decorator as _
from .domas_quadruples import Quadruple
from .domas_errors import ReservedWordError
import json


@_('')
def programa(self, p):
    print('Tabla de funciones:', json.dumps(self.function_table, indent=2))
    print('Table de clases:', json.dumps(self.class_table, indent=2))
    print('Cuadruplos:')
    for num, quad in enumerate(self.quadruples, start=1):
        print(num, quad)
    return 'programa'


@_('')
def pro0(self, p):
    self.quadruples.append(Quadruple(None, None, 'goto', None))
    self.quad_counter += 1


@_('')
def pro1(self, p):
    if p[-1] == 'main':
        raise ReservedWordError('main', 'program name')
    self.program_name = p[-1]
    self.curr_scope = p[-1]
    self.function_table[p[-1]] = {'return_type': None, 'vars': {}}
