from sly.yacc import _decorator as _
from .domas_quadruples import Quadruple
from . import domas_semantic_cube as sc


@_('variable ass1 EQUALS expression ass2 SEMI')
def assignment(self, p):
    return 'assignment'


@_('')
def ass1(self, p):
    # If we're dealing with a method of a class
    if self.current_class != None:
        # print('ass1 p[-1]:', p[-1])
        if not p[-1] in self.class_table[self.current_class][self.curr_scope]['vars'] and not p[-1] in self.class_table[self.current_class]['vars']:
            raise SyntaxError(f'Variable {p[-1]} is not declared')
        self.latest_var = p[-1]
    # elif not p[-1] in self.function_table[self.curr_scope]['vars'] and not p[-1] in self.function_table[self.program_name]['vars']:
    #     raise SyntaxError(f'Variable {p[-1]} is not declared')
    else:
        self.latest_var = p[-1]


@_('')
def ass2(self, p):
    # print(f'ass2 line {sys._getframe().f_lineno}')
    while(len(self.stack_operators)):
        self.make_and_push_quad()
    lo = self.stack_operands.pop()
    # print(json.dumps(self.function_table, indent=2))
    v_type = self.get_var_type(self.latest_var)
    # print('ass2 v_type', v_type)
    self.last_type = sc.checkOperation(v_type, lo['type'], '=')
    q = Quadruple(lo['value'], None, '=', self.latest_var)
    self.quadruples.append(q)
    self.quad_counter += 1
    # for num, quad in enumerate(self.quadruples, start=1):
    #     print(num, quad)
