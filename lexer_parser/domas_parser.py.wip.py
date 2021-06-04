from sly import Parser
from sly.yacc import _decorator as _
from .domas_lexer import DomasLexer
from .domas_quadruples import Quadruple
from .domas_errors import *
from .domas_directory import Directory
from . import domas_semantic_cube as sm
import json  # to debug only
import sys
import copy


class DomasParser(Parser):
    # Parser directives
    tokens = DomasLexer.tokens
    debugfile = 'parser.out'
    start = 'programa'
    # Directories
    function_directory = Directory()
    class_directory = Directory()
    function_table = {}
    class_table = {}
    constant_table = {'int': [], 'float': [], 'string': [], 'bool': []}
    # Stacks
    stack_of_stacks = [[], []]  # operands, operators !important
    stack_vars = []
    arr_temps = []
    displacements = []
    for_var_dir = []
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
    curr_scope = None
    last_type = None
    has_returned = False
    types = ['int', 'float', 'string', 'bool', 'void']
    operators = ['+', '-', '*', '/', '<',
                 '>', '<=', '>=', '==', '<>', '&', '|']

    def get_type_from_address(self, address):
        return self.types.index((address % 1500) // 300)

    def add_to_func_table(self, id, return_type):
        self.function_table[id] = {
            'return_type': return_type, 'vars': {}, 'num_types': '0\u001f' * len(self.types), 'params': '', 'num_temps': '0\u001f' * len(self.types)}

    def check_variable_exists(self, var):
        # if self.current_class != None:
        #     return var in self.function_table[self.curr_scope]['vars'] or var in self.class_table[self.current_class]['vars']
        # return var in self.function_table[self.curr_scope]['vars'] or var in self.function_table[self.program_name]['vars']
        if self.current_class != None:
            return self.function_directory.scope_has_id(var, self.curr_scope) or self.class_directory.scope_has_id(var, self.current_class)
        return self.function_directory.scope_has_id(var, self.curr_scope) or self.function_directory.scope_has_id(var, self.program_name)

    def get_var_type(self, var):
        # if self.current_class != None:
        #     if var in self.function_table[self.curr_scope]['vars']:
        if self.current_class != None and self.class_directory.scope_has_id(var, self.current_class):
            # return self.function_table[self.curr_scope]['vars'][var]['type']
            return self.class_directory.get_var_type(var, self.current_class)
            # return self.class_table[self.current_class]['vars'][var]['type']
        # if var in self.function_table[self.curr_scope]['vars']:
        if self.function_directory.scope_has_id(var, self.curr_scope):
            # return self.function_table[self.curr_scope]['vars'][var]['type']
            return self.function_directory.get_var_type(var, self.curr_scope)
        return self.function_directory.get_var_type(var, self.program_name)

    def update_num_temps(self, func_num_temps, type_idx, quantity=1):
        lst = func_num_temps.split('\u001f')
        # print(lst[type_idx])
        lst[type_idx] = str(int(lst[type_idx]) + quantity)
        return '\u001f'.join(lst)

    def check_var_is_array(self, var):
        if not self.check_variable_exists(var):
            return False
        # if self.current_class != None:
        #     if var in self.class_table[self.current_class]['vars']:
        #         return 'd1' in self.class_table[self.current_class]['vars'][var]
        #     else:
        #         return 'd1' in self.function_table[self.curr_scope]['vars'][var]
        # elif var in self.function_table[self.curr_scope]['vars']:
        #     return 'd1' in self.function_table[self.curr_scope]['vars'][var]
        # else:
        #     return 'd1' in self.function_table[self.program_name]['vars'][var]
        if self.current_class != None and self.class_directory.scope_has_id(var, self.current_class):
            return self.class_directory.var_is_array(var, self.current_class)
        elif self.function_directory.scope_has_id(var, self.curr_scope):
            return self.function_directory.var_is_array(var, self.curr_scope)
        else:
            return self.function_directory.var_is_array(var, self.program_name)

    def make_and_push_quad(self):
        # ro = self.stack_of_stacks[-2].pop()
        # lo = self.stack_of_stacks[-2].pop()
        # op = self.stack_of_stacks[-1].pop()
        # # print('ro', ro, 'lo', lo)
        # r_type = sm.checkOperation(lo['type'], ro['type'], op)
        # self.last_type = r_type
        # idx = self.types.index(r_type)
        # num_temps = self.function_table[self.curr_scope]['num_temps']
        # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
        #     num_temps, idx)
        # t_dir = idx * 300 + \
        #     int(num_temps.split('\u001f')[idx]) + 3000
        # self.stack_of_stacks[-2].append(
        #     {'value': 't' + str(self.temp_counter), 'type': r_type, 'dir': t_dir})
        # if self.check_var_is_array(lo['value']):
        #     lo_dir = '$' + str(self.arr_temps.pop())
        # else:
        #     lo_dir = lo['dir']
        # if self.check_var_is_array(ro['value']):
        #     ro_dir = '$' + str(self.arr_temps.pop())
        # else:
        #     ro_dir = ro['dir']
        # self.quadruples.append(
        #     Quadruple(lo_dir, ro_dir, op, t_dir))
        # self.temp_counter += 1
        # self.quad_counter += 1
        ########
        ro = self.stack_of_stacks[-2].pop()
        lo = self.stack_of_stacks[-2].pop()
        op = self.stack_of_stacks[-1].pop()
        r_type = sm.checkOperation(lo['type'], ro['type'], op)
        self.last_type = r_type
        temp = self.function_directory.add_temp(
            self.curr_scope, self.last_type, self.temp_counter)
        self.stack_of_stacks[-2].append(temp)
        if self.check_var_is_array(lo['value']):
            lo_dir = '$' + str(self.arr_temps.pop())
        else:
            lo_dir = lo['dir']
        if self.check_var_is_array(ro['value']):
            ro_dir = '$' + str(self.arr_temps.pop())
        else:
            ro_dir = ro['dir']
        self.quadruples.append(
            Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
        self.temp_counter += 1
        self.quad_counter += 1

    @_('PROGRAM ID pro1 SEMI pro0 declarations')
    def programa(self, p):
        func_dir_out = open('debug/funcdir.out', 'w')
        class_dir_out = open('debug/classdir.out', 'w')
        func_dir_out.write(json.dumps(
            self.function_table, indent=2))
        class_dir_out.write(json.dumps(
            self.class_table, indent=2))
        return (self.program_name, self.function_directory.get_directory(), self.class_directory.get_directory(), self.constant_table, self.quadruples)

    @_('')
    def pro0(self, p):
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.quad_counter += 1

    @_('')
    def pro1(self, p):
        if p[-1] == 'main':
            raise ReservedWordError('main', 'program name')
        self.function_directory.add_scope(p[-1], is_global=True)
        self.program_name = p[-1]
        self.curr_scope = p[-1]
        # self.function_table[p[-1]] = {'return_type': None,
        #                               'vars': {}, 'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'}

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
        # if p[-1] == self.program_name or p[-1] in self.class_table:
        if p[-1] == self.program_name or self.class_directory.has_id(p[-1]):
            raise RedefinitionError(p[-1])
        else:
            self.class_directory.add_scope(p[-1], is_global=True)
            # self.class_table[p[-1]] = {'vars': {},
            #                            'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'}
            self.current_class = p[-1]

    @ _('INHERITS ID cd3', 'empty')
    def inherits(self, p):
        return 'inherits'

    @ _('')
    def cd3(self, p):
        if not p[-1] in self.class_table:
            raise UndeclaredIdError(p[-1])
        else:
            self.class_directory.inherit_content(self.current_class, p[-1])
            # self.class_table[self.current_class] = copy.deepcopy(
            #     self.class_table[p[-1]])

    @ _('VAR ID ad1 attr_vector', 'VAR ID ad1 attr_simple_var', 'empty')
    def attribute_declaration(self, p):
        return 'attribute_declaration'

    @ _('')
    def ad1(self, p):
        if p[-1] == self.program_name or self.class_directory.has_id(self.current_class, p[-1]):
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
        self.class_directory.add_array(
            self.latest_var, self.current_class, p[-1])
        # if self.class_table[self.current_class]['vars']:
        #     self.class_table[self.current_class]['vars'][self.latest_var] = {
        #         'd1': p[-1]}
        # else:
        #     self.class_table[self.current_class]['vars'] = {
        #         self.latest_var: {'d1': p[-1]}}

    @ _('COMMA CTE_I ad3', 'empty')
    def attr_multidim(self, p):
        return 'attr_multidim'

    @ _('')
    def ad3(self, p):
        # self.class_table[self.current_class]['vars'][self.latest_var]['d2'] = p[-1]
        self.class_directory.set_matrix_d2(
            self.latest_var, self.current_class, p[-1])

    @ _('')
    def ad4(self, p):
        # self.class_table[self.current_class]['vars'][self.latest_var]['type'] = p[-1]
        # idx = self.types.index(p[-1])
        # num_types = self.class_table[self.current_class]['num_types']
        # if 'd1' in self.class_table[self.current_class]['vars'][self.latest_var]:
        #     q = self.class_table[self.current_class]['vars'][self.latest_var]['d1']
        # if 'd2' in self.class_table[self.current_class]['vars'][self.latest_var]:
        #     q *= self.class_table[self.current_class]['vars'][self.latest_var]['d2']
        # self.class_table[self.current_class]['vars'][self.latest_var]['dir'] = idx * \
        #     300 + int(num_types.split('\u001f')[idx])
        # self.class_table[self.current_class]['vars'][self.latest_var]['type'] = p[-1]
        # self.class_table[self.current_class]['num_types'] = self.update_num_temps(
        #     num_types, idx, q)
        self.class_directory.set_var_type(
            self.latest_var, self.current_class, p[-1])
        self.class_directory.set_array_address(
            self.latest_var, self.current_class)

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
            # if (curr_var == self.program_name or
            #         curr_var in self.class_table or
            #         curr_var in self.class_table[self.current_class]['vars']):
            if curr_var == self.program_name or self.class_directory.has_id(curr_var, self.current_class):
                raise RedefinitionError(curr_var)
            # idx = self.types.index(p[-1])
            # num_types = self.class_table[self.current_class]['num_types']
            # self.class_table[self.current_class]['num_types'] = self.update_num_temps(
            #     num_types, idx)
            # self.class_table[self.current_class]['vars'][curr_var] = {
            #     'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx])}
            self.class_directory.set_var_type(
                curr_var, self.current_class, p[-1])
            self.class_directory.set_var_address(curr_var, self.current_class)

    @ _('''def_type fd1_current_type FUNCTION ID md3 LPAREN m_parameters
           RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6
           method_definition''', 'empty')
    def method_definition(self, p):
        return 'method_definition'

    @ _('')
    def md3(self, p):
        # if (p[-1] == self.program_name or
        #         p[-1] in self.class_table or
        #         p[-1] in self.class_table[self.current_class]['vars'] or
        #         p[-1] in self.class_table[self.current_class]):
        if p[-1] == self.program_name or self.class_directory.has_id(p[-1], self.current_class):
            raise RedefinitionError(p[-1])
        else:
            # self.add_to_func_table(
            #     self.current_class + '.' + p[-1], self.curr_func_type)
            self.last_func_added = self.current_class + '.' + p[-1]
            self.curr_scope = self.last_func_added
            # idx = self.types.index(self.curr_func_type)
            # num_types = self.function_table[self.program_name]['num_types']
            # self.function_table[self.program_name]['num_types'] = self.update_num_temps(
            #     num_types, idx)
            # self.function_table[self.program_name]['vars'][self.current_class + '.' + p[-1]] = {
            #     'type': self.curr_func_type, 'dir': 0, 'real_dir': idx * 300 + int(num_types.split('\u001f')[idx])}
            self.function_directory.add_scope(
                self.last_func_added, self.curr_func_type)
            self.function_directory.add_function_var(
                self.last_func_added, self.program_name, self.curr_func_type)

    @_('ID p1 COLON simple_type m2 m_param_choose', 'empty')
    def m_parameters(self, p):
        return 'parameters'

    @ _('')
    def m2(self, p):
        # if self.latest_var in self.function_table[self.curr_scope]['vars']:
        if self.function_directory.has_id(self.latest_var, self.curr_scope):
            raise RedefinitionError({self.latest_var})
        else:
            # idx = self.types.index(p[-1])
            # self.function_table[self.curr_scope]['params'] += str(
            #     idx)
            # num_types = self.function_table[self.curr_scope]['num_types']
            # self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
            #     num_types, idx)
            # self.function_table[self.curr_scope]['vars'][self.latest_var] = {
            #     'type': p[-1], 'dir': 1500 + idx * 300 + int(num_types.split('\u001f')[idx])}
            self.function_directory.add_function_parameter(
                self.latest_var, self.curr_scope, p[-1])

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
        # if p[-1] == self.program_name or p[-1] in self.function_table or p[-1] in self.class_table:
        if p[-1] == self.program_name or self.function_directory.has_id(p[-1]) or self.class_directory.has_id(p[-1], self.current_class):
            raise RedefinitionError(p[-1])
        # elif self.current_class != None and p[-1] in self.class_table[self.current_class]:
            # raise RedefinitionError(p[-1])
        else:
            self.stack_vars.append(p[-1])

    @ _('LBRACKET CTE_I gvd2 multidim RBRACKET COLON simple_type gvd4 SEMI var_declaration')
    def vector(self, p):
        return 'vector'

    @ _('')
    def gvd2(self, p):
        self.latest_var = self.stack_vars.pop()
        # if self.function_table[self.curr_scope]['vars']:
        #     self.function_table[self.curr_scope]['vars'][self.latest_var] = {
        #         'd1': p[-1]}
        # else:
        #     self.function_table[self.curr_scope]['vars'] = {
        #         self.latest_var: {'d1': p[-1]}}
        self.function_directory.add_array(
            self.latest_var, self.curr_scope, p[-1])

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
        # self.function_table[self.curr_scope]['vars'][self.latest_var]['d2'] = p[-1]
        self.function_directory.set_matrix_d2(
            self.latest_var, self.curr_scope, p[-1])

    @ _('')
    def gvd4(self, p):
        # idx = self.types.index(p[-1])
        # num_types = self.function_table[self.curr_scope]['num_types']
        # offset = 1500 if self.curr_scope != self.program_name else 0
        # if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
        #     q = self.function_table[self.curr_scope]['vars'][self.latest_var]['d1']
        # if 'd2' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
        #     q *= self.function_table[self.curr_scope]['vars'][self.latest_var]['d2']
        # self.function_table[self.curr_scope]['vars'][self.latest_var]['dir'] = idx * \
        #     300 + int(num_types.split('\u001f')[idx]) + offset
        # self.function_table[self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]
        # self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
        #     num_types, idx, q)
        self.function_directory.set_var_type(
            self.latest_var, self.curr_scope, p[-1])
        self.function_directory.set_array_address(
            self.latest_var, self.curr_scope)

    @ _('')
    def gvd5(self, p):
        while len(self.stack_vars) > 0:
            curr_var = self.stack_vars.pop()
            # idx = self.types.index(p[-1])
            # num_types = self.function_table[self.curr_scope]['num_types']
            offset = 1500 if self.curr_scope != self.program_name else 0
            # self.function_table[self.curr_scope]['vars'][curr_var] = {
            #     'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx]) + offset}
            # self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
            #     num_types, idx)
            self.function_directory.add_variable(
                curr_var, self.curr_scope, p[-1], offset)

    @ _('')
    def gvd6(self, p):
        while len(self.stack_vars) > 0:
            var_id = self.stack_vars.pop()
            offset = 1500 if self.curr_scope != self.program_name else 0
            num_types = self.function_table[self.curr_scope]['num_types']
            base_addrs = [int(n) for n in num_types.split('\u001f')[:-1]]
            for attr in self.class_table[p[-1]]['vars']:
                # attr_type = self.class_table[p[-1]]['vars'][attr]['type']
                idx = self.types.index(attr_type)
                # num_types = self.function_table[self.curr_scope]['num_types']
                # q = 1
                # if 'd1' in self.class_table[p[-1]]['vars'][attr]:
                #     q = self.class_table[p[-1]]['vars'][attr]['d1']
                # if 'd2' in self.class_table[p[-1]]['vars'][attr]:
                #     q *= self.class_table[p[-1]]['vars'][attr]['d2']
                # self.function_table[self.curr_scope]['vars'][var_id + '.' + attr] = {
                #     'type': attr_type, 'dir': base_addrs[idx] + self.class_table[p[-1]]['vars'][attr]['dir'] + offset}
                # self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                #     num_types, idx, q)
                var_name = var_id + '.' + attr
                attr_type = self.class_directory.get_var_type(attr, p[-1])
                if self.class_directory.var_is_array(attr, p[-1]):
                    d1 = self.class_directory.get_var_d1(attr, p[-1])
                    self.function_directory.add_array(
                        var_name, self.curr_scope, d1)
                    if self.class_directory.var_is_matrix(attr, p[-1]):
                        d2 = self.class_directory.get_var_d2(attr, p[-1])
                        self.function_directory.set_matrix_d2(
                            var_name, self.curr_scope, d2)
                    self.function_directory.set_var_type(
                        var_name, self.curr_scope, attr_type)
                    self.function_directory.set_array_address(
                        var_name, self.curr_scope, base_addrs[idx])
                else:
                    self.function_directory.add_variable(
                        var_name, self.curr_scope, attr_type, offset+base_addrs[idx])

            # self.function_table[self.curr_scope]['vars'][var_id] = {
            #     'type': p[-1]}
            self.function_directory.add_object(var_id, self.curr_scope, p[-1])

    @ _('def_type fd1_current_type FUNCTION ID fd3 LPAREN parameters RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6 function_definition', 'empty')
    def function_definition(self, p):
        return 'function_definition'

    @ _('')
    def fd1_current_type(self, p):
        self.curr_func_type = p[-1]

    @ _('')
    def fd3(self, p):
        # if p[-1] in self.function_table or p[-1] in self.class_table or p[-1] in self.function_table[self.program_name]['vars']:
        if self.function_directory.has_id(p[-1], self.program_name) or self.class_directory.has_id(p[-1]):
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            # self.add_to_func_table(p[-1], self.curr_func_type)
            self.last_func_added = p[-1]
            self.curr_scope = self.last_func_added
            # idx = self.types.index(self.curr_func_type)
            # num_types = self.function_table[self.program_name]['num_types']
            # self.function_table[self.program_name]['num_types'] = self.update_num_temps(
            #     num_types, idx)
            # self.function_table[self.program_name]['vars'][p[-1]] = {
            #     'type': self.curr_func_type, 'dir': 0, 'real_dir': idx * 300 + int(num_types.split('\u001f')[idx])}
            self.function_directory.add_scope(
                p[-1], self.curr_func_type)
            self.function_directory.add_function_var(
                p[-1], self.program_name, self.curr_func_type)

    @ _('')
    def fd4(self, p):
        # self.function_table[self.last_func_added]['start'] = self.quad_counter
        self.function_directory.set_function_start(
            self.last_func_added, self.quad_counter)

    @ _('')
    def fd5(self, p):
        # print(self.function_table[self.last_func_added])
        # del self.function_table[self.last_func_added]['vars']
        self.function_directory.delete_var_table(self.last_func_added)

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
        # if self.latest_var in self.function_table[self.curr_scope]['vars']:
        if self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            raise SyntaxError(f'{p[-1]} already declared as parameter')
        # idx = self.types.index(p[-1])
        # self.function_table[self.curr_scope]['params'] += str(idx)
        # num_types = self.function_table[self.curr_scope]['num_types']
        # offset = 1500 if self.curr_scope != self.program_name else 0
        # self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
        #     num_types, idx)
        # self.function_table[self.curr_scope]['vars'][self.latest_var] = {
        #     'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx]) + offset}
        self.function_directory.add_function_parameter(
            self.latest_var, self.curr_scope, p[-1])

    @_('assignment', 'call_to_void_function', 'function_returns', 'read', 'print',
       'decision_statement', 'repetition_statement')
    def statement(self, p):
        return 'statement'

    @_('variable ass1 EQUALS expression ass2 SEMI')
    def assignment(self, p):
        return 'assignment'

    @_('')
    def ass1(self, p):
        # If we're dealing with a method of a class
        if self.current_class != None:
            # if not p[-1] in self.function_table[self.curr_scope]['vars'] and not p[-1] in self.class_table[self.current_class]['vars']:
            if not self.function_directory.scope_has_id(p[-1], self.curr_scope) and not self.class_directory.scope_has_id(p[-1], self.current_class):
                raise SyntaxError(f'Variable {p[-1]} is not declared')
            self.latest_var = p[-1]
        else:
            if not self.function_directory.has_id(p[-1], self.curr_scope) and not self.function_directory.scope_has_id(p[-1], self.program_name):
                raise SyntaxError(f'Variable {p[-1]} is not declared')
            self.latest_var = p[-1]

    @_('')
    def ass2(self, p):
        print('ass2 begin')
        while(len(self.stack_of_stacks[-1])):
            self.make_and_push_quad()
        lo = self.stack_of_stacks[-2].pop()
        v_type = self.get_var_type(self.latest_var)
        self.last_type = sm.checkOperation(v_type, lo['type'], '=')
        if self.current_class != None:
            # if self.latest_var in self.class_table[self.current_class]['vars']:
            if self.class_directory.scope_has_id(self.latest_var, self.current_class):
                # if 'd1' in self.class_table[self.current_class]['vars'][self.latest_var]:
                if self.class_directory.var_is_array(self.latest_var, self.current_class):
                    var_dir = '$' + str(self.arr_temps.pop())
                else:
                    # var_dir =  self.class_table[self.current_class]['vars'][self.latest_var]['dir']
                    var_dir = self.class_directory.get_var_address(
                        self.latest_var, self.current_class)
            else:
                # if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
                if self.function_directory.var_is_array(self.latest_var, self.curr_scope):
                    var_dir = '$' + str(self.arr_temps.pop())
                else:
                    # var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
                    var_dir = self.function_directory.get_var_address(
                        self.latest_var, self.curr_scope)
        # elif self.latest_var in self.function_table[self.curr_scope]['vars']:
        elif self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            # if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
            #     var_dir = '$' + str(self.arr_temps.pop())
            # else:
            #     var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
            if self.function_directory.var_is_array(self.latest_var, self.curr_scope):
                var_dir = '$' + str(self.arr_temps.pop())
            else:
                var_dir = self.function_directory.get_var_address(
                    self.latest_var, self.curr_scope)
        else:
            # if 'd1' in self.function_table[self.program_name]['vars'][self.latest_var]:
            #     var_dir = '$' + str(self.arr_temps.pop())
            # else:
            #     var_dir = self.function_table[self.program_name]['vars'][self.latest_var]['dir']
            if self.function_directory.var_is_array(self.latest_var, self.program_name):
                var_dir = '$' + str(self.arr_temps.pop())
            else:
                var_dir = self.function_directory.get_var_address(
                    self.latest_var, self.program_name)

        q = Quadruple(lo['dir'], -1, '=', var_dir)
        self.quadruples.append(q)
        self.quad_counter += 1

    @_('id_or_attribute', 'id_or_attribute v0 LBRACKET expression v1 RBRACKET',
        'id_or_attribute v0 LBRACKET expression v2 COMMA v4 expression v3 RBRACKET')
    def variable(self, p):
        # print(f'variable line {sys._getframe().f_lineno}')
        # print('Variable p[0]: ', p[0])
        return p[0]

    @_('')
    def v0(self, p):
        # self.check_variable_exists(p[-1])
        if not self.function_directory.has_id(p[-1], self.curr_scope) and not self.class_directory.scope_has_id(p[-1], self.current_class):
            raise UndeclaredIdError(p[-1])
        # if self.current_class != None:
            # if not 'd1' in self.class_table[self.current_class]['vars'][p[-1]]:
        if self.current_class != None and self.class_directory.scope_has_id(p[-1], self.current_class):
            if not self.class_directory.var_is_array(p[-1], self.current_class):
                raise TypeError(f'{p[-1]} is not an array or vector')
        # elif p[-1] in self.function_table[self.curr_scope]['vars']:
        elif self.function_directory.scope_has_id(p[-1], self.curr_scope):
            # if not 'd1' in self.function_table[self.curr_scope]['vars'][p[-1]]:
            if not self.function_directory.var_is_array(p[-1], self.curr_scope):
                raise TypeError(f'{p[-1]} is not an array or vector')
        else:
            # if not 'd1' in self.function_table[self.program_name]['vars'][p[-1]]:
            if not self.function_directory.var_is_array(p[-1], self.program_name):
                raise TypeError(f'{p[-1]} is not an array or vector')
        self.latest_var = p[-1]
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @ _('')
    def v4(self, p):
        # self.check_variable_exists(self.latest_var)
        # raise UndeclaredIdError(p[-1])
        # if self.current_class != None:
        #     if not 'd2' in self.class_table[self.current_class]['vars'][self.latest_var]:
        #         raise TypeError(f'{self.latest_var} is not an array or vector')
        # elif self.latest_var in self.function_table[self.curr_scope]['vars']:
        #     if not 'd2' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
        #         raise TypeError(f'{self.latest_var} is not an array or vector')
        # else:
        #     if not 'd2' in self.function_table[self.program_name]['vars'][self.latest_var]:
        #         raise TypeError(f'{self.latest_var} is not an array or vector')
        if self.current_class != None and self.class_directory.scope_has_id(self.latest_var, self.current_class):
            if not self.class_directory.var_is_array(self.latest_var, self.current_class):
                raise TypeError(f'{self.latest_var} is not an array or vector')
        elif self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            if not self.function_directory.var_is_array(self.latest_var, self.curr_scope):
                raise TypeError(f'{self.latest_var} is not an array or vector')
        else:
            if not self.function_directory.var_is_array(self.latest_var, self.program_name):
                raise TypeError(f'{self.latest_var} is not an array or vector')
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @ _('')
    def v1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        # elif self.latest_var in self.function_table[self.curr_scope]['vars']:
        elif self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            # lms = self.function_table[self.curr_scope]['vars'][self.latest_var]['d1']
            lms = self.function_directory.get_var_d1(
                self.latest_var, self.curr_scope)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            # dir_b = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
            dir_b = self.function_directory.get_var_address(
                self.latest_var, self.curr_scope)
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, 0)
            # self.quadruples.append(Quadruple(cons_dir, t_addr, '+', t_dir))
            temp = self.function_directory.add_temp(
                self.curr_scope, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(cons_dir, t_addr, '+', temp['dir']))
            self.quad_counter += 1
            self.arr_temps.append(temp['dir'])
        else:
            # t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
            #     'dir']
            # if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
            #     raise TypeError('Type mismatch')
            # lms = self.function_table[self.program_name]['vars'][self.latest_var]['d1']
            # self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            # self.quad_counter += 1
            # dir_b = self.function_table[self.program_name]['vars'][self.latest_var]['dir']
            # self.constant_table['int'].append(dir_b)
            # cons_dir = self.constant_table['int'].index(dir_b) + 4500
            # num_temps = self.function_table[self.program_name]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.program_name]['num_temps'] = self.update_num_temps(
            #     num_temps, 0)
            # self.quadruples.append(Quadruple(cons_dir, t_addr, '+', t_dir))
            # self.quad_counter += 1
            # self.arr_temps.append(t_dir)
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            lms = self.function_directory.get_var_d1(
                self.latest_var, self.program_name)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_directory.get_var_address(
                self.latest_var, self.program_name)
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            temp = self.function_directory.add_temp(
                self.program_name, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(cons_dir, t_addr, '+', temp['dir']))
            self.quad_counter += 1
            self.arr_temps.append(temp['dir'])
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @ _('')
    def v2(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        # elif self.latest_var in self.function_table[self.curr_scope]['vars']:
        elif self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            # lms = self.function_table[self.curr_scope]['vars'][self.latest_var]['d1']
            lms = self.function_directory.get_var_d1(
                self.latest_var, self.curr_scope)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            # d2 = self.function_table[self.curr_scope]['vars'][self.latest_var]['d2']
            d2 = self.function_directory.get_var_d2(
                self.latest_var, self.curr_scope)
            if not d2 in self.constant_table['int']:
                self.constant_table['int'].append(d2)
            cons_dir = self.constant_table['int'].index(d2) + 4500
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, 0)
            # self.quadruples.append(Quadruple(cons_dir, t_addr, '+', t_dir))
            temp = self.function_directory.add_temp(
                self.curr_scope, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(cons_dir, t_addr, '*', temp['dir']))
            self.quad_counter += 1
            self.displacements.append(temp['dir'])
        else:
            # t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
            #     'dir']
            # if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
            #     raise TypeError('Type mismatch')
            # lms = self.function_table[self.program_name]['vars'][self.latest_var]['d1']
            # self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            # self.quad_counter += 1
            # d2 = self.function_table[self.program_name]['vars'][self.latest_var]['d2']
            # self.constant_table['int'].append(d2)
            # cons_dir = self.constant_table['int'].index(d2) + 4500
            # num_temps = self.function_table[self.program_name]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.program_name]['num_temps'] = self.update_num_temps(
            #     num_temps, 0)
            # self.quadruples.append(Quadruple(cons_dir, t_addr, '*', t_dir))
            # self.quad_counter += 1
            # self.displacements.append(t_dir)
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            lms = self.function_directory.get_var_d1(
                self.latest_var, self.program_name)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            d2 = self.function_directory.get_var_d2(
                self.latest_var, self.program_name)
            if not d2 in self.constant_table['int']:
                self.constant_table['int'].append(d2)
            cons_dir = self.constant_table['int'].index(d2) + 4500
            temp = self.function_directory.add_temp(
                self.program_name, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(cons_dir, t_addr, '*', temp['dir']))
            self.quad_counter += 1
            self.displacements.append(temp['dir'])
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @ _('')
    def v3(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if self.current_class != None:
            pass
        # elif self.latest_var in self.function_table[self.curr_scope]['vars']:
        elif self.function_directory.scope_has_id(self.latest_var, self.curr_scope):
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            # lms = self.function_table[self.curr_scope]['vars'][self.latest_var]['d2']
            lms = self.function_directory.get_var_d2(
                self.latest_var, self.curr_scope)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            # dir_b = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
            dir_b = self.function_directory.get_var_address(
                self.latest_var, self.curr_scope)
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, 0, 2)
            # self.quadruples.append(
            #     Quadruple(self.displacements.pop(), t_addr, '+', t_dir))
            # self.quadruples.append(Quadruple(cons_dir, t_dir, '+', t_dir + 1))
            temp = self.function_directory.add_temp(
                self.curr_scope, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(self.displacements.pop(), t_addr, '+', temp['dir']))
            self.quadruples.append(
                Quadruple(cons_dir, temp['dir'], '+', temp['dir'] + 1))
            self.quad_counter += 2
            self.arr_temps.append(temp['dir'] + 1)
        else:
            # t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
            #     'dir']
            # if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
            #     raise TypeError('Type mismatch')
            # lms = self.function_table[self.program_name]['vars'][self.latest_var]['d2']
            # self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            # self.quad_counter += 1
            # dir_b = self.function_table[self.program_name]['vars'][self.latest_var]['dir']
            # self.constant_table['int'].append(dir_b)
            # cons_dir = self.constant_table['int'].index(dir_b) + 4500
            # num_temps = self.function_table[self.program_name]['num_temps']
            # t_dir = int(num_temps.split('\u001f')[0]) + 3000
            # self.function_table[self.program_name]['num_temps'] = self.update_num_temps(
            #     num_temps, 0, 2)
            # self.quadruples.append(
            #     Quadruple(self.displacements.pop(), t_addr, '+', t_dir))
            # self.quadruples.append(Quadruple(cons_dir, t_dir, '+', t_dir + 1))
            # self.quad_counter += 2
            # self.arr_temps.append(t_dir + 1)
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if self.get_type_from_address(t_addr) != 'int' and self.get_type_from_address(t_addr) != 'float':
                raise TypeError('Type mismatch')
            lms = self.function_directory.get_var_d2(
                self.latest_var, self.program_name)
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.function_directory.get_var_address(
                self.latest_var, self.program_name)
            if not dir_b in self.constant_table['int']:
                self.constant_table['int'].append(dir_b)
            cons_dir = self.constant_table['int'].index(dir_b) + 4500
            temp = self.function_directory.add_temp(
                self.program_name, 0, self.temp_counter)
            self.quadruples.append(
                Quadruple(self.displacements.pop(), t_addr, '+', temp['dir']))
            self.quadruples.append(
                Quadruple(cons_dir, temp['dir'], '+', temp['dir'] + 1))
            self.quad_counter += 2
            self.arr_temps.append(temp['dir'] + 1)
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()
        print('v3 end')

    @ _('ID', 'ID DOT ID')
    def id_or_attribute(self, p):
        if len(p) > 1:
            # print('here')
            #     # Checar si estamos en una clase
            #     if self.current_class != None:
            #         raise SyntaxError('Cannot have objects in a class')
            #     # Checar que la clase existe checando que la p[0] existe y no es INT, BOOL, ETC
            #     if p[0] in self.function_table[self.curr_scope]['vars']:
            #         var_type = self.function_table[self.curr_scope]['vars'][p[0]]['type']
            #         # print(var_type)
            #     elif p[0] in self.function_table[self.program_name]['vars']:
            #         var_type = self.function_table[self.program_name]['vars'][p[0]]['type']
            #     else:
            #         raise SyntaxError(f'Undefined variable {p[0]}')

            #     if not var_type in self.class_table:
            #         raise SyntaxError(f'{var_type} is not a class')
            #     if not p[2] in self.class_table[var_type]['vars']:
            #         raise SyntaxError(
            #             f'Undefined attribute {p[2]} in class {var_type}')
            return p[0] + p[1] + p[2]
        return p[0]

    @ _('variable', 'CTE_I', 'CTE_F', 'CTE_STRING', 'cte_bool', 'call_to_function')
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
            # whole_p = p[0] + p[1] + p[2] if len(p) == 3 else p[0]
            # if not self.check_variable_exists(whole_p):
            if not self.check_variable_exists(p[-1]):
                raise UndeclaredIdError(p[-1])
            # if self.current_class != None:
            if self.current_class != None and self.class_directory.scope_has_id(p[0], self.current_class):
                # if whole_p in self.class_table[self.current_class]['vars']:
                #     cte_type = self.class_table[self.current_class]['vars'][whole_p]['type']
                #     var_dir = self.class_table[self.current_class]['vars'][whole_p]['dir']
                #     # var_dir = attr_dir + 1200 * len(self.types)
                # else:
                #     cte_type = self.function_table[self.curr_scope]['vars'][whole_p]['type']
                #     var_dir = self.function_table[self.curr_scope]['vars'][whole_p]['dir']
                #     # var_dir = attr_dir + 1200 * len(self.types)
                cte_type = self.class_directory.get_var_type(
                    p[0], self.current_class)
                cons_dir = self.class_directory.get_var_address(
                    p[0], self.current_class)
            else:
                print(p[0])
                # cte_type = self.get_var_type(whole_p)
                # if whole_p in self.function_table[self.curr_scope]['vars']:
                if self.function_directory.scope_has_id(p[0], self.curr_scope):
                    # var_dir = self.function_table[self.curr_scope]['vars'][whole_p]['dir']
                    cte_type = self.function_directory.get_var_type(
                        p[0], self.curr_scope)
                    cons_dir = self.function_directory.get_var_address(
                        p[0], self.curr_scope)
                else:
                    # var_dir = self.function_table[self.program_name]['vars'][whole_p]['dir']
                    cte_type = self.function_directory.get_var_type(
                        p[0], self.program_name)
                    cons_dir = self.function_directory.get_var_address(
                        p[0], self.program_name)

        return {'value': p[0], 'type': cte_type, 'dir': cons_dir}

    @ _('constant e2 operator e3 expression', 'constant e2', 'LPAREN e1 expression RPAREN e4')
    def expression(self, p):
        return p[0]

    @ _('')
    def e1(self, p):
        self.stack_of_stacks[-1].append('(')

    @ _('')
    def e2(self, p):
        self.stack_of_stacks[-2].append(p[-1])

    @ _('')
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

    @ _('')
    def e4(self, p):
        print('e4')
        while(self.stack_of_stacks[-1][-1] != '('):
            self.make_and_push_quad()
        self.stack_of_stacks[-1].pop()

    @ _('AND', 'OR')
    def logical_operator(self, p):
        return p[-1]

    @ _('LT', 'GT', 'SAME', 'GEQ', 'LEQ', 'NEQ')
    def relational_operator(self, p):
        return p[0]

    @ _('PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE')
    def arithmetic_operator(self, p):
        return p[0]

    @ _('logical_operator', 'relational_operator', 'arithmetic_operator')
    def operator(self, p):
        return p[0]

    @ _('PLUS var_cte', 'MINUS var_cte', 'var_cte')
    def constant(self, p):
        if len(p) > 1 and p[1] == '-':
            return -p.var_cte
        else:
            return p.var_cte

    @ _('READ LPAREN read_h')
    def read(self, p):
        return 'read'

    @ _('variable r1 COMMA read_h', 'variable r1 RPAREN SEMI')
    def read_h(self, p):
        return 'read_h'

    @ _('')
    def r1(self, p):
        # if p[-1] in self.function_table[self.curr_scope]['vars']:
        if self.function_directory.scope_has_id(p[-1], self.curr_scope):
            # if self.check_var_is_array(p[-1]):
            if self.function_directory.var_is_array(p[-1], self.curr_scope):
                var_addr = '$' + str(self.arr_temps.pop())
            else:
                # var_addr = self.function_table[self.curr_scope]['vars'][p[-1]]['dir']
                var_addr = self.function_directory.get_var_address(
                    p[-1], self.curr_scope)
        # elif p[-1] in self.function_table[self.program_name]['vars']:
        elif self.function_directory.scope_has_id(p[-1], self.program_name):
            # if self.check_var_is_array(p[-1]):
            if self.function_directory.var_is_array(p[-1], self.program_name):
                var_addr = '$' + str(self.arr_temps.pop())
            else:
                # var_addr = self.function_table[self.program_name]['vars'][p[-1]]['dir']
                var_addr = self.function_directory.get_var_address(
                    p[-1], self.program_name)
        else:
            raise UndeclaredIdError(p[-1])
        self.quadruples.append(Quadruple(-1, -1, 'read', var_addr))
        self.quad_counter += 1

    @ _('function_or_method vf0 ctf2 LPAREN func_params RPAREN fp2 fp3 ctf0 ctf3')
    def call_to_function(self, p):
        # func_dir = self.function_table[self.program_name]['vars'][p[0]]['dir']
        func_dir = self.function_directory.get_var_address(
            p[0], self.program_name)
        # func_type = self.function_table[p[0]]['return_type']
        func_type = self.function_directory.get_var_type(
            p[0], self.program_name)
        return {
            'value': 't' + str(self.temp_counter - 1),
            'type': func_type,
            'dir': func_dir
        }

    @ _('')
    def ctf2(self, p):
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    @ _('')
    def ctf3(self, p):
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    @ _('')
    def ctf0(self, p):
        # func_dir = self.function_table[self.program_name]['vars'][self.called_func]['real_dir']
        func_dir = self.function_directory.get_function_address(
            self.called_func, self.program_name)
        # func_type = self.function_table[self.program_name]['vars'][self.called_func]['type']
        func_type = self.function_directory.get_var_type(
            p[0], self.program_name)
        # idx = self.types.index(func_type)
        # num_temps = self.function_table[self.curr_scope]['num_temps']
        # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
        #     num_temps, idx)
        # t_dir = idx * 300 + 3000
        temp = self.function_directory.add_temp(
            self.curr_scope, func_type, self.temp_counter)
        self.quadruples.append(
            Quadruple(func_dir, -1, '=', temp['dir']))
        # self.function_table[self.program_name]['vars'][self.called_func]['dir'] = t_dir
        self.function_directory.update_var_address(
            self.called_func, self.program_name, temp['dir'])
        self.quad_counter += 1
        self.temp_counter += 1

    @ _('ID', 'ID DOT ID')
    def function_or_method(self, p):
        if not self.function_directory.has_id(p[-1], self.curr_scope) and not self.class_directory.scope_has_id(p[-1], self.current_class):
            raise UndeclaredIdError(p[-1])
        if(len(p) == 1):
            # if not p[0] in self.function_table:
            if not self.function_directory.has_id(p[0]):
                raise SyntaxError(f'function {p[0]} is not defined')
            else:
                return p[0]
        else:
            # var_type = self.get_var_type(p[0])
            # return var_type + p[1] + p[2]
            if self.function_directory.scope_has_id(p[0], self.curr_scope):
                var_type = self.function_directory.get_var_type(
                    p[0], self.curr_scope)
            else:
                var_type = self.function_directory.get_var_type(
                    p[0], self.program_name)
            return var_type + p[1] + p[2]

    # @ _('')
    # def ctf1_exists_in_func_table(self, p):
    #     if not p[-1] in self.function_table:
    #         raise SyntaxError(f'Function {p[-1]} is not defined')
    #     else:
    #         pass

    @ _('COMMA expression fp1 param_list', 'empty')
    def param_list(self, p):
        return 'param_list'

    @ _('PRINT LPAREN res_write RPAREN SEMI')
    def print(self, p):
        return 'print'

    @ _('expression pr1 comma_thing')
    def res_write(self, p):
        return 'res_write'

    @ _('COMMA res_write', 'empty')
    def comma_thing(self, p):
        return 'comma_thing'

    @ _('')
    def pr1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
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
                var_dir = '$' + str(self.arr_temps.pop())
            else:
                var_dir = var['dir']
            self.quadruples.append(
                Quadruple(-1, -1, 'print', var_dir))
            self.quad_counter += 1

    @ _('TRUE', 'FALSE')
    def cte_bool(self, p):
        return p[0]

    @ _('IF LPAREN expression dec1 RPAREN THEN LCURL statements RCURL else_stm')
    def decision_statement(self, p):
        return 'decision_statement'

    @ _('')
    def dec1(self, p):
        while len(self.stack_of_stacks[-1]):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
            if self.check_var_is_array(lo['value']):
                lo_dir = '$' + str(self.arr_temps.pop())
            else:
                lo_dir = lo['dir']
            if self.check_var_is_array(ro['value']):
                ro_dir = '$' + str(self.arr_temps.pop())
            else:
                ro_dir = ro['dir']
            self.quadruples.append(
                Quadruple(lo_dir, ro_dir, op, temp['dir']))
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

    @ _('dec2 ELSE LCURL statements RCURL dec3', 'empty dec4')
    def else_stm(self, p):
        return 'else_stm'

    @ _('')
    def dec2(self, p):
        falso = self.jumps.pop()
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1
        self.quadruples[falso - 1].res = self.quad_counter

    @ _('')
    def dec3(self, p):
        jump = self.jumps.pop()
        self.quadruples[jump - 1].res = self.quad_counter

    @ _('')
    def dec4(self, p):
        jump = self.jumps.pop()
        self.quadruples[jump - 1].res = self.quad_counter

    @ _('conditional', 'non_conditional')
    def repetition_statement(self, p):
        return 'repetition_statement'

    @ _('WHILE LPAREN con0 expression con1 RPAREN DO LCURL statements RCURL con2')
    def conditional(self, p):
        return 'conditional'

    @ _('')
    def con0(self, p):
        self.jumps.append(self.quad_counter)

    @ _('')
    def con1(self, p):
        while len(self.stack_of_stacks[-1]):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            # made_quad = True
        if self.last_type != 'bool':
            raise SyntaxError(
                'Expression to evaluate in if statement is not boolean')
        else:
            last_quad = self.quadruples[-1].res
            self.quadruples.append(Quadruple(-1, last_quad, 'goto_f', -1))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1

    @ _('')
    def con2(self, p):
        falso = self.jumps.pop()
        ret = self.jumps.pop()
        self.quadruples.append(Quadruple(-1, -1, 'goto', ret))
        self.quadruples[falso - 1].res = self.quad_counter + 1
        self.quad_counter += 1

    @ _('FOR variable ass1 EQUALS expression ass2 nc0 UNTIL expression nc1 DO nc2 LCURL statements RCURL nc3')
    def non_conditional(self, p):
        return 'non_conditional'

    @ _('')
    def nc0(self, p):
        self.for_var_dir.append(self.quadruples[-1].res)

    @ _('')
    def nc1(self, p):
        while len(self.stack_of_stacks[-1]):
            self.make_and_push_quad()
        if len(self.stack_of_stacks[-2]) == 0 and (self.last_type != 'int' and self.last_type != 'float'):
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif p[-1]['type'] != 'int' and p[-1]['type'] != 'float':
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif len(self.stack_of_stacks[-2]) == 0:
            last_quad = self.quadruples[-1].res
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = 3 * 300 + \
            #     int(num_temps.split('\u001f')[3]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, 3)
            temp = self.function_directory.add_temp(
                self.curr_scope, 3, self.temp_counter)
            self.temp_counter += 1
            if self.check_var_is_array(last_quad['value']):
                var_dir = '$' + str(self.arr_temps.pop())
            else:
                var_dir = last_quad['dir']
            self.quadruples.append(
                Quadruple(self.for_var_dir[-1], var_dir, '<=', temp['dir']))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
        else:
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = 3 * 300 + \
            #     int(num_temps.split('\u001f')[3]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, 3)
            temp = self.function_directory.add_temp(
                self.curr_scope, 3, self.temp_counter)
            self.temp_counter += 1
            if self.check_var_is_array(p[-1]['value']):
                var_dir = '$' + str(self.arr_temps.pop())
            else:
                var_dir = p[-1]['dir']
            self.quadruples.append(
                Quadruple(self.for_var_dir[-1], var_dir, '<=', temp['dir']))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1

    @ _('')
    def nc2(self, p):
        last_quad = self.quadruples[-1].res
        self.quadruples.append(Quadruple(-1, last_quad, 'goto_f', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1

    @ _('')
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
        self.for_var_dir.pop()

    @ _('RETURN LPAREN expression fr0 RPAREN SEMI fr1')
    def function_returns(self, p):
        return 'function_returns'

    @ _('')
    def fr0(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            self.make_and_push_quad()
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                # Quadruple(last_quad.res, -1, 'return', self.function_table[self.program_name]['vars'][self.curr_scope]['real_dir']))
                Quadruple(last_quad.res, -1, 'return', self.function_directory.get_function_address(self.curr_scope, self.program_name)))
            self.quad_counter += 1
            self.stack_of_stacks[-2].pop()
        else:
            self.quadruples.append(
                # Quadruple(self.stack_of_stacks[-2].pop()['dir'], -1, 'return', self.function_table[self.program_name]['vars'][self.curr_scope]['real_dir']))
                Quadruple(self.stack_of_stacks[-2].pop()['dir'], -1, 'return', self.function_directory.get_function_address(self.curr_scope, self.program_name)))
            self.quad_counter += 1

    @ _('')
    def fr1(self, p):
        self.has_returned = True

    @ _('function_or_method vf0 LPAREN func_params RPAREN fp2 fp3 SEMI')
    def call_to_void_function(self, p):
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
        self.called_func = p[-1]
        self.quadruples.append(Quadruple(p[-1], -1, 'era', -1))
        self.quad_counter += 1

    @ _('expression fp1 param_list', 'empty')
    def func_params(self, p):
        return 'func_params'

    @ _('')
    def fp1(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            ro = self.stack_of_stacks[-2].pop()
            lo = self.stack_of_stacks[-2].pop()
            op = self.stack_of_stacks[-1].pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            # idx = self.types.index(self.last_type)
            # num_temps = self.function_table[self.curr_scope]['num_temps']
            # t_dir = idx * 300 + int(num_temps.split('\u001f')[idx]) + 3000
            # self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
            #     num_temps, idx)
            temp = self.function_directory.add_temp(
                self.curr_scope, self.last_type, self.temp_counter)
            self.stack_of_stacks[-2].append(temp)
            self.quadruples.append(
                Quadruple(lo['dir'], ro['dir'], op, temp['dir']))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            # if self.param_counter == len(self.function_table[self.called_func]['params']):
            if self.param_counter == len(self.function_directory.get_function_params(self.called_func)):
                raise SyntaxError('Too many params')
            param_type = (last_quad.res % 1500) // 300
            # if param_type != int(self.function_table[self.called_func]['params'][self.param_counter]):
            if param_type != int(self.function_directory.get_function_params(self.called_func)[self.param_counter]):
                raise TypeError('Type mismatch')
            self.quadruples.append(
                Quadruple(last_quad.res, -1, 'param', self.param_counter))
            self.quad_counter += 1
            self.param_counter += 1
        else:
            val = self.stack_of_stacks[-2].pop()
            # if self.param_counter == len(self.function_table[self.called_func]['params']):
            if self.param_counter == len(self.function_directory.get_function_params(self.called_func)):
                raise SyntaxError('Too many params')
            param_type = (val['dir'] % 1500) // 300
            # if param_type != int(self.function_table[self.called_func]['params'][self.param_counter]):
            print('fp1', param_type, self.function_directory.get_function_params(
                self.called_func), self.param_counter)
            if param_type != int(self.function_directory.get_function_params(self.called_func)[self.param_counter]):
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
        # del self.function_table[self.program_name]['vars']
        # del self.function_table['main']['vars']
        self.function_directory.delete_var_table(self.program_name)
        self.function_directory.delete_var_table('main')
        for class_name in self.class_table:
            # del self.class_table[class_name]['vars']
            self.class_directory.delete_var_table(class_name)

    @ _('')
    def m1_add_to_func_table(self, p):
        self.curr_scope = 'main'
        # self.add_to_func_table('main', None)
        self.function_directory.add_scope('main')

    @ _('')
    def empty(self, p):
        pass

    def error(self, p):
        print(p.value in DomasLexer.reserved_words)
        if p.value in DomasLexer.reserved_words:
            raise ReservedWordError(p.value)
        else:
            print("Syntax error in input!", p.lineno, p)
