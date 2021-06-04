from sly.yacc import _decorator as _
from .domas_quadruples import Quadruple


@ _('')
def fd1(self, p):
    self.curr_func_type = p[-1]


@ _('')
def fd3(self, p):
    if p[-1] in self.function_table or p[-1] in self.class_table or p[-1] in self.function_table[self.program_name]['vars']:
        raise SyntaxError(f'Redefinition of {p[-1]}')
    else:
        self.add_to_func_table(p[-1], self.curr_func_type)
        self.last_func_added = p[-1]
        self.curr_scope = self.last_func_added
        self.function_table[self.program_name]['vars'][p[-1]
                                                       ] = {'type': self.curr_func_type}


@ _('')
def fd4(self, p):
    self.function_table[self.last_func_added]['start'] = self.quad_counter


@ _('')
def fd5(self, p):
    # del self.function_table[self.last_func_added]['vars']
    pass


@ _('')
def fd6(self, p):
    self.quadruples.append(Quadruple(None, None, 'end_func', None))
    self.quad_counter += 1
    self.temp_counter = 1
