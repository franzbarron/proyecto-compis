
from sly import Parser
from .domas_lexer import DomasLexer
from .domas_quadruples import Quadruple
from . import domas_semantic_cube as sm
import json  # to debug only
import sys
import copy
from inspect import currentframe
cf = currentframe()


class DomasParser(Parser):
    tokens = DomasLexer.tokens
    debugfile = 'parser.out'
    start = 'programa'
    var_stack = []
    class_table = {}
    current_class = None
    stack_operands = []
    stack_operators = []
    quadruples = []
    jumps = []
    quad_counter = 1
    param_counter = 1
    last_type = None
    temp_counter = 1

    def add_to_func_table(self, id, return_type):
        self.function_table[id] = {'return_type': return_type, 'vars': {}}

    def check_variable_exists(self, var):
        if self.current_class != None:
            return var in self.class_table[self.current_class][self.curr_scope]['vars'] or var in self.class_table[self.current_class]['vars']
        return var in self.function_table[self.curr_scope]['vars'] or var in self.function_table[self.program_name]['vars']

    def get_var_type(self, var):
        var = var.split('.')
        if self.current_class != None:
            if var[0] in self.class_table[self.current_class][self.curr_scope]['vars']:
                return self.class_table[self.current_class][self.curr_scope]['vars'][var[0]]['type']
            return self.class_table[self.current_class]['vars'][var[0]]['type']
        if len(var) == 2:
            obj_type = self.get_var_type(var[0])
            if obj_type in self.class_table and var[1] in self.class_table[obj_type]['vars']:
                return self.class_table[obj_type]['vars'][var[1]]['type']
        elif var[0] in self.function_table[self.curr_scope]['vars']:
            return self.function_table[self.curr_scope]['vars'][var[0]]['type']
        return self.function_table[self.program_name]['vars'][var[0]]['type']

    def make_and_push_quad(self):
        # print(f'make_and_push_quad line {sys._getframe().f_lineno}')
        # print('Operators: ', self.stack_operators)
        # print('Operands: ', self.stack_operands)
        ro = self.stack_operands.pop()
        lo = self.stack_operands.pop()
        op = self.stack_operators.pop()
        r_type = sm.checkOperation(lo['type'], ro['type'], op)
        self.quadruples.append(
            Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
        self.last_type = r_type
        self.stack_operands.append(
            {'value': 't' + str(self.temp_counter), 'type': r_type})
        self.temp_counter += 1
        self.quad_counter += 1
        # print('Made the quad ', self.quadruples[-1])

    @_('PROGRAM create_func_table ID add_func_table SEMI pro0 declarations')
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
    def create_func_table(self, p):
        self.function_table = {}

    @_('')
    def add_func_table(self, p):
        if p[-1] == 'main':
            raise SyntaxError('Keyword main cannot be used as function name')
        self.program_name = p[-1]
        self.curr_scope = p[-1]
        self.function_table = {p[-1]: {'return_type': None, 'vars': {}}}

    @_('class_declaration out_class var_declaration function_definition main')
    def declarations(self, p):
        return 'declarations'

    @_('')
    def out_class(self, p):
        self.current_class = None
        self.curr_scope = self.program_name

    @_('LBRACKET CTE_I ad2 attr_multidim RBRACKET COLON simple_type ad4 SEMI attribute_declaration')
    def attr_vector(self, p):
        return 'vector'

    @_('COMMA CTE_I ad3', 'empty')
    def attr_multidim(self, p):
        return 'multidim'

    @_('attr_var_list COLON simple_type ad5 SEMI attribute_declaration')
    def attr_simple_var(self, p):
        return 'simple_var'

    @_('COMMA ID ad1 var_list', 'empty')
    def attr_var_list(self, p):
        return 'var_list'

    @_('VAR ID ad1 attr_vector', 'VAR ID ad1 attr_simple_var', 'empty')
    def attribute_declaration(self, p):
        return 'var_declaration'

    @_('')
    def ad1(self, p):
        if p[-1] == self.program_name or p[-1] in self.class_table:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.var_stack.append(p[-1])

    @_('')
    def ad2(self, p):
        self.latest_var = self.var_stack.pop()
        if self.class_table[self.current_class]['vars']:
            self.class_table[self.current_class]['vars'][self.latest_var] = {
                'size': p[-1]}
        else:
            self.class_table[self.current_class]['vars'] = {
                self.latest_var: {'size': p[-1]}}

    @_('')
    def ad3(self, p):
        self.class_table[self.current_class]['vars'][self.latest_var]['size'] *= p[-1]

    @_('')
    def ad4(self, p):
        self.class_table[self.current_class]['vars'][self.latest_var]['type'] = p[-1]

    @_('')
    def ad5(self, p):
        while len(self.var_stack) > 0:
            curr_var = self.var_stack.pop()
            self.class_table[self.current_class]['vars'][curr_var] = {
                'type': p[-1]}

    @_('def_type fd1_current_type FUNCTION ID md3 LPAREN m_parameters RPAREN LCURL md4 var_declaration statements RCURL md5 fd6 method_definition', 'empty')
    def method_definition(self, p):
        return 'method_definition'

    @_('')
    def md3(self, p):
        if p[-1] in self.function_table or p[-1] in self.class_table:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.class_table[self.current_class][p[-1]
                                                 ] = {'return_type': self.curr_func_type, 'vars': {}}
            self.last_func_added = p[-1]
            self.curr_scope = self.last_func_added

    @_('')
    def md4(self, p):
        self.class_table[self.current_class][self.last_func_added]['start'] = self.quad_counter

    @_('')
    def md5(self, p):
        # del self.function_table[self.last_func_added]['vars']
        pass

    @_('ID p1 COLON simple_type m2 m_param_choose', 'empty')
    def m_parameters(self, p):
        return 'parameters'

    @_('COMMA m_parameters', 'empty')
    def m_param_choose(self, p):
        return 'm_param_choose'

    @_('')
    def m2(self, p):
        if self.latest_var in self.class_table[self.current_class][self.curr_scope]['vars']:
            raise SyntaxError(
                f'{self.latest_var} already declared as parameter')
        else:
            self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var] = {
                'type': p[-1]}

    @_('CLASS ID cd1 inherits LCURL ATTRIBUTES attribute_declaration METHODS method_definition RCURL class_declaration', 'empty')
    def class_declaration(self, p):
        return 'class_declaration'

    @_('')
    def cd1(self, p):
        if p[-1] in self.class_table or p[-1] == 'main':
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.class_table[p[-1]] = {'vars': {}}
            self.current_class = p[-1]

    @_('INHERITS ID cd3', 'empty')
    def inherits(self, p):
        return 'inherits'

    @_('')
    def cd3(self, p):
        if not p[-1] in self.class_table:
            raise SyntaxError(f'{p[-1]} is not a defined class')
        else:
            self.class_table[self.current_class] = copy.deepcopy(
                self.class_table[p[-1]])

    @_('VAR ID gvd1 vector', 'VAR ID gvd1 simple_var', 'empty')
    def var_declaration(self, p):
        return 'var_declaration'

    @_('LBRACKET CTE_I gvd2 multidim RBRACKET COLON simple_type gvd4 SEMI var_declaration')
    def vector(self, p):
        return 'vector'

    @_('COMMA CTE_I gvd3', 'empty')
    def multidim(self, p):
        return 'multidim'

    @_('var_list COLON composite_type gvd5 SEMI', 'var_list COLON simple_type gvd5 SEMI var_declaration')
    def simple_var(self, p):
        return 'simple_var'

    @_('COMMA ID gvd1 var_list', 'empty')
    def var_list(self, p):
        return 'var_list'

    @_('')
    def gvd1(self, p):
        if p[-1] == self.program_name or p[-1] in self.function_table or p[-1] in self.class_table:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        elif self.current_class != None and p[-1] in self.class_table[self.current_class]:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.var_stack.append(p[-1])

    @_('')
    def gvd2(self, p):
        self.latest_var = self.var_stack.pop()
        # If we're dealing with a method of a class
        if self.current_class != None:
            self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var] = {
                'size': p[-1]}

        elif self.function_table[self.curr_scope]['vars']:
            self.function_table[self.curr_scope]['vars'][self.latest_var] = {
                'size': p[-1]}
        else:
            self.function_table[self.curr_scope]['vars'] = {
                self.latest_var: {'size': p[-1]}}

    @_('')
    def gvd3(self, p):
        # If we're dealing with a method of a class
        if self.current_class != None:
            self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var]['size'] *= p[-1]

        else:
            self.function_table[self.curr_scope]['vars'][self.latest_var]['size'] *= p[-1]

    @_('')
    def gvd4(self, p):
        # If we're dealing with a method of a class
        if self.current_class != None:
            self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]

        else:
            self.function_table[self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]

    @_('')
    def gvd5(self, p):
        while len(self.var_stack) > 0:
            curr_var = self.var_stack.pop()
            # If we're dealing with a method of a class
            if self.current_class != None:
                self.class_table[self.current_class][self.curr_scope]['vars'][curr_var] = {
                    'type': p[-1]}
            else:
                self.function_table[self.curr_scope]['vars'][curr_var] = {
                    'type': p[-1]}

    @_('def_type fd1_current_type FUNCTION ID fd3_add_to_func_table LPAREN parameters RPAREN LCURL fd4 var_declaration statements RCURL fd5_borrar_var_table fd6 function_definition', 'empty')
    def function_definition(self, p):
        return 'function_definition'

    @_('')
    def fd1_current_type(self, p):
        self.curr_func_type = p[-1]

    @_('')
    def fd3_add_to_func_table(self, p):
        if p[-1] in self.function_table or p[-1] in self.class_table or p[-1] in self.function_table[self.program_name]['vars']:
            raise SyntaxError(f'Redefinition of {p[-1]}')
        else:
            self.add_to_func_table(p[-1], self.curr_func_type)
            self.last_func_added = p[-1]
            self.curr_scope = self.last_func_added
            self.function_table[self.program_name]['vars'][p[-1]
                                                           ] = {'type': self.curr_func_type}

    @_('')
    def fd4(self, p):
        self.function_table[self.last_func_added]['start'] = self.quad_counter

    @_('')
    def fd5_borrar_var_table(self, p):
        # del self.function_table[self.last_func_added]['vars']
        pass

    @_('')
    def fd6(self, p):
        self.quadruples.append(Quadruple(None, None, 'end_func', None))
        self.quad_counter += 1
        self.temp_counter = 1

    @_('statement statements', 'empty')
    def statements(self, p):
        return 'statements'

    @_('simple_type', 'VOID')
    def def_type(self, p):
        return p[0]

    @_('INT', 'FLOAT', 'STRING', 'BOOL')
    def simple_type(self, p):
        return p[0]

    @_('ID')
    def composite_type(self, p):
        return p[0]

    @_('ID p1 COLON simple_type p2 param_choose', 'empty')
    def parameters(self, p):
        return 'parameters'

    @_('COMMA parameters', 'empty')
    def param_choose(self, p):
        return 'param_choose'

    @_('')
    def p1(self, p):
        self.latest_var = p[-1]

    @_('')
    def p2(self, p):
        if self.latest_var in self.function_table[self.curr_scope]['vars']:
            raise SyntaxError(f'{p[-1]} already declared as parameter')
        self.function_table[self.curr_scope]['vars'][self.latest_var] = {
            'type': p[-1]}

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
        self.last_type = sm.checkOperation(v_type, lo['type'], '=')
        q = Quadruple(lo['value'], None, '=', self.latest_var)
        self.quadruples.append(q)
        self.quad_counter += 1
        # for num, quad in enumerate(self.quadruples, start=1):
        #     print(num, quad)

    @_('id_or_attribute', 'id_or_attribute v1 LBRACKET expression v2 RBRACKET',
        'id_or_attribute v1 LBRACKET expression v3 COMMA expression v4 RBRACKET')
    def variable(self, p):
        # print(f'variable line {sys._getframe().f_lineno}')
        # print('Variable p[0]: ', p[0])
        return p[0]

    @_('ID', 'ID DOT ID')
    def id_or_attribute(self, p):
        if len(p) > 1:
            # Checar si estamos en una clase
            if self.current_class != None:
                raise SyntaxError('Cannot have objects in a class')
            # Checar que la clase existe checando que la p[0] existe y no es INT, BOOL, ETC
            if p[0] in self.function_table[self.curr_scope]['vars']:
                var_type = self.function_table[self.curr_scope]['vars'][p[0]]['type']
                # print(var_type)
            elif p[0] in self.function_table[self.program_name]['vars']:
                var_type = self.function_table[self.program_name]['vars'][p[0]]['type']
            else:
                raise SyntaxError(f'Undefined variable {p[0]}')

            if not var_type in self.class_table:
                raise SyntaxError(f'{var_type} is not a class')
            if not p[2] in self.class_table[var_type]['vars']:
                raise SyntaxError(
                    f'Undefined attribute {p[2]} in class {var_type}')
            return p[0] + p[1] + p[2]
        return p[len(p) - 1]

    @_('')
    def v1(self, p):
        # Checar si la cosa es arreglo
        return None

    @_('')
    def v2(self, p):
        # Checar expresion es float o int y que sea <= tam
        return None

    @_('')
    def v3(self, p):
        # Checar expresion es float o int, que sea <= tam y guardarlo somewhere
        return None

    @_('')
    def v4(self, p):
        # Checar expresion es float o int, multiplicar por la cosa que guardamos en v3 y checar que sea <= tam
        return None

    @_('ID', 'ID DOT ID', 'CTE_I', 'CTE_F', 'CTE_STRING', 'cte_bool', 'call_to_function')
    def var_cte(self, p):
        if len(p) == 3:
            curr_class = self.get_var_type(p[0])
            curr_attr = p[2]
            if not curr_class in self.class_table or not curr_attr in self.class_table[curr_class]['vars']:
                raise SyntaxError(f'Variable {curr_attr} is not declared')
            else:
                cte_type = self.class_table[curr_class]['vars'][curr_attr]['type']
                return {'value': curr_attr, 'type': cte_type}
        if hasattr(p, 'CTE_I'):
            cte_type = 'int'
        elif hasattr(p, 'CTE_F'):
            cte_type = 'float'
        elif hasattr(p, 'CTE_STRING'):
            cte_type = 'string'
        elif hasattr(p, 'cte_bool'):
            cte_type = 'bool'
        elif hasattr(p, 'call_to_function'):
            # for num, quad in enumerate(self.quadruples, start=1):
            #     print(num, quad)
            return p[0]
        else:
            if not self.check_variable_exists(p[len(p) - 1]):
                raise SyntaxError(f'Variable {p[len(p) - 1]} is not declared')
            else:
                cte_type = self.get_var_type(p[len(p) - 1])

        return {'value': p[0], 'type': cte_type}

    @_('constant e2 operator e3 expression', 'constant e2', 'LPAREN e1 expression RPAREN e4', 'LPAREN e1 expression RPAREN e4 operator e3 expression')
    def expression(self, p):
        # print(f'Expression line {sys._getframe().f_lineno}')
        # print('Operators: ', self.stack_operators)
        # print('Operands: ', self.stack_operands)
        # for quad in self.quadruples:
        #     print(quad)
        # print('Expression p[0]:', p[0])
        return p[0]

    @_('')
    def e1(self, p):
        self.stack_operators.append('(')

    @_('')
    def e2(self, p):
        # print(f'e2 line {sys._getframe().f_lineno}')
        # print('Operators: ', self.stack_operators)
        # print('Operands: ', self.stack_operands)
        self.stack_operands.append(p[-1])

    @_('')
    def e3(self, p):
        # print(f'e3 line {sys._getframe().f_lineno}')
        # print('Operators: ', self.stack_operators)
        # print('Operands: ', self.stack_operands)
        # print('p[-1]: ', p[-1])
        # if len(self.stack_operators) > 0:
        # print('Operators top: ', self.stack_operators[-1])

        if len(self.stack_operators) == 0 or self.stack_operators[-1] == '(':
            # print(
            #     f'operators empty or top is ) line {sys._getframe().f_lineno}')
            self.stack_operators.append(p[-1])
        elif self.stack_operators[-1] == '*' or self.stack_operators[-1] == '/':
            # print(f'operators top is * or / line {sys._getframe().f_lineno}')
            self.make_and_push_quad()
            if (self.stack_operators and (self.stack_operators[-1] == '+' or self.stack_operators[-1] == '-')) and (p[-1] == '+' or p[-1] == '-'):
                # print(sys._getframe().f_lineno)
                self.make_and_push_quad()
            self.stack_operators.append(p[-1])
        elif p[-1] == '*' or p[-1] == '/':
            # print(f'p[-1] is * or / line {sys._getframe().f_lineno}')
            self.stack_operators.append(p[-1])
        elif self.stack_operators[-1] == '+' or self.stack_operators[-1] == '-':
            # print(f'operator top is + or - {sys._getframe().f_lineno}')
            self.make_and_push_quad()
            self.stack_operators.append(p[-1])
        elif p[-1] == '+' or p[-1] == '-':
            # print(f'p[-1] is + or - line {sys._getframe().f_lineno}')
            self.stack_operators.append(p[-1])
        elif self.stack_operators[-1] in sm.comparison_ops or self.stack_operators[-1] in sm.equality_ops:
            # print(f'operator top is comp or equal {sys._getframe().f_lineno}')
            self.make_and_push_quad()
            self.stack_operators.append(p[-1])
        elif p[-1] in sm.comparison_ops or p[-1] in sm.equality_ops:
            # print(f'operator top is comp or equal {sys._getframe().f_lineno}')
            self.stack_operators.append(p[-1])
        elif self.stack_operators[-1] in sm.logic_ops:
            # print(f'operator top is logic {sys._getframe().f_lineno}')
            self.make_and_push_quad()
            self.stack_operators.append(p[-1])
        elif p[-1] in sm.logic_ops:
            # print(f'operator top is logic {sys._getframe().f_lineno}')
            self.stack_operators.append(p[-1])

    @_('')
    def e4(self, p):
        while(self.stack_operators[-1] != '('):
            self.make_and_push_quad()
        self.stack_operators.pop()

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

    @_('id_or_attribute r1 COMMA read_h', 'id_or_attribute r1 RPAREN SEMI')
    def read_h(self, p):
        return 'read_h'

    @_('')
    def r1(self, p):
        self.quadruples.append(Quadruple(None, None, 'read', p[-1]))
        self.quad_counter += 1

    @_('function_or_method vf0 LPAREN func_params RPAREN fp2 fp3 ctf0')
    def call_to_function(self, p):
        return {'value': 't' + str(self.temp_counter - 1), 'type': self.function_table[p[0]]['return_type']}

    @_('')
    def ctf0(self, p):
        self.quadruples.append(
            Quadruple(self.last_func_added, None, '=', 't' + str(self.temp_counter)))
        self.quad_counter += 1
        self.temp_counter += 1

    @_('ID ctf1_exists_in_func_table', 'ID DOT ID')
    def function_or_method(self, p):
        # print('function_or_method')
        # for num, quad in enumerate(self.quadruples, start=1):
        #     print(num, quad)
        if(len(p) == 2):
            if not p[0] in self.function_table:
                raise SyntaxError(f'function {p[0]} is not defined')
            else:
                return p[0]
        else:
            # print('p2: ', p[2])
            return p[2]

    @_('')
    def ctf1_exists_in_func_table(self, p):
        if not p[-1] in self.function_table:
            raise SyntaxError(f'Function {p[-1]} is not defined')
        else:
            pass

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

    @_('')
    def pr1(self, p):
        made_quad = False
        while(len(self.stack_operators)):
            ro = self.stack_operands.pop()
            lo = self.stack_operands.pop()
            op = self.stack_operators.pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.quadruples.append(
                Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                Quadruple(None, None, 'print', last_quad.res))
            self.quad_counter += 1
        else:
            self.quadruples.append(
                Quadruple(None, None, 'print', self.stack_operands.pop()['value']))
            self.quad_counter += 1

    @_('TRUE', 'FALSE')
    def cte_bool(self, p):
        return p[0]

    @_('IF LPAREN expression dec1 RPAREN THEN LCURL statements RCURL else_stm')
    def decision_statement(self, p):
        return 'decision_statement'

    @_('')
    def dec1(self, p):
        while len(self.stack_operators):
            ro = self.stack_operands.pop()
            lo = self.stack_operands.pop()
            op = self.stack_operators.pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.quadruples.append(
                Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
            self.temp_counter += 1
            self.quad_counter += 1

        # print(f'dec1 line {sys._getframe().f_lineno}')
        # print('Last type:', self.last_type)
        if self.last_type != 'bool':
            raise SyntaxError(
                'Expression to evaluate in if statement is not boolean')
        else:
            last_quad = self.quadruples[-1].res
            self.quadruples.append(Quadruple(None, last_quad, 'goto_f', None))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
        # print('Cuadruplos:')
        # for quad in self.quadruples:
        #     print(quad)

    @_('dec2 ELSE LCURL statements RCURL dec3', 'empty dec4')
    def else_stm(self, p):
        return 'else_stm'

    @_('')
    def dec2(self, p):
        falso = self.jumps.pop()
        self.quadruples.append(Quadruple(None, None, 'goto', None))
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
        while len(self.stack_operators):
            ro = self.stack_operands.pop()
            lo = self.stack_operands.pop()
            op = self.stack_operators.pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.quadruples.append(
                Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
            self.temp_counter += 1
            self.quad_counter += 1
        # for quad in self.quadruples:
        #     print(quad)
        # print('Last type:', self.last_type)
        if self.last_type != 'bool':
            raise SyntaxError(
                'Expression to evaluate in if statement is not boolean')
        else:
            last_quad = self.quadruples[-1].res
            self.quadruples.append(Quadruple(None, last_quad, 'goto_f', None))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1

    @_('')
    def con2(self, p):
        # print(f'con2 line {sys._getframe().f_lineno}')
        falso = self.jumps.pop()
        ret = self.jumps.pop()
        self.quadruples.append(Quadruple(None, None, 'goto', ret))
        self.quadruples[falso - 1].res = self.quad_counter + 1
        self.quad_counter += 1
        # for num, quad in enumerate(self.quadruples, start=1):
        #     print(num, quad)

    @_('FOR variable ass1 EQUALS expression nc0 UNTIL expression nc1 DO nc2 LCURL statements RCURL nc3')
    def non_conditional(self, p):
        return 'non_conditional'

    @_('')
    def nc0(self, p):
        while len(self.stack_operators):
            ro = self.stack_operands.pop()
            lo = self.stack_operands.pop()
            op = self.stack_operators.pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.quadruples.append(
                Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
            self.temp_counter += 1
            self.quad_counter += 1
        # print(f'nc0 line {sys._getframe().f_lineno}')
        if len(self.stack_operands) == 0 == 0 and (self.last_type != 'int' and self.last_type != 'float'):
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif p[-1]['type'] != 'int' and p[-1]['type'] != 'float':
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif len(self.stack_operands) == 0:
            last_quad = self.quadruples[-1].res
            self.quadruples.append(
                Quadruple(self.latest_var, last_quad, '=', 't' + str(self.temp_counter)))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1
        else:
            self.quadruples.append(
                Quadruple(self.latest_var, p[-1]['value'], '=', 't' + str(self.temp_counter)))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1

    @_('')
    def nc1(self, p):
        # print(f'dec1 line {sys._getframe().f_lineno}')
        # print('Cuadruplos:')
        # for num, quad in enumerate(self.quadruples, start=1):
        #     print(num, quad)
        while len(self.stack_operators):
            self.make_and_push_quad()
        if len(self.stack_operands) == 0 and (self.last_type != 'int' and self.last_type != 'float'):
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif p[-1]['type'] != 'int' and p[-1]['type'] != 'float':
            raise SyntaxError(
                'Expression to evaluate in for statement is not integer or float')
        elif len(self.stack_operands) == 0:
            lo = self.jumps[-1]
            last_quad = self.quadruples[-1].res
            self.quadruples.append(
                Quadruple('r' + str(lo), last_quad, '<=', None))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
        else:
            lo = self.jumps[-1]
            self.quadruples.append(
                Quadruple('r' + str(lo), p[-1]['value'], '<=', 't' + str(self.temp_counter)))
            self.jumps.append(self.quad_counter)
            self.quad_counter += 1
            self.temp_counter += 1

    @_('')
    def nc2(self, p):
        last_quad = self.quadruples[-1].res
        self.quadruples.append(Quadruple(None, last_quad, 'goto_f', None))
        self.jumps.append(self.quad_counter)
        self.quad_counter += 1

    @_('')
    def nc3(self, p):
        #print(f'nc3 line {sys._getframe().f_lineno}')
        #print('Saltos:', self.jumps)
        falso = self.jumps.pop()
        cond = self.jumps.pop()
        to_update = self.jumps.pop()

        self.quadruples.append(
            Quadruple('r' + str(to_update), 1, '+', 'r' + str(to_update)))
        self.quad_counter += 1
        self.quadruples.append(Quadruple(None, None, 'goto', cond))
        self.quad_counter += 1
        self.quadruples[falso - 1].res = self.quad_counter

    @_('RETURN LPAREN expression fr0 RPAREN SEMI')
    def function_returns(self, p):
        return 'function_returns'

    @_('')
    def fr0(self, p):
        made_quad = False
        while(len(self.stack_operators)):
            self.make_and_push_quad()
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                Quadruple(None, None, 'return', last_quad.res))
            self.quad_counter += 1
            self.stack_operands.pop()
        else:
            self.quadruples.append(
                Quadruple(None, None, 'return',
                          self.stack_operands.pop()['value']))
            self.quad_counter += 1

    @ _('function_or_method vf0 LPAREN func_params RPAREN fp2 fp3 SEMI')
    def call_to_void_function(self, p):
        return 'call_to_void_function'

    @ _('')
    def fp2(self, p):
        self.quadruples.append(
            Quadruple(self.last_func_added, None, 'gosub', None))
        self.quad_counter += 1

    @ _('')
    def fp3(self, p):
        # for num, quad in enumerate(self.quadruples, start=1):
        #     print(num, quad)
        self.param_counter = 1

    @ _('')
    def vf0(self, p):
        #print('last_func_added', p[-1])
        self.last_func_added = p[-1]
        self.quadruples.append(Quadruple(p[-1], None, 'era', None))
        self.quad_counter += 1

    @ _('expression fp1 param_list', 'empty')
    def func_params(self, p):
        return 'func_params'

    @ _('')
    def fp1(self, p):
        made_quad = False
        while(len(self.stack_operators)):
            ro = self.stack_operands.pop()
            lo = self.stack_operands.pop()
            op = self.stack_operators.pop()
            self.last_type = sm.checkOperation(lo['type'], ro['type'], op)
            self.quadruples.append(
                Quadruple(lo['value'], ro['value'], op, 't' + str(self.temp_counter)))
            self.temp_counter += 1
            self.quad_counter += 1
            made_quad = True
        if made_quad:
            last_quad = self.quadruples[-1]
            self.quadruples.append(
                Quadruple(last_quad.res, None, 'param', f'param{self.param_counter}'))
            self.quad_counter += 1
            self.param_counter += 1
        else:
            val = self.stack_operands.pop()
            self.quadruples.append(
                Quadruple(val['value'], None, 'param', f'param{self.param_counter}'))
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
        self.quadruples.append(Quadruple(None, None, 'end', None))

    @ _('')
    def m1_add_to_func_table(self, p):
        self.curr_scope = 'main'
        self.add_to_func_table('main', None)

    @ _('')
    def empty(self, p):
        pass

    def error(self, p):
        print("Syntax error in input!", p.lineno, p)
