from sly import Parser
from sly.yacc import _decorator as _
from .domas_lexer import DomasLexer
from .domas_quadruples import Quadruple
from .domas_errors import *
from . import domas_semantic_cube as sm
import json  # to debug only
import os
import copy

os.system('color')


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
    last_func_added = None
    has_returned = False
    found_errors = False
    types = ['int', 'float', 'string', 'bool', 'void']
    operators = ['+', '-', '*', '/', '<',
                 '>', '<=', '>=', '==', '<>', '&', '|']

    # Add a function to the function table
    def add_to_func_table(self, id, return_type):
        self.function_table[id] = {
            'return_type': return_type,
            'vars': {},
            'num_types': '0\u001f' * len(self.types),
            'params': '',
            'num_temps': '0\u001f' * len(self.types)
        }

    # Checks if a variable exists
    def check_variable_exists(self, var):
        if self.current_class != None:
            return var in self.function_table[self.curr_scope]['vars'] or var in self.class_table[self.current_class]['vars']
        return var in self.function_table[self.curr_scope]['vars'] or var in self.function_table[self.program_name]['vars']

    # Returns the type of a variable if it exists
    def get_var_type(self, var, tok):
        if not self.check_variable_exists(var):
            self.found_errors = True
            print('ERROR: No variable\033[1m',
                  var, '\033[0mwas found.')
            print('       Missing reference found on line',
                  tok.lineno)
            return None
        if self.current_class != None:
            if var in self.function_table[self.curr_scope]['vars']:
                return self.function_table[self.curr_scope]['vars'][var]['type']
            return self.class_table[self.current_class]['vars'][var]['type']
        if var in self.function_table[self.curr_scope]['vars']:
            return self.function_table[self.curr_scope]['vars'][var]['type']
        return self.function_table[self.program_name]['vars'][var]['type']

    # Updates the amount of temporals used in fucntions.
    def update_num_temps(self, func_num_temps, type_idx, quantity=1):
        lst = func_num_temps.split('\u001f')
        lst[type_idx] = str(int(lst[type_idx]) + quantity)
        return '\u001f'.join(lst)

    # Cheks if a var is an array by finding its first dimension
    def check_var_is_array(self, var):
        if not var:
            return
        if var['dir'] >= 4500 and var['dir'] < 6000:
            return False
        if not self.check_variable_exists(var['value']):
            return False
        if self.current_class != None:
            if var['value'] in self.function_table[self.curr_scope]['vars']:
                return 'd1' in self.function_table[self.curr_scope]['vars'][var['value']]
            else:
                return 'd1' in self.class_table[self.current_class]['vars'][var['value']]
        elif var['value'] in self.function_table[self.curr_scope]['vars']:
            return 'd1' in self.function_table[self.curr_scope]['vars'][var['value']]
        else:
            return 'd1' in self.function_table[self.program_name]['vars'][var['value']]

    # Makes quadruples for arithemtic operators and pushes them into the quadruple stack
    def make_and_push_quad(self):
        ro = self.stack_of_stacks[-2].pop()
        lo = self.stack_of_stacks[-2].pop()
        op = self.stack_of_stacks[-1].pop()
        if not ro or not lo:
            raise SystemError("Reached unsolvable state")
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
        if self.check_var_is_array(lo):
            lo_dir = '$' + str(self.last_arr_t.pop())
        else:
            lo_dir = lo['dir']
        if self.check_var_is_array(ro):
            ro_dir = '$' + str(self.last_arr_t.pop())
        else:
            ro_dir = ro['dir']
        self.quadruples.append(
            Quadruple(lo_dir, ro_dir, op, t_dir))
        self.temp_counter += 1
        self.quad_counter += 1

    @_('PROGRAM ID pro1 SEMI pro0 declarations')
    def programa(self, p):
        if self.found_errors:
            raise CompilationError()
        # func_dir_out = open('debug/funcdir.out', 'w')
        # class_dir_out = open('debug/classdir.out', 'w')
        # func_dir_out.write(json.dumps(
        #     self.function_table, indent=2))
        # class_dir_out.write(json.dumps(
        #     self.class_table, indent=2))
        return (self.program_name, self.function_table, self.class_table, self.constant_table, self.quadruples)

    # Creates goto main quadruple and appends it to the quadruple list
    @_('')
    def pro0(self, p):
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.quad_counter += 1

    # creates function table
    @_('')
    def pro1(self, p):
        self.program_name = p[-1]
        self.curr_scope = p[-1]
        self.function_table[p[-1]] = {
            'return_type': None,
            'vars': {}, 'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'
        }

    @ _('class_declaration out_class var_declaration function_definition main')
    def declarations(self, p):
        return 'declarations'

    @ _('''CLASS ID cd1 inherits LCURL ATTRIBUTES attribute_declaration METHODS
          method_definition RCURL class_declaration''', 'empty')
    def class_declaration(self, p):
        return 'class_declaration'

    # Adds class to class table
    @ _('')
    def cd1(self, p):
        if p[-1] in self.class_table:
            self.found_errors = True
            print(
                'ERROR: A class with the name\033[1m', p[-1], '\033[0mhas already been defined')
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
        else:
            self.class_table[p[-1]] = {
                'vars': {},
                'num_types': '0\u001f0\u001f0\u001f0\u001f0\u001f'
            }
            self.current_class = p[-1]

    @ _('INHERITS ID cd3', 'empty')
    def inherits(self, p):
        return 'inherits'

    # Copies the information from parent class to its child.
    @ _('')
    def cd3(self, p):
        if not p[-1] in self.class_table:
            self.found_errors = True
            print('ERROR: Id\033[1m', p[-1],
                  '\033[0mis not defined as a class')
            print('       Missing reference found on line',
                  self.symstack[-1].lineno)
        else:
            self.class_table[self.current_class] = copy.deepcopy(
                self.class_table[p[-1]])

    @ _('VAR ID ad1 attr_vector', 'VAR ID ad1 attr_simple_var', 'empty')
    def attribute_declaration(self, p):
        return 'attribute_declaration'

    # Appends declared variable to the stack of variables if it doesn't exist
    @ _('')
    def ad1(self, p):
        if p[-1] in self.class_table[self.current_class]['vars']:
            self.found_errors = True
            print('ERROR: An attribute\033[1m',
                  p[-1], '\033[0mhas already been defined')
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
        else:
            self.stack_vars.append(p[-1])

    @ _('''LBRACKET CTE_I ad2 attr_multidim RBRACKET COLON simple_type ad4 SEMI
           attribute_declaration''')
    def attr_vector(self, p):
        return 'vector'

    # Adds the first dimension of an array to the information of the variable
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

    # Adds the second dimension of an array to the information of the variable.
    @ _('')
    def ad3(self, p):
        self.class_table[self.current_class]['vars'][self.latest_var]['d2'] = p[-1]

    # Adds the type and direction to the information of the variable declared and updated the amount of types used in the class.
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

    # Pops the stack of variables and giving each their corresponding type.
    @ _('')
    def ad5(self, p):
        while len(self.stack_vars) > 0:
            curr_var = self.stack_vars.pop()
            if curr_var in self.class_table[self.current_class]['vars']:
                self.found_errors = True
                print('ERROR: An attribute\033[1m',
                      curr_var, '\033[0mhas already been defined in class', self.current_class)
                print('       Redefinition found on line',
                      self.symstack[-2].lineno)
            idx = self.types.index(p[-1])
            num_types = self.class_table[self.current_class]['num_types']
            self.class_table[self.current_class]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.class_table[self.current_class]['vars'][curr_var] = {
                'type': p[-1], 'dir': 6000 + idx * 300 + int(num_types.split('\u001f')[idx])}

    @ _('''def_type fd1 FUNCTION ID md3 LPAREN m_parameters
           RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6
           method_definition''', 'empty')
    def method_definition(self, p):
        return 'method_definition'

    # Adds the id with the name of the class prefixed to the function table.
    @ _('')
    def md3(self, p):
        if p[-1] in self.class_table[self.current_class]['vars']:
            self.found_errors = True
            print('ERROR: An attribute or method\033[1m',
                  p[-1], '\033[0mhas already been defined in class', self.current_class)
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
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

    # Adds the id and type of the parameter to the table of variables of the current method.
    @ _('')
    def m2(self, p):
        if self.latest_var in self.function_table[self.curr_scope]['vars']:
            self.found_errors = True
            print('ERROR: A parameter\033[1m',
                  self.latest_var, '\033[0mhas already been declared for method', self.last_func_added.split('.')[1], 'in class', self.current_class)
            print('       Redefinition found on line',
                  self.symstack[-2].lineno)
        else:
            idx = self.types.index(p[-1])
            self.function_table[self.curr_scope]['params'] += str(
                idx)
            num_types = self.function_table[self.curr_scope]['num_types']
            self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                num_types, idx)
            self.function_table[self.curr_scope]['vars'][self.latest_var] = {
                'type': p[-1],
                'dir': 1500 + idx * 300 + int(num_types.split('\u001f')[idx])
            }

    @ _('COMMA m_parameters', 'empty')
    def m_param_choose(self, p):
        return 'm_param_choose'

    @ _('')
    def out_class(self, p):
        self.current_class = None
        self.curr_scope = self.program_name

    @ _('VAR ID gvd1 vector', 'VAR ID gvd1 simple_var', 'empty')
    def var_declaration(self, p):
        return p[0]

    # Appends the current var to the stack of variables of it doesn't exist.
    @ _('')
    def gvd1(self, p):
        if p[-1] in self.function_table:
            self.found_errors = True
            print('ERROR: A function with ID\033[1m',
                  p[-1], '\033[0mhas already been declared. Variables may not share name with functions')
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
        # elif self.current_class != None and p[-1] in self.class_table[self.current_class]:
        #     raise RedefinitionError(p[-1])
        else:
            self.stack_vars.append(p[-1])

    @ _('LBRACKET CTE_I gvd2 multidim RBRACKET COLON simple_type gvd4 SEMI var_declaration')
    def vector(self, p):
        return 'vector'

    # Adds the variable and its first dimension to the variable table of the current scope.
    @ _('')
    def gvd2(self, p):
        self.latest_var = self.stack_vars.pop()
        if self.function_table[self.curr_scope]['vars']:
            self.function_table[self.curr_scope]['vars'][self.latest_var] = {
                'd1': p[-1]
            }
        else:
            self.function_table[self.curr_scope]['vars'] = {
                self.latest_var: {'d1': p[-1]}
            }

    @ _('COMMA CTE_I gvd3', 'empty')
    def multidim(self, p):
        return 'multidim'

    @ _('var_list COLON composite_type gvd6 SEMI var_declaration', 'var_list COLON simple_type gvd5 SEMI var_declaration')
    def simple_var(self, p):
        return 'simple_var'

    @ _('COMMA ID gvd1 var_list', 'empty')
    def var_list(self, p):
        return 'var_list'

    # Adds the second dimension to the latest variable in the current scope
    @ _('')
    def gvd3(self, p):
        self.function_table[self.curr_scope]['vars'][self.latest_var]['d2'] = p[-1]

    # Adds the type and address to the information of the variable declared and updated the amount of types used in the class.
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

    # Pops the var stack, adding their ids and types to the variable directory of the current scope
    @ _('')
    def gvd5(self, p):
        while len(self.stack_vars) > 0:
            curr_var = self.stack_vars.pop()
            if curr_var in self.function_table[self.curr_scope]['vars']:
                self.found_errors = True
                print('ERROR: A variable\033[1m',
                      curr_var, '\033[0mhas already been declared.')
                print('       Redefinition found on line',
                      self.symstack[-5].lineno)
            idx = self.types.index(p[-1])
            num_types = self.function_table[self.curr_scope]['num_types']
            offset = 1500 if self.curr_scope != self.program_name else 0
            self.function_table[self.curr_scope]['vars'][curr_var] = {
                'type': p[-1], 'dir': idx * 300 + int(num_types.split('\u001f')[idx]) + offset}
            self.function_table[self.curr_scope]['num_types'] = self.update_num_temps(
                num_types, idx)

    # Same as gvd5 but it also adds the variables of the class in question to the table of the current scope
    @ _('')
    def gvd6(self, p):
        while len(self.stack_vars) > 0:
            var_id = self.stack_vars.pop()
            if var_id in self.function_table[self.curr_scope]['vars']:
                self.found_errors = True
                print('ERROR: A variable\033[1m',
                      var_id, '\033[0mhas already been declared.')
                print('       Redefinition found on line',
                      self.symstack[-5].lineno)
            offset = 1500 if self.curr_scope != self.program_name else 0
            num_types = self.function_table[self.curr_scope]['num_types']
            base_addrs = [int(n) for n in num_types.split('\u001f')[:-1]]
            if not p[-1] in self.class_table:
                for i in range(1, len(self.symstack)):
                    if hasattr(self.symstack[i * -1], 'lineno'):
                        lineno = self.symstack[i * -1].lineno
                        break
                print('ERROR: No class\033[1m',
                      p[-1], '\033[0mwas found.')
                print('       Missing reference found on line',
                      lineno)
                return
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

    @ _('def_type fd1 FUNCTION ID fd3 LPAREN parameters RPAREN LCURL fd4 var_declaration statements RCURL fd5 fd6 function_definition', 'empty')
    def function_definition(self, p):
        return 'function_definition'

    # saves thee current function type in a variable
    @ _('')
    def fd1(self, p):
        self.curr_func_type = p[-1]

    # Adds the id of the function to the function table
    @ _('')
    def fd3(self, p):
        if p[-1] in self.function_table:
            self.found_errors = True
            print('ERROR: A function\033[1m',
                  p[-1], '\033[0mhas already been defined.')
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
        elif p[-1] in self.function_table[self.program_name]['vars']:
            self.found_errors = True
            print('ERROR: A global variable\033[1m',
                  p[-1], '\033[0mhas been declared. Functions may not share names with global variables')
            print('       Redefinition found on line',
                  self.symstack[-1].lineno)
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

    # Adds the start of the quadruples related to the current function to the ts information in the function table
    @ _('')
    def fd4(self, p):
        if not self.last_func_added:
            return
        self.function_table[self.last_func_added]['start'] = self.quad_counter

    # Deletes the variable table of the current scope
    @ _('')
    def fd5(self, p):
        if not self.last_func_added:
            return
        del self.function_table[self.last_func_added]['vars']

    # Creates and appends the end_func quadruple to the quadruple stack
    @ _('')
    def fd6(self, p):
        if self.curr_func_type != 'void' and self.has_returned == False:
            self.found_errors = True
            print('ERROR: Function\033[1m',
                  self.curr_scope, '\033[0mis missing a return statement')
            print('       Non-void functions must have a return statement.')
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

    # Saves the ID of the parameter ina  variable
    @ _('')
    def p1(self, p):
        self.latest_var = p[-1]

    # Adds the type of the parameter to its information in the variable table of the current scope
    @ _('')
    def p2(self, p):
        if self.latest_var in self.function_table[self.curr_scope]['vars']:
            self.found_errors = True
            print('ERROR: A parameter\033[1m',
                  self.latest_var, '\033[0mhas already been declared for function', self.last_func_added)
            print('       Redefinition found on line',
                  self.symstack[-2].lineno)
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

    # Adds the quadruple counter to the break stack
    @_('')
    def br0(self, p):
        if len(self.jumps) == 0:
            self.found_errors = True
            print('ERROR: break statement on line',
                  self.symstack[-1].lineno, 'used outside a loop')
        self.quadruples.append(Quadruple(-1, -1, 'goto', None))
        self.break_stack.append(self.quad_counter)
        self.quad_counter += 1

    @_('variable ass1 EQUALS expression ass2 SEMI')
    def assignment(self, p):
        return 'assignment'

    # Save the id in a variable
    @_('')
    def ass1(self, p):
        self.latest_var = p[-1]

    # Generate the quadruple containing an '=' as its operator. Get the addresses of the left and res
    @_('')
    def ass2(self, p):
        made_quad = False
        while(len(self.stack_of_stacks[-1])):
            self.make_and_push_quad()
            made_quad = True
        lo = self.stack_of_stacks[-2].pop()
        if not lo:
            return
        v_type = self.get_var_type(self.latest_var, self.symstack[-2])
        if not v_type:
            return
        self.last_type = sm.checkOperation(v_type, lo['type'], '=')
        if not made_quad and self.check_var_is_array(lo):
            lo_dir = '$' + str(self.last_arr_t.pop())
        else:
            lo_dir = lo['dir']
        if self.current_class != None:
            if self.latest_var in self.class_table[self.current_class]['vars']:
                if 'd1' in self.class_table[self.current_class]['vars'][self.latest_var]:
                    if not self.last_arr_t:
                        return
                    var_dir = '$' + str(self.last_arr_t.pop())
                else:
                    var_dir = self.class_table[self.current_class]['vars'][self.latest_var]['dir']
            else:
                if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
                    if not self.last_arr_t:
                        return
                    var_dir = '$' + str(self.last_arr_t.pop())
                else:
                    var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
        elif self.latest_var in self.function_table[self.curr_scope]['vars']:
            if 'd1' in self.function_table[self.curr_scope]['vars'][self.latest_var]:
                if not self.last_arr_t:
                    return
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = self.function_table[self.curr_scope]['vars'][self.latest_var]['dir']
        else:
            if 'd1' in self.function_table[self.program_name]['vars'][self.latest_var]:
                if not self.last_arr_t:
                    return
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

    # Checks that the variable exists and is an array
    @_('')
    def v0(self, p):
        self.check_variable_exists(p[-1])
        if self.current_class != None:
            if not 'd1' in self.class_table[self.current_class]['vars'][p[-1]]:
                self.found_errors = True
                print('ERROR: Variable\033[1m',
                      p[-1], '\033[0mis not an array or matrix.')
                self.stack_of_stacks.append([])
                self.stack_of_stacks.append([])
                return
        elif p[-1] in self.function_table[self.curr_scope]['vars']:
            if not 'd1' in self.function_table[self.curr_scope]['vars'][p[-1]]:
                self.found_errors = True
                print('ERROR: Variable\033[1m',
                      p[-1], '\033[0mis not an array or matrix.')
                self.stack_of_stacks.append([])
                self.stack_of_stacks.append([])
                return
        elif not 'd1' in self.function_table[self.program_name]['vars'][p[-1]]:
            self.found_errors = True
            print('ERROR: Variable\033[1m',
                  p[-1], '\033[0mis not an array or matrix.')
            self.stack_of_stacks.append([])
            self.stack_of_stacks.append([])
            return
        self.last_arr_id = p[-1]
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    # Checks that the variable is a matrix
    @_('')
    def v4(self, p):
        self.check_variable_exists(self.last_arr_id)
        if self.current_class != None:
            if not 'd2' in self.class_table[self.current_class]['vars'][self.last_arr_id]:
                self.found_errors = True
                print('ERROR: Variable\033[1m',
                      self.last_arr_id, '\033[0mis not a matrix.')
        elif self.last_arr_id in self.function_table[self.curr_scope]['vars']:
            if not 'd2' in self.function_table[self.curr_scope]['vars'][self.last_arr_id]:
                self.found_errors = True
                print('ERROR: Variable\033[1m',
                      self.last_arr_id, '\033[0mis not a matrix.')
        else:
            if not 'd2' in self.function_table[self.program_name]['vars'][self.last_arr_id]:
                self.found_errors = True
                print('ERROR: Variable\033[1m',
                      self.last_arr_id, '\033[0mis not a matrix.')
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    # Calculates the address of the array index
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
        if self.current_class != None and self.last_arr_id in self.class_table[self.current_class]['vars']:
            t_addr = self.quadruples[-1].res if made_quad else self.stack_of_stacks[-2].pop()[
                'dir']
            if (t_addr % 1500) // 300 != 0 and (t_addr % 1500) // 300 != 1:
                raise TypeError('Type mismatch')
            lms = self.class_table[self.current_class]['vars'][self.last_arr_id]['d1']
            self.quadruples.append(Quadruple(0, lms, 'verify', t_addr))
            self.quad_counter += 1
            dir_b = self.class_table[self.current_class]['vars'][self.last_arr_id]['dir']
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

    # Calculate the address of the matrix index
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

    # Calculate s1*d2
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

    # Returns value, type and address of the constant
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
            if not self.check_variable_exists(p[0]):
                for i in range(1, len(self.symstack)):
                    if hasattr(self.symstack[i * -1], 'lineno'):
                        lineno = self.symstack[i * -1].lineno
                        break
                self.found_errors = True
                print('ERROR: No variable\033[1m',
                      p[0], '\033[0mwas found.')
                print('       Missing reference found on line',
                      lineno)
                return
            if self.current_class != None and p[0] in self.class_table[self.current_class]['vars']:
                cte_type = self.class_table[self.current_class]['vars'][p[0]]['type']
                cons_dir = self.class_table[self.current_class]['vars'][p[0]]['dir']
            else:
                cte_type = self.get_var_type(p[0], self.symstack[-2])
                if p[0] in self.function_table[self.curr_scope]['vars']:
                    cons_dir = self.function_table[self.curr_scope]['vars'][p[0]]['dir']
                else:
                    cons_dir = self.function_table[self.program_name]['vars'][p[0]]['dir']

        return {'value': p[0], 'type': cte_type, 'dir': cons_dir}

    @_('constant e2 operator e3 expression', 'constant e2', 'LPAREN e1 expression RPAREN e4', 'LPAREN e1 expression RPAREN e4 operator e3 expression')
    def expression(self, p):
        if hasattr(p, 'LPAREN'):
            return p[2]
        return p[0]

    # Append the open parenthesis to the stack of operators in the stacks_of_stacks
    @_('')
    def e1(self, p):
        self.stack_of_stacks[-1].append('(')

    # Appende the operand to the stack of operands in the stacks_of _stacks
    @_('')
    def e2(self, p):
        self.stack_of_stacks[-2].append(p[-1])

    # Makes the quadruple of operation
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

    # Pops the operator stack and makes quads until an open parenthesis is found
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

    @_('variable r1 COMMA read_h', 'variable r1 RPAREN SEMI')
    def read_h(self, p):
        return 'read_h'

    # Makes the read quadruple wiht res being the address prefixed with a dollar sign ($)
    @_('')
    def r1(self, p):
        if self.current_class != None and p[-1] in self.class_table[self.current_class]['vars']:
            if 'd1' in self.class_table[self.current_class]['vars'][p[-1]]:
                var_addr = '$' + str(self.last_arr_t.pop())
            else:
                var_addr = self.class_table[self.current_class]['vars'][p[-1]]['dir']
        elif p[-1] in self.function_table[self.curr_scope]['vars']:
            if 'd1' in self.function_table[self.curr_scope]['vars'][p[-1]]:
                var_addr = '$' + str(self.last_arr_t.pop())
            else:
                var_addr = self.function_table[self.curr_scope]['vars'][p[-1]]['dir']
        elif p[-1] in self.function_table[self.program_name]['vars']:
            if 'd1' in self.function_table[self.program_name]['vars'][p[-1]]:
                var_addr = '$' + str(self.last_arr_t.pop())
            else:
                var_addr = self.function_table[self.program_name]['vars'][p[-1]]['dir']
        else:
            raise UndeclaredIdError(p[-1])
        self.quadruples.append(Quadruple(-1, -1, 'read', var_addr))
        self.quad_counter += 1

    @_('function_or_method vf0 ctf2 LPAREN func_params RPAREN fp2 fp3 ctf0 ctf3')
    def call_to_function(self, p):
        if not self.check_variable_exists(self.called_func):
            # self.found_errors = True
            # print('ERROR: No function\033[1m',
            #       self.called_func, '\033[0mwas found.')
            # print('       Missing reference found on line',
            #       self.symstack[-5].lineno)
            return
        func_dir = self.function_table[self.program_name]['vars'][self.called_func]['dir']
        func_type = self.function_table[self.called_func]['return_type']
        return {'value': 't' + str(self.temp_counter - 1), 'type': func_type, 'dir': func_dir}

    # Append two empty stacks to the stack_of_stacks
    @_('')
    def ctf2(self, p):
        self.stack_of_stacks.append([])
        self.stack_of_stacks.append([])

    # Pops the staks from the stacks_of_stacks
    @_('')
    def ctf3(self, p):
        self.stack_of_stacks.pop()
        self.stack_of_stacks.pop()

    # Call the return value in the address of the corresponding variable
    @_('')
    def ctf0(self, p):
        if not self.check_variable_exists(self.called_func):
            self.found_errors = True
            print('ERROR: No function\033[1m',
                  self.called_func, '\033[0mwas found.')
            print('       Missing reference found on line',
                  self.symstack[-3].lineno)
            return
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

    #
    @_('ID ctf1', 'ID DOT ID')
    def function_or_method(self, p):
        if(len(p) == 2):
            return (p[0], None)
        else:
            var_type = self.get_var_type(p[0], self.symstack[-1])
            quads = []
            for attr in self.class_table[var_type]['vars']:
                var_dir = self.function_table[self.curr_scope]['vars'][p[0]+'.'+attr]['dir']
                attr_dir = self.class_table[var_type]['vars'][attr]['dir']
                quads.append(Quadruple(var_dir, -2, '=', attr_dir))
                # self.quad_counter += 1
            return (var_type + p[1] + p[2], quads)

    # Check if name of the function being called exists in the function table
    @_('')
    def ctf1(self, p):
        if self.current_class != None:
            if not self.current_class + '.' + p[-1] in self.function_table:
                self.found_errors = True
                print('ERROR: No function\033[1m',
                      p[-1], '\033[0mwas found.')
                print('       Missing reference found on line',
                      self.symstack[-1].lineno)
        elif not p[-1] in self.function_table:
            self.found_errors = True
            print('ERROR: No function\033[1m',
                  p[-1], '\033[0mwas found.')
            print('       Missing reference found on line',
                  self.symstack[-1].lineno)

    @_('COMMA expression fp1 param_list', 'empty')
    def param_list(self, p):
        return 'param_list'

    @_('PRINT LPAREN res_write RPAREN SEMI')
    def print(self, p):
        return 'print'

    @_('expression pr1 comma_thing')
    def res_write(self, p):
        return 'res_write'

    @_('COMMA res_write', 'empty')
    def comma_thing(self, p):
        return 'comma_thing'

    # Make quadruples if the stack of operators is not empty and Make print quadruple
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
            if not lo['dir'] in range(4500, 6000) and self.check_var_is_array(lo):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if not ro['dir'] in range(4500, 6000) and self.check_var_is_array(ro):
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
            if not var:
                return
            if self.check_var_is_array(var):
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

    # Make quadruples if the stack of operators is not empty and goto_f quadruple
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
            if self.check_var_is_array(lo):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if self.check_var_is_array(ro):
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

    # Makes goto quadruples
    @_('')
    def dec2(self, p):
        falso = self.jumps.pop()
        self.quadruples.append(Quadruple(-1, -1, 'goto', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1
        self.quadruples[falso - 1].res = self.quad_counter

    # Actualizes goto quadruple
    @_('')
    def dec3(self, p):
        jump = self.jumps.pop()
        self.quadruples[jump - 1].res = self.quad_counter

    # Actualizes goto_f
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

    # Add quadruple counter to jumps stack
    @_('')
    def con0(self, p):
        self.jumps.append(self.quad_counter)

    # Make quadruples if the stack of operators is not empty and make goto_f quadruple
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
            if self.check_var_is_array(lo):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if self.check_var_is_array(ro):
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

    # Make goto quadruple and actualize goto_f
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

    # Append the result of the last quadruple to the for_var_dir stack
    @_('')
    def nc0(self, p):
        self.for_var_dir.append(self.quadruples[-1].res)

    # Make quadruples if the stack of operators is not empty and do quadruple with <= as its operator
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
            if not lo['dir'] in range(4500, 6000) and self.check_var_is_array(lo):
                lo_dir = '$' + str(self.last_arr_t.pop())
            else:
                lo_dir = lo['dir']
            if not ro['dir'] in range(4500, 6000) and self.check_var_is_array(ro):
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
                raise TypeError('Type mismatch')
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
                raise TypeError('Type mismatch')
            num_temps = self.function_table[self.curr_scope]['num_temps']
            t_dir = 3 * 300 + \
                int(num_temps.split('\u001f')[3]) + 3000
            self.function_table[self.curr_scope]['num_temps'] = self.update_num_temps(
                num_temps, 3)
            if self.check_var_is_array(var):
                var_dir = '$' + str(self.last_arr_t.pop())
            else:
                var_dir = var['dir']
            self.quadruples.append(
                Quadruple(self.for_var_dir[-1], var_dir, '<=', t_dir))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1

    # Make goto_f quadruple
    @_('')
    def nc2(self, p):
        last_quad = self.quadruples[-1].res
        self.quadruples.append(Quadruple(-1, last_quad, 'goto_f', -1))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1

    # Make goto quadruple and actualize goto_f
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

    @_('RETURN LPAREN expression fr0 RPAREN SEMI fr1')
    def function_returns(self, p):
        return 'function_returns'

    # Make return quadruple
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

    # Actualize has_returned to true
    @_('')
    def fr1(self, p):
        self.has_returned = True

    @ _('function_or_method vf0 LPAREN func_params RPAREN fp2 fp3 SEMI')
    def call_to_void_function(self, p):
        return 'call_to_void_function'

    # Make gosub quadruple
    @ _('')
    def fp2(self, p):
        self.quadruples.append(
            Quadruple(self.called_func, -1, 'gosub', -1))
        self.quad_counter += 1

    # Equalize parameter counter to 0
    @ _('')
    def fp3(self, p):
        self.param_counter = 0

    # make era quadruple
    @ _('')
    def vf0(self, p):
        self.called_func, quads = p[-1]
        if self.current_class != None:
            self.called_func = self.current_class + '.' + self.called_func
        self.quadruples.append(Quadruple(self.called_func, -1, 'era', -1))
        self.quad_counter += 1
        if quads:
            for q in quads:
                self.quadruples.append(q)
                self.quad_counter += 1

    @ _('expression fp1 param_list', 'empty')
    def func_params(self, p):
        return 'func_params'

    #  Make quadruples if the stack of operators is not empty and do param quadruples
    @ _('')
    def fp1(self, p):
        if not self.called_func in self.function_table:
            for i in range(1, len(self.symstack)):
                if hasattr(self.symstack[i * -1], 'lineno'):
                    lineno = self.symstack[i * -1].lineno
                    break
            self.found_errors = True
            print('ERROR: No function\033[1m',
                  self.called_func, '\033[0mwas found.')
            print('       Missing reference found on line', lineno)
            return
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
                self.found_errors = True
                print(
                    'ERROR: Too many parameters passed in call to function on line', self.symstack[-2].lineno)
                return
            try:
                sm.checkAssignment(self.types[int(self.function_table[self.called_func]
                                                  ['params'][self.param_counter])], self.types[(last_quad.res % 1500) // 300], '=')
            except TypeError:
                self.found_errors = True
                print(
                    'ERROR: Type mismatch on line', self.symstack[-2].lineno)
                print(
                    '       Expected value of type', self.types[int(self.function_table[self.called_func]['params'][self.param_counter])], 'got value of type', self.types[(last_quad.res % 1500) // 300], 'instead')
                return
            self.quadruples.append(
                Quadruple(last_quad.res, -1, 'param', self.param_counter))
            self.quad_counter += 1
            self.param_counter += 1
        else:
            val = self.stack_of_stacks[-2].pop()
            if self.param_counter == len(self.function_table[self.called_func]['params']):
                self.found_errors = True
                print(
                    'ERROR: Too many parameters passed in call to function on line', self.symstack[-2].lineno)
                return
            if not val:
                return
            try:
                sm.checkAssignment(self.types[int(self.function_table[self.called_func]
                                                  ['params'][self.param_counter])], self.types[(val['dir'] % 1500) // 300], '=')
            except TypeError:
                self.found_errors = True
                print(
                    'ERROR: Type mismatch on line', self.symstack[-2].lineno)
                print(
                    '       Expected value of type', self.types[int(self.function_table[self.called_func]['params'][self.param_counter])], 'got value of type', self.types[(last_quad.res % 1500) // 300], 'instead')
                return
            self.quadruples.append(
                Quadruple(val['dir'], -1, 'param', self.param_counter))
            self.quad_counter += 1
            self.param_counter += 1

    @ _('MAIN m1_add_to_func_table LPAREN RPAREN LCURL main0 var_declaration statements RCURL main2')
    def main(self, p):
        return 'main'

    # Actualize the jump of the first goto made int he list of quadruples
    @ _('')
    def main0(self, p):
        self.quadruples[0].res = self.quad_counter

    # Do end quadruple and delete function and class tables
    @ _('')
    def main2(self, p):
        self.quadruples.append(Quadruple(-1, -1, 'end', -1))
        del self.function_table[self.program_name]['vars']
        del self.function_table['main']['vars']
        for class_name in self.class_table:
            del self.class_table[class_name]['vars']
        pass

    # Add main to function table
    @ _('')
    def m1_add_to_func_table(self, p):
        self.curr_scope = 'main'
        self.add_to_func_table('main', None)

    @ _('')
    def empty(self, p):
        pass

    def error(self, p):
        if not p:
            return
        print('ERROR: Syntax error found on line', p.lineno)
        if p.value == 'var':
            print(
                '       All variable declarations must be done before any other statement')
        elif p.value == '(':
            print(
                '       Parentheses are not allowed in this position.')
        elif p.value == '{':
            print(
                '       Curly brackets are not allowed in this position.')
        elif p.value == '[':
            print(
                '       Brackets are not allowed in this position.')
        elif p.value == ')':
            print(
                '       Closing parenthesis found without matching opening one.')
        elif p.value == '}':
            print(
                '       Closing curly bracket without an opening one.')
        elif p.value == ']':
            print(
                '       Closing bracket without an opening one.')
        elif p.value == ';':
            print(
                '       Must only be used at the end of statements')
        elif p.value == '=':
            print(
                '       Assignment is not allowed here. Perhaps you meant to use ==?')
        else:
            print(
                '       Keyword or id misplaced')
        if not self.found_errors:
            print(
                '       It\'s possible that all other syntax errors may be fixed by solving this one.')
        self.errok()
        self.found_errors = True
        while True:
            tok = next(self.tokens, None)

            if tok == None:
                raise EOFError()

            if tok.type == 'SEMI':
                tok = next(self.tokens, None)
                return tok
