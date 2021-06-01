from sly import Parser
from sly.yacc import _decorator as _
from .domas_lexer import DomasLexer
from .domas_quadruples import Quadruple
from .domas_errors import *
from . import domas_semantic_cube as sm
import json  # to debug only
import sys
import copy


class DomasParser(Parser):
    # Parser directives
    tokens = DomasLexer.tokens
    # debugfile = 'parser.out'
    start = 'programa'
    # Tables
    function_table = {}
    class_table = {}
    constant_table = {'int': [], 'float': [], 'string': [], 'bool': []}
    # Stacks
    stack_of_stacks = [[], []]  # operands, operators !important
    stack_vars = []
    last_arr_t = []
    displacements = []
    for_var_dir = []
    break_stack = []
    # Lists
    quadruples = []
    jumps = []
    # Counters
    quad_counter = 1
    param_counter = 0
    temp_counter = 0
    attr_counter = 1
    # Aux vars
    current_class = None
    last_arr_id = None
    last_type = None
    has_returned = False
    types = ['int', 'float', 'string', 'bool', 'void']
    operators = ['+', '-', '*', '/', '<',
                 '>', '<=', '>=', '==', '<>', '&', '|']

    def add_to_func_table(self, id, return_type):
        self.function_table[id] = {
            'return_type': return_type,
            'vars': {},
            'num_types': '0\u001f' * len(self.types),
            'params': '',
            'num_temps': '0\u001f' * len(self.types)
        }

    def check_variable_exists(self, var):
        if self.current_class != None:
            return var in self.function_table[self.curr_scope]['vars'] or var in self.class_table[self.current_class]['vars']
        return var in self.function_table[self.curr_scope]['vars'] or var in self.function_table[self.program_name]['vars']

    def get_var_type(self, var):
        if self.current_class != None:
            if var in self.function_table[self.curr_scope]['vars']:
                return self.function_table[self.curr_scope]['vars'][var]['type']
            return self.class_table[self.current_class]['vars'][var]['type']
        if var in self.function_table[self.curr_scope]['vars']:
            return self.function_table[self.curr_scope]['vars'][var]['type']
        return self.function_table[self.program_name]['vars'][var]['type']

    def update_num_temps(self, func_num_temps, type_idx, quantity=1):
        lst = func_num_temps.split('\u001f')
        lst[type_idx] = str(int(lst[type_idx]) + quantity)
        return '\u001f'.join(lst)

    def check_var_is_array(self, var):
        if not self.check_variable_exists(var):
            return False
        if self.current_class != None:
            if var in self.class_table[self.current_class]['vars']:
                return 'd1' in self.class_table[self.current_class]['vars'][var]
            else:
                return 'd1' in self.function_table[self.curr_scope]['vars'][var]
        elif var in self.function_table[self.curr_scope]['vars']:
            return 'd1' in self.function_table[self.curr_scope]['vars'][var]
        else:
            return 'd1' in self.function_table[self.program_name]['vars'][var]

    def make_and_push_quad(self):
        ro = self.stack_of_stacks[-2].pop()
        lo = self.stack_of_stacks[-2].pop()
        op = self.stack_of_stacks[-1].pop()
        r_type = sm.checkOperation(lo['type'], ro['type'], op)
        self.last_type = r_type
        idx = self.types.index(r_type)
        num_temps = self.function_table[self.curr_scope]['num_temps']
        self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            num_temps, idx)
        t_dir = idx * 300 + \
            int(num_temps.split('\u001f')[idx]) + 3000
        self.stack_of_stacks[-2].append(
            {'value': 't' + str(self.temp_counter), 'type': r_type, 'dir': t_dir})
        if self.check_var_is_array(lo['value']):
            lo_dir = '$' + str(self.last_arr_t.pop())
        else:
            lo_dir = lo['dir']
        if self.check_var_is_array(ro['value']):
            ro_dir = '$' + str(self.last_arr_t.pop())
        else:
            ro_dir = ro['dir']
        self.quadruples.append(
            Quadruple(lo_dir, ro_dir, op, t_dir))
        self.temp_counter += 1
        self.quad_counter += 1

    @_('PROGRAM ID pro1 SEMI pro0 declarations', 'PROGRAM error SEMI')
    def programa(self, p):
        if hasattr(p, 'error'):
            print('Error on line', p.lineno)
        func_dir_out = open('debug/funcdir.out', 'w')
        class_dir_out = open('debug/classdir.out', 'w')
        func_dir_out.write(json.dumps(
            self.function_table, indent=2))
        class_dir_out.write(json.dumps(
            self.class_table, indent=2))
        return (self.program_name, self.function_table, self.class_table, self.constant_table, self.quadruples)

    @_('')
    def pro0(self, p):
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.quad_counter += 1

    @_('')
    def pro1(self, p):
        if p[-1] == 'main':
            raise ReservedWordError('main', 'program name')
        self.program_name = p[-1]
        self.curr_scope = p[-1]
        self.function_table[p[-1]] = {'return_type': None,
                                      'vars': {}, 'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'}

    @ _('class_declaration out_class var_declaration function_definition main')
    def declarations(self, p):
        return 'declarations'

    @ _('''CLASS ID cd1 inherits LCURL ATTRIBUTES attribute_declaration METHODS
          method_definition RCURL class_declaration''', 'empty')
    def class_declaration(self, p):
        return 'class_declaration'

    @ _('')
    def cd1(self, p):
        if p[-1] == 'main':
            raise ReservedWordError('main', 'class name')
        if p[-1] == self.program_name or p[-1] in self.class_table:
            raise RedefinitionError(p[-1])
        else:
            self.class_table[p[-1]] = {'vars': {},
                                       'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'}
            self.current_class = p[-1]

    @ _('INHERITS ID cd3', 'empty')
    def inherits(self, p):
        return 'inherits'

    @ _('')
    def cd3(self, p):
        if not p[-1] in self.class_table:
            raise UndeclaredIdError(p[-1])
        else:
            self.class_table[self.current_class] = copy.deepcopy(
                self.class_table[p[-1]])

    @ _('VAR ID ad1 attr_vector', 'VAR ID ad1 attr_simple_var', 'empty')
    def attribute_declaration(self, p):
        return 'attribute_declaration'

    @ _('')
    def ad1(self, p):
        if (p[-1] == self.program_name or
                p[-1] in self.class_table or
                p[-1] in self.class_table[self.current_class]['vars']):
            raise RedefinitionError(p[-1])
        else:
            self.stack_vars.append(p[-1])

    @ _('''LBRACKET CTE_I ad2 attr_multidim RBRACKET COLON simple_type ad4 SEMI
           attribute_declaration''')
    def attr_vector(self, p):
        return 'vector'

    @ _('')
    def ad2(self, p):
        self.latest_var = self.stack_vars.pop()
        if self.class_table[self.current_class]['vars']:
            self.class_table[self.current_class]['vars'][self.latest_var] = {
                'd1': p[-1]}
        else:
            self.class_table[self.current_class]['vars'] = {
                self.latest_var: {'d1': p[-1]}}

    @ _('COMMA CTE_I ad3', 'empty')
    def attr_multidim(self, p):
        return 'attr_multidim'

    @ _('')
    def ad3(self, p):
        self.class_table[self.current_class]['vars'][self.latest_var]['d2'] = p[-1]

    @ _('')
    def ad4(self, p):
        idx = self.types.index(p[-1])
        num_types = self.class_table[self.current_class]['num_types']
        if 'd1' in self.class_table[self.current_class]['vars'][self.latest_var]:
            q = self.class_table[self.current_class]['vars'][self.latest_var]['d1']
        if 'd2' in self.class_table[self.current_class]['vars'][self.latest_var]:
            q *= self.class_table[self.current_class]['vars'][self.latest_var]['d2']
        self.class_table[self.current_class]['vars'][self.latest_var]['dir'] = 6000 + idx * \
            300 + int(num_types.split('\u001f')[idx])
        self.class_table[self.current_class]['vars'][self.latest_var]['type'] = p[-1]
        self.class_table[self.current_class]['num_types'] = self.update_num_temps(
            num_types, idx, q)

    @ _('attr_var_list COLON simple_type ad5 SEMI attribute_declaration')
    def attr_simple_var(self, p):
        return 'attr_simple_var'

    @ _('COMMA ID ad1 attr_var_list', 'empty')
    def attr_var_list(self, p):
        return 'attr_var_list'

    @ _('')
    def ad5(self, p):
        while len(self.stack_vars) > 0:
            curr_var = self.stack_vars.pop()
            if (curr_var == self.program_name or
                    curr_var in self.class_table or
                    curr_var in self.class_table[self.current_class]['vars']):
                raise RedefinitionError(curr_var)
            idx = self.types.index(p[-1])
            num_types = self.class_table[self.current_class]['num_types']
            self.class_table[self.current_class]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.class_table[self.current_class]['vars'][curr_var] = {
                'type': p[-1], 'dir': 6000 + idx * 300 + int(num_types.split('\u001f')[idx])}

    @ _('''def_type fd1_current_type FUNCTION ID md3 LPAREN m_parameters
           RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6
           method_definition''', 'empty')
    def method_definition(self, p):
        return 'method_definition'

    # @ _('')
    # def md6(self, p):
    #     if self.curr_func_type != 'void' and self.has_returned == False:
    #         raise SyntaxError(
    #             f'No return type for function {self.last_func_added}')
    #     self.quadruples.append(Quadruple(-1, -1, 'end_meth', -1))
    #     self.quad_counter += 1
    #     self.temp_counter = 1
    #     self.has_returned = False

    @ _('')
    def md3(self, p):
        if (p[-1] == self.program_name or
                p[-1] in self.class_table or
                p[-1] in self.class_table[self.current_class]['vars'] or
                p[-1] in self.class_table[self.current_class]):
            raise RedefinitionError(p[-1])
        else:
            self.add_to_func_table(
                self.current_class + '.' + p[-1], self.curr_func_type)
            self.last_func_added = self.current_class + '.' + p[-1]
            self.curr_scope = self.last_func_added
            idx = self.types.index(self.curr_func_type)
            num_types = self.function_table[self.program_name]['num_types']
            self.function_table[self.program_name]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.function_table[self.program_name]['vars'][self.current_class + '.' + p[-1]] = {
                'type': self.curr_func_type, 'dir': 0, 'real_dir': idx * 300 + int(num_types.split('\u001f')[idx])}

    @_('ID p1 COLON simple_type m2 m_param_choose', 'empty')
    def m_parameters(self, p):
        return 'parameters'

    @ _('')
    def m2(self, p):
        if self.latest_var in self.function_table[self.curr_scope]['vars']:
            raise RedefinitionError({self.latest_var})
        else:
            idx = self.types.index(p[-1])
            self.function_table[self.curr_scope]['params'] += str(
                idx)
            num_types = self.function_table[self.curr_scope]['num_types']
            self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.function_table[self.curr_scope]['vars'][self.latest_var] = {
                'type': p[-1], 'dir': 1500 + idx * 300 + int(num_types.split('\u001f')[idx])}

    @ _('COMMA m_parameters', 'empty')
    def m_param_choose(self, p):
        return 'm_param_choose'

    @ _('')
    def out_class(self, p):
        self.current_class = None
        self.curr_scope = self.program_name

    @ _('VAR ID gvd1 vector', 'VAR ID gvd1 simple_var', 'empty')
    def var_declaration(self, p):
        return 'var_declaration'

    @ _('')
    def gvd1(self, p):
        if p[-1] == self.program_name or p[-1] in self.function_table or p[-1] in self.class_table:
            raise RedefinitionError(p[-1])
        elif self.current_class != None and p[-1] in self.class_table[self.current_class]:
            raise RedefinitionError(p[-1])
        else:
            self.stack_vars.append(p[-1])

    @ _('LBRACKET CTE_I gvd2 multidim RBRACKET COLON simple_type gvd4 SEMI var_declaration')
    def vector(self, p):
        return 'vector'

    @ _('')
    def gvd2(self, p):
        self.latest_var = self.stack_vars.pop()
        if self.function_table[self.curr_scope]['vars']:
            self.function_table[self.curr_scope]['vars'][self.latest_var] = {
                'd1': p[-1]}
        else:
            self.function_table[self.curr_scope]['vars'] = {
                self.latest_var: {'d1': p[-1]}}

    @ _('COMMA CTE_I gvd3', 'empty')
    def multidim(self, p):
        return 'multidim'

    @ _('var_list COLON composite_type gvd6 SEMI var_declaration', 'var_list COLON simple_type gvd5 SEMI var_declaration')
    def simple_var(self, p):
        return 'simple_var'

    @ _('COMMA ID gvd1 var_list', 'empty')
    def var_list(self, p):
        return 'var_list'

    @ _('')
    def gvd3(self, p):
        self.function_table[self.curr_scope]['vars'][self.latest_var]['d2'] = p[-1]

    @ _('')
    def gvd4(self, p):
        idx = self.types.index(p[-1])
        num_types = self.function_table[self.curr_scope]['num_types']
        offset = 1500 if self.curr_scope != self.program_name else 0
        if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
            q = self.function_table[self.curr_scope]['vars'][self.latest_var]['d1']
        if 'd2' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
            q *= self.function_table[self.curr_scope]['vars'][self.latest_var]['d2']
        self.function_table[self.curr_scope]['vars'][self.latest_var]['dir'] = idx * \
            300 + int(num_types.split('\u001f')[idx]) + offset
        self.function_table[self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]
        self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
            num_types, idx, q)

    @ _('')
    def gvd5(self, p):
        while len(self.stack_vars) > 0:
            curr_var = self.stack_vars.pop()
            idx = self.types.index(p[-1])
            num_types = self.function_table[self.curr_scope]['num_types']
            offset = 1500 if self.curr_scope != self.program_name else 0
            self.function_table[self.curr_scope]['vars'][curr_var] = {
                'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx]) + offset}
            self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                num_types, idx)

    @ _('')
    def gvd6(self, p):
        while len(self.stack_vars) > 0:
            var_id = self.stack_vars.pop()
            offset = 1500 if self.curr_scope != self.program_name else 0
            num_types = self.function_table[self.curr_scope]['num_types']
            base_addrs = [int(n) for n in num_types.split('\u001f')[:-1]]
            for attr in self.class_table[p[-1]]['vars']:
                attr_type = self.class_table[p[-1]]['vars'][attr]['type']
                idx = self.types.index(attr_type)
                num_types = self.function_table[self.curr_scope]['num_types']
                q = 1
                self.function_table[self.curr_scope]['vars'][var_id + '.' + attr] = {
                    'type': attr_type,
                    'dir': base_addrs[idx] + self.class_table[p[-1]]['vars'][attr]['dir'] - 6000 + offset
                }
                if 'd1' in self.class_table[p[-1]]['vars'][attr]:
                    q = self.class_table[p[-1]]['vars'][attr]['d1']
                    self.function_table[self.curr_scope]['vars'][var_id +
                                                                 '.' + attr]['d1'] = q
                if 'd2' in self.class_table[p[-1]]['vars'][attr]:
                    d2 = self.class_table[p[-1]]['vars'][attr]['d2']
                    q *= d2
                    self.function_table[self.curr_scope]['vars'][var_id +
                                                                 '.' + attr]['d2'] = d2
                self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                    num_types, idx, q)
            self.function_table[self.curr_scope]['vars'][var_id] = {
                'type': p[-1]}

    @ _('def_type fd1_current_type FUNCTION ID fd3_add_to_func_table LPAREN parameters RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6 function_definition', 'empty')
    def function_definition(self, p):
        return 'function_definition'

    @ _('')
    def fd1_current_type(self, p):
        self.curr_func_type = p[-1]

    @ _('')
    def fd3_add_to_func_table(self, p):
        if p[-1] in self.function_table or p[-1] in self.class_table or p[-1] in self.function_table[self.program_name]['vars']:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.add_to_func_table(p[-1], self.curr_func_type)
            self.last_func_added = p[-1]
            self.curr_scope = self.last_func_added
            idx = self.types.index(self.curr_func_type)
            num_types = self.function_table[self.program_name]['num_types']
            self.function_table[self.program_name]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.function_table[self.program_name]['vars'][p[-1]] = {
                'type': self.curr_func_type, 'dir': 0, 'real_dir': idx * 300 + int(num_types.split('\u001f')[idx])}

    @ _('')
    def fd4(self, p):
        self.function_table[self.last_func_added]['start'] = self.quad_counter

    @ _('')
    def fd5(self, p):
        del self.function_table[self.last_func_added]['vars']
        pass

    @ _('')
    def fd6(self, p):
        if self.curr_func_type != 'void' and self.has_returned == False:
            raise SyntaxError(
                f'No return type for function {self.last_func_added}')
        self.quadruples.append(Quadruple(-1, -1, 'end_func', -1))
        self.quad_counter += 1
        self.temp_counter = 1
        self.has_returned = False

    @ _('statement statements', 'empty')
    def statements(self, p):
        return 'statements'

    @ _('simple_type', 'VOID')
    def def_type(self, p):
        return p[0]

    @ _('INT', 'FLOAT', 'STRING', 'BOOL')
    def simple_type(self, p):
        return p[0]

    @ _('ID')
    def composite_type(self, p):
        return p[0]

    @ _('ID p1 COLON simple_type p2 param_choose', 'empty')
    def parameters(self, p):
        return 'parameters'

    @ _('COMMA parameters', 'empty')
    def param_choose(self, p):
        return 'param_choose'

    @ _('')
    def p1(self, p):
        self.latest_var = p[-1]

    @ _('')
    def p2(self, p):
        if self.latest_var in self.function_table[self.curr_scope]['vars']:
            raise SyntaxError(f'{p[-1]} already declared as parameter')
        idx = self.types.index(p[-1])
        self.function_table[self.curr_scope]['params'] += str(idx)
        num_types = self.function_table[self.curr_scope]['num_types']
        offset = 1500 if self.curr_scope != self.program_name else 0
        self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
            num_types, idx)
        self.function_table[self.curr_scope]['vars'][self.latest_var] = {
            'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx]) + offset}

    @_('assignment', 'call_to_void_function', 'function_returns', 'read', 'print',
       'decision_statement', 'repetition_statement', 'BREAK br0 SEMI')
    def statement(self, p):
        return 'statement'

    @_('')
    def br0(self, p):
        if len(self.jumps) == 0:
            raise SyntaxError(':(')
        self.quadruples.append(Quadruple(-1, -1, 'goto', None))
        self.break_stack.append(self.quad_counter)
        self.quad_counter += 1

    @_('variable ass1 EQUALS expression ass2 SEMI', 'variable ass1 EQUALS error SEMI')
    def assignment(self, p):
        if hasattr(p, 'error'):
            print('Error in assignment on line', p.lineno)
        return 'assignment'

    @_('')
    def ass1(self, p):
        if self.current_class != None:
            if not p[-1] in self.function_table[self.curr_scope]['vars'] and not p[-1] in self.class_table[self.current_class]['vars']:
                raise SyntaxError(f'Variable {p[-1]} is not declared')
            self.latest_var = p[-1]
        else:
            self.latest_var = p[-1]

    @_('')
    def ass2(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            self.make_and_push_quad()
            made_quad = True
        lo = self.stack_of_stacks[-2].pop()
        v_type = self.get_var_type(self.latest_var)
        self.last_type = sm.checkOperation(v_type, lo['type'], '=')
        if not made_quad and self.check_var_is_array(lo['value']):
            lo_dir = '$' + str(self.last_arr_t.pop())
        else:
            lo_dir = lo['dir']
        if self.current_class != None:
            if self.latest_var in self.class_table[self.current_class]['vars']:
                if 'd1' in self.class_table[self.current_class]['vars'][self.latest_var]:
                    var_dir = '$' + str(self.last_arr_t.pop())
                else:
                    var_dir = self.class_table[self.current_class]['vars'][self.latest_var]['dir']
            else:
                if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
                    var_dir = '$' + str(self.last_arr_t.pop())
                else:
                    var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
        elif self.latest_var in self.function_table[self.curr_scope]['vars']:
            if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
        else:
            if 'd1' in self.function_table[self.program_name]['vars'][self.latest_var]:
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = self.function_table[self.program_name]['vars'][self.latest_var]['dir']
        q = Quadruple(lo_dir, -1, '=', var_dir)
        self.quadruples.append(q)
        self.quad_counter += 1

    @_('id_or_attribute', 'id_or_attribute v0 LBRACKET expression v1 RBRACKET',
        'id_or_attribute v0 LBRACKET expression v2 COMMA v4 expression v3 RBRACKET')
    def variable(self, p):
        return p[0]

    @_('')
    def v0(self, p):
        self.check_variable_exists(p[-1])
        if self.current_class != None:
            if not 'd1' in self.class_table[self.current_class]['vars'][p[-1]]:
                raise TypeError(f'{p[-1]} is not an array or vector')
        elif p[-1] in self.function_table[self.curr_scope]['vars']:
            if not 'd1' in self.function_table[self.curr_scope]['vars'][p[-1]]:
                raise TypeError(f'{p[-1]} is not an array or vector')
        else:
            if not 'd1' in self.function_table[self.program_name]['vars'][p[-1]]:
                raise TypeError(f'{p[-1]} is not an array or vector')
        self.last_arr_id = p[-1]
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @_('')
    def v4(self, p):
        self.check_variable_exists(self.last_arr_id)
        if self.current_class != None:
            if not 'd2' in self.class_table[self.current_class]['vars'][self.last_arr_id]:
                raise TypeError(
                    f'{self.last_arr_id} is not an array or vector')
        elif self.last_arr_id in self.function_table[self.curr_scope]['vars']:
            if not 'd2' in self.function_table[self.curr_scope]['vars'][self.last_arr_id]:
                raise TypeError(
                    f'{self.last_arr_id} is not an array or vector')
        else:
            if not 'd2' in self.function_table[self.program_name]['vars'][self.last_arr_id]:
                raise TypeError(
                    f'{self.last_arr_id} is not an array or vector')
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @_('')
    def v1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + \
                int(num_temps.split('\u001f')[idx]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        elif self.last_arr_id in self.function_table[self.curr_scope]['vars']:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['d1']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['dir']
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0)
            self.quadruples.append(Quadruple(cons_dir, t_addr, '+', t_dir))
            self.quad_counter += 1
            self.last_arr_t.append(t_dir)
        else:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.program_name]['vars'][self.last_arr_id]['d1']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_table[self.program_name]['vars'][self.last_arr_id]['dir']
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0)
            self.quadruples.append(Quadruple(cons_dir, t_addr, '+', t_dir))
            self.quad_counter += 1
            self.last_arr_t.append(t_dir)
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @_('')
    def v2(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + \
                int(num_temps.split('\u001f')[idx]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        elif self.last_arr_id in self.function_table[self.curr_scope]['vars']:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['d1']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            d2 = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['d2']
            if not d2 in self.constant_table['int']:
                self.constant_table['int'].append(d2)
            cons_dir = self.constant_table['int'].index(d2) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0)
            self.quadruples.append(Quadruple(cons_dir, t_addr, '*', t_dir))
            self.quad_counter += 1
            self.displacements.append(t_dir)
        else:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.program_name]['vars'][self.last_arr_id]['d1']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            d2 = self.function_table[self.program_name]['vars'][self.last_arr_id]['d2']
            if not d2 in self.constant_table['int']:
                self.constant_table['int'].append(d2)
            cons_dir = self.constant_table['int'].index(d2) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0)
            self.quadruples.append(Quadruple(cons_dir, t_addr, '*', t_dir))
            self.quad_counter += 1
            self.displacements.append(t_dir)
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @_('')
    def v3(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + \
                int(num_temps.split('\u001f')[idx]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        elif self.last_arr_id in self.function_table[self.curr_scope]['vars']:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['d2']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_table[self.curr_scope]['vars'][self.last_arr_id]['dir']
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0, 2)
            self.quadruples.append(
                Quadruple(self.displacements.pop(), t_addr, '+', t_dir))
            self.quadruples.append(Quadruple(cons_dir, t_dir, '+', t_dir + 1))
            self.quad_counter += 2
            self.last_arr_t.append(t_dir + 1)
        else:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.function_table[self.program_name]['vars'][self.last_arr_id]['d2']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_table[self.program_name]['vars'][self.last_arr_id]['dir']
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = int(num_temps.split('\u001f')[0]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 0, 2)
            self.quadruples.append(
                Quadruple(self.displacements.pop(), t_addr, '+', t_dir))
            self.quadruples.append(Quadruple(cons_dir, t_dir, '+', t_dir + 1))
            self.quad_counter += 2
            self.last_arr_t.append(t_dir + 1)
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @_('ID', 'ID DOT ID')
    def id_or_attribute(self, p):
        if len(p) > 1:
            return p[0] + p[1] + p[2]
        return p[0]

    @_('variable', 'CTE_I', 'CTE_F', 'CTE_STRING', 'cte_bool', 'call_to_function')
    def var_cte(self, p):
        offset = 4500
        if hasattr(p, 'CTE_I'):
            cte_type = 'int'
            if not p[0] in self.constant_table['int']:
                self.constant_table['int'].append(p[0])
            cons_dir = self.constant_table['int'].index(p[0]) + offset
        elif hasattr(p, 'CTE_F'):
            cte_type = 'float'
            if not p[0] in self.constant_table['float']:
                self.constant_table['float'].append(p[0])
            cons_dir = self.constant_table['float'].index(p[0]) + offset + 300
        elif hasattr(p, 'CTE_STRING'):
            cte_type = 'string'
            if not p[0] in self.constant_table['string']:
                self.constant_table['string'].append(p[0])
            cons_dir = self.constant_table['string'].index(p[0]) + offset + 600
        elif hasattr(p, 'cte_bool'):
            cte_type = 'bool'
            if not p[0] in self.constant_table['bool']:
                self.constant_table['bool'].append(p[0])
            cons_dir = self.constant_table['bool'].index(p[0]) + offset + 900
        elif hasattr(p, 'call_to_function'):
            return p[0]
        else:
            whole_p = p[0] + p[1] + p[2] if len(p) == 3 else p[0]
            if not self.check_variable_exists(whole_p):
                raise SyntaxError(f'Variable {whole_p} is not declared')
            if self.current_class != None:
                if whole_p in self.class_table[self.current_class]['vars']:
                    cte_type = self.class_table[self.current_class]['vars'][whole_p]['type']
                    var_dir = self.class_table[self.current_class]['vars'][whole_p]['dir']
                else:
                    cte_type = self.function_table[self.curr_scope]['vars'][whole_p]['type']
                    var_dir = self.function_table[self.curr_scope]['vars'][whole_p]['dir']
                return {'value': whole_p, 'type': cte_type, 'dir': var_dir}
            else:
                cte_type = self.get_var_type(whole_p)
                if whole_p in self.function_table[self.curr_scope]['vars']:
                    var_dir = self.function_table[self.curr_scope]['vars'][whole_p]['dir']
                else:
                    var_dir = self.function_table[self.program_name]['vars'][whole_p]['dir']
                return {'value': whole_p, 'type': cte_type, 'dir': var_dir}

        return {'value': p[0], 'type': cte_type, 'dir': cons_dir}

    @_('constant e2 operator e3 expression', 'constant e2', 'LPAREN e1 expression RPAREN e4', 'LPAREN e1 expression RPAREN e4 operator e3 expression')
    def expression(self, p):
        if hasattr(p, 'LPAREN'):
            return p[2]
        return p[0]

    @_('')
    def e1(self, p):
        self.stack_of_stacks[-1].append('(')

    @_('')
    def e2(self, p):
        self.stack_of_stacks[-2].append(p[-1])

    @_('')
    def e3(self, p):
        if len(self.stack_of_stacks[-1]) == 0 or self.stack_of_stacks[-1][-1] == '(':
            self.stack_of_stacks[-1].append(p[-1])
        elif self.stack_of_stacks[-1][-1] == '*' or self.stack_of_stacks[-1][-1] == '/':
            self.make_and_push_quad()
            if (self.stack_of_stacks[-1] and (self.stack_of_stacks[-1][-1] == '+' or self.stack_of_stacks[-1][-1] == '-')) and (p[-1] == '+' or p[-1] == '-'):
                self.make_and_push_quad()
            self.stack_of_stacks[-1].append(p[-1])
        elif p[-1] == '*' or p[-1] == '/':
            self.stack_of_stacks[-1].append(p[-1])
        elif self.stack_of_stacks[-1][-1] == '+' or self.stack_of_stacks[-1][-1] == '-':
            self.make_and_push_quad()
            self.stack_of_stacks[-1].append(p[-1])
        elif p[-1] == '+' or p[-1] == '-':
            self.stack_of_stacks[-1].append(p[-1])
        elif self.stack_of_stacks[-1][-1] in sm.comparison_ops or self.stack_of_stacks[-1][-1] in sm.equality_ops:
            self.make_and_push_quad()
            self.stack_of_stacks[-1].append(p[-1])
        elif p[-1] in sm.comparison_ops or p[-1] in sm.equality_ops:
            self.stack_of_stacks[-1].append(p[-1])
        elif self.stack_of_stacks[-1][-1] in sm.logic_ops:
            self.make_and_push_quad()
            self.stack_of_stacks[-1].append(p[-1])
        elif p[-1] in sm.logic_ops:
            self.stack_of_stacks[-1].append(p[-1])

    @_('')
    def e4(self, p):
        while(self.stack_of_stacks[-1][-1] != '('):
            self.make_and_push_quad()
        self.stack_of_stacks[-1].pop()

    @_('AND', 'OR')
    def logical_operator(self, p):
        return p[-1]

    @_('LT', 'GT', 'SAME', 'GEQ', 'LEQ', 'NEQ')
    def relational_operator(self, p):
        return p[0]

    @_('PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE')
    def arithmetic_operator(self, p):
        return p[0]

    @_('logical_operator', 'relational_operator', 'arithmetic_operator')
    def operator(self, p):
        return p[0]

    @_('PLUS var_cte', 'MINUS var_cte', 'var_cte')
    def constant(self, p):
        if len(p) > 1 and p[1] == '-':
            return -p.var_cte
        else:
            return p.var_cte

    @_('READ LPAREN read_h')
    def read(self, p):
        return 'read'

    @_('variable r1 COMMA read_h', 'variable r1 RPAREN SEMI', 'error RPAREN SEMI')
    def read_h(self, p):
        if hasattr(p, 'error'):
            print("Error with read on line", p.lineno)
        return 'read_h'

    @_('')
    def r1(self, p):
        if p[-1] in self.function_table[self.curr_scope]['vars']:
            if self.check_var_is_array(p[-1]):
                var_addr = '$' + str(self.last_arr_t.pop())
            else:
                var_addr = self.function_table[self.curr_scope]['vars'][p[-1]]['dir']
        elif p[-1] in self.function_table[self.program_name]['vars']:
            if self.check_var_is_array(p[-1]):
                var_addr = '$' + str(self.last_arr_t.pop())
            else:
                var_addr = self.function_table[self.program_name]['vars'][p[-1]]['dir']
        else:
            raise UndeclaredIdError(p[-1])
        self.quadruples.append(Quadruple(-1, -1, 'read', var_addr))
        self.quad_counter += 1

    @_('function_or_method vf0 ctf2 LPAREN func_params RPAREN fp2 fp3 ctf0 ctf3')
    def call_to_function(self, p):
        func_dir = self.function_table[self.program_name]['vars'][self.called_func]['dir']
        func_type = self.function_table[self.called_func]['return_type']
        return {'value': 't' + str(self.temp_counter - 1), 'type': func_type, 'dir': func_dir}

    @_('')
    def ctf2(self, p):
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @_('')
    def ctf3(self, p):
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @_('')
    def ctf0(self, p):
        func_dir = self.function_table[self.program_name]['vars'][self.called_func]['real_dir']
        func_type = self.function_table[self.program_name]['vars'][self.called_func]['type']
        idx = self.types.index(func_type)
        num_temps = self.function_table[self.curr_scope]['num_temps']
        # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
        #     num_temps, idx)
        t_dir = idx * 300 + \
            int(num_temps.split('\u001f')[idx]) + 3000
        self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            num_temps, idx)
        self.quadruples.append(
            Quadruple(func_dir, -1, '=', t_dir))
        self.function_table[self.program_name]['vars'][self.called_func]['dir'] = t_dir
        self.quad_counter += 1
        self.temp_counter += 1

    @_('ID ctf1_exists_in_func_table', 'ID DOT ID')
    def function_or_method(self, p):
        if(len(p) == 2):
            return (p[0], None)
        else:
            var_type = self.get_var_type(p[0])
            quads = []
            for attr in self.class_table[var_type]['vars']:
                var_dir = self.function_table[self.curr_scope]['vars'][p[0]+'.'+attr]['dir']
                attr_dir = self.class_table[var_type]['vars'][attr]['dir']
                print(var_dir, attr_dir)
                quads.append(Quadruple(var_dir, -2, '=', attr_dir))
                # self.quad_counter += 1
            return (var_type + p[1] + p[2], quads)

    @_('')
    def ctf1_exists_in_func_table(self, p):
        if not p[-1] in self.function_table:
            # print(p.lineno)
            # self.error(p)
            raise SyntaxError('Wey noooo')
        else:
            pass

    @_('COMMA expression fp1 param_list', 'empty')
    def param_list(self, p):
        return 'param_list'

    @_('PRINT LPAREN res_write RPAREN SEMI', 'PRINT LPAREN error RPAREN SEMI')
    def print(self, p):
        if hasattr(p, 'error'):
            print('Error with print on line', p.lineno)
        return 'print'

    @_('expression pr1 comma_thing')
    def res_write(self, p):
        return 'res_write'

    @_('COMMA res_write', 'empty')
    def comma_thing(self, p):
        return 'comma_thing'

    @_('')
    def pr1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + \
                int(num_temps.split('\u001f')[idx]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            if not lo['dir'] in range(4500, 6000) and self.check_var_is_array(lo['value']):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if not ro['dir'] in range(4500, 6000) and self.check_var_is_array(ro['value']):
                ro_dir = '$' + str(self.last_arr_t.pop())
            else:
                ro_dir = ro['dir']
            self.quadruples.append(
                Quadruple(lo_dir, ro_dir, op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                Quadruple(-1, -1, 'print', last_quad.res))
            self.quad_counter += 1
        else:
            var = self.stack_of_stacks[-2].pop()
            if not var['dir'] in range(4500, 6000) and self.check_var_is_array(var['value']):
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = var['dir']
            self.quadruples.append(
                Quadruple(-1, -1, 'print', var_dir))
            self.quad_counter += 1

    @_('TRUE', 'FALSE')
    def cte_bool(self, p):
        return p[0]

    @_('IF LPAREN expression dec1 RPAREN THEN LCURL statements RCURL else_stm')
    def decision_statement(self, p):
        return 'decision_statement'

    @_('')
    def dec1(self, p):
        while len(self.stack_of_stacks[-1]):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + 3000
            r_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.stack_of_stacks[-2].append(
                {'value': 't' + str(self.temp_counter), 'type': r_type, 'dir': t_dir})
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            if self.check_var_is_array(lo['value']):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if self.check_var_is_array(ro['value']):
                ro_dir = '$' + str(self.last_arr_t.pop())
            else:
                ro_dir = ro['dir']
            self.quadruples.append(
                Quadruple(lo_dir, ro_dir, op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1

        lo = self.stack_of_stacks[-2].pop()
        if lo['type'] != 'bool':
            raise SyntaxError(
                'Expression to evaluate in if statement is not boolean')
        else:
            self.quadruples.append(Quadruple(-1, lo['dir'], 'goto_f', -1))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1

    @_('dec2 ELSE LCURL statements RCURL dec3', 'empty dec4')
    def else_stm(self, p):
        return 'else_stm'

    @_('')
    def dec2(self, p):
        falso = self.jumps.pop()
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1
        self.quadruples[falso - 1].res = self.quad_counter

    @_('')
    def dec3(self, p):
        jump = self.jumps.pop()
        self.quadruples[jump - 1].res = self.quad_counter

    @_('')
    def dec4(self, p):
        jump = self.jumps.pop()
        self.quadruples[jump - 1].res = self.quad_counter

    @_('conditional', 'non_conditional')
    def repetition_statement(self, p):
        return 'repetition_statement'

    @_('WHILE LPAREN con0 expression con1 RPAREN DO LCURL statements RCURL con2')
    def conditional(self, p):
        return 'conditional'

    @_('')
    def con0(self, p):
        self.jumps.append(self.quad_counter)

    @_('')
    def con1(self, p):
        while len(self.stack_of_stacks[-1]):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            r_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.stack_of_stacks[-2].append(
                {'value': 't' + str(self.temp_counter), 'type': r_type, 'dir': t_dir})
            if self.check_var_is_array(lo['value']):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if self.check_var_is_array(ro['value']):
                ro_dir = '$' + str(self.last_arr_t.pop())
            else:
                ro_dir = ro['dir']
            self.quadruples.append(
                Quadruple(lo_dir, ro_dir, op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
        if self.last_type != 'bool':
            raise SyntaxError(
                'Expression to evaluate in if statement is not boolean')
        else:
            last_quad = self.quadruples[-1].res
            self.quadruples.append(Quadruple(-1, last_quad, 'goto_f', -1))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1

    @_('')
    def con2(self, p):
        falso = self.jumps.pop()
        ret = self.jumps.pop()
        self.quadruples.append(Quadruple(-1, -1, 'goto', ret))
        self.quadruples[falso - 1].res = self.quad_counter + 1
        if len(self.break_stack):
            bq = self.break_stack.pop()
            self.quadruples[bq - 1].res = self.quad_counter + 1
        self.quad_counter += 1

    @_('FOR variable ass1 EQUALS expression ass2 nc0 UNTIL expression nc1 DO nc2 LCURL statements RCURL nc3')
    def non_conditional(self, p):
        return 'non_conditional'

    @_('')
    def nc0(self, p):
        self.for_var_dir.append(self.quadruples[-1].res)

    @_('')
    def nc1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = idx * 300 + \
                int(num_temps.split('\u001f')[idx]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            if not lo['dir'] in range(4500, 6000) and self.check_var_is_array(lo['value']):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if not ro['dir'] in range(4500, 6000) and self.check_var_is_array(ro['value']):
                ro_dir = '$' + str(self.last_arr_t.pop())
            else:
                ro_dir = ro['dir']
            self.quadruples.append(
                Quadruple(lo_dir, ro_dir, op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1].res
            if (last_quad % 1500) // 300 != 0 and (last_quad % 1500) // 300 != 1:
                raise TypeError("Type mismatch")
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = 3 * 300 + \
                int(num_temps.split('\u001f')[3]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 3)
            self.quadruples.append(
                Quadruple(self.for_var_dir[-1], last_quad, '<=', t_dir))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1
        else:
            var = self.stack_of_stacks[-2].pop()
            if (var['dir'] % 1500) // 300 != 0 and (var['dir'] % 1500) // 300 != 1:
                raise TypeError("Type mismatch")
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = 3 * 300 + \
                int(num_temps.split('\u001f')[3]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 3)
            if self.check_var_is_array(var['value']):
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = var['dir']
            self.quadruples.append(
                Quadruple(self.for_var_dir[-1], var_dir, '<=', t_dir))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1

    @_('')
    def nc2(self, p):
        last_quad = self.quadruples[-1].res
        self.quadruples.append(Quadruple(-1, last_quad, 'goto_f', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1

    @_('')
    def nc3(self, p):
        falso = self.jumps.pop()
        cond = self.jumps.pop()
        if not 1 in self.constant_table['int']:
            self.constant_table['int'].append(1)
        one_dir = self.constant_table['int'].index(1) + 4500
        self.quadruples.append(
            Quadruple(self.for_var_dir[-1], one_dir, '+', self.for_var_dir[-1]))
        self.quad_counter += 1
        self.quadruples.append(Quadruple(-1, -1, 'goto', cond))
        self.quad_counter += 1
        self.quadruples[falso - 1].res = self.quad_counter
        if len(self.break_stack):
            bq = self.break_stack.pop()
            self.quadruples[bq - 1].res = self.quad_counter + 1
        self.for_var_dir.pop()

    @_('RETURN LPAREN expression fr0 RPAREN SEMI fr1', 'RETURN error SEMI')
    def function_returns(self, p):
        if hasattr(p, 'error'):
            print('Error with return on line', p.lineno)
        return 'function_returns'

    @_('')
    def fr0(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            self.make_and_push_quad()
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                Quadruple(last_quad.res, -1, 'return', self.function_table[self.program_name]['vars'][self.curr_scope]['real_dir']))
            self.quad_counter += 1
            self.stack_of_stacks[-2].pop()
        else:
            self.quadruples.append(
                Quadruple(self.stack_of_stacks[-2].pop()['dir'], -1, 'return', self.function_table[self.program_name]['vars'][self.curr_scope]['real_dir']))
            self.quad_counter += 1

    @_('')
    def fr1(self, p):
        self.has_returned = True

    @ _('function_or_method vf0 LPAREN func_params RPAREN fp2 fp3 SEMI', 'function_or_method error SEMI')
    def call_to_void_function(self, p):
        if hasattr(p, 'error'):
            print('Error with call to function on line', p.lineno)
        return 'call_to_void_function'

    @ _('')
    def fp2(self, p):
        self.quadruples.append(
            Quadruple(self.called_func, -1, 'gosub', -1))
        self.quad_counter += 1

    @ _('')
    def fp3(self, p):
        self.param_counter = 0

    @ _('')
    def vf0(self, p):
        self.called_func, quads = p[-1]
        self.quadruples.append(Quadruple(self.called_func, -1, 'era', -1))
        self.quad_counter += 1
        if quads:
            for q in quads:
                self.quadruples.append(q)
                self.quad_counter += 1

    @ _('expression fp1 param_list', 'empty')
    def func_params(self, p):
        return 'func_params'

    @ _('')
    def fp1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            offset = 800 * len(self.types) * 2
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            idx = self.types.index(self.last_type)
            num_temps = self.function_table[self.curr_scope]['num_temps']
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, idx)
            t_dir = idx * 300 + 3000
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, t_dir))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            if self.param_counter == len(self.function_table[self.called_func]['params']):
                raise SyntaxError('Too many params')
            param_type = (last_quad.res % 1500) // 300
            if param_type != int(self.function_table[self.called_func]['params'][self.param_counter]):
                raise TypeError('Type mismatch')
            self.quadruples.append(
                Quadruple(last_quad.res, -1, 'param', self.param_counter))
            self.quad_counter += 1
            self.param_counter += 1
        else:
            val = self.stack_of_stacks[-2].pop()
            if self.param_counter == len(self.function_table[self.called_func]['params']):
                raise SyntaxError('Too many params')
            param_type = (val['dir'] % 1500) // 300
            if param_type != int(self.function_table[self.called_func]['params'][self.param_counter]):
                raise TypeError('Type mismatch')
            self.quadruples.append(
                Quadruple(val['dir'], -1, 'param', self.param_counter))
            self.quad_counter += 1
            self.param_counter += 1

    @ _('MAIN m1_add_to_func_table LPAREN RPAREN LCURL main0 var_declaration statements RCURL main2')
    def main(self, p):
        return 'main'

    @ _('')
    def main0(self, p):
        self.quadruples[0].res = self.quad_counter

    @ _('')
    def main2(self, p):
        self.quadruples.append(Quadruple(-1, -1, 'end', -1))
        del self.function_table[self.program_name]['vars']
        del self.function_table['main']['vars']
        for class_name in self.class_table:
            del self.class_table[class_name]['vars']
        pass

    @ _('')
    def m1_add_to_func_table(self, p):
        self.curr_scope = 'main'
        self.add_to_func_table('main', None)

    @ _('')
    def empty(self, p):
        pass

    def error(self, p):
        # print(p.value in DomasLexer.reserved_words)
        # if p.value in DomasLexer.reserved_words:
        #     raise ReservedWordError(p.value)
        # else:
        print("Syntax error in input!")
