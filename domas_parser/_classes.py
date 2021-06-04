from sly.yacc import _decorator as _
from .domas_errors import ReservedWordError, RedefinitionError, UndeclaredIdError
import copy


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
        self.class_table[p[-1]] = {'vars': {}}
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
    self.class_table[self.current_class]['vars'][self.latest_var] = {
        'size': p[-1]}


@ _('COMMA CTE_I ad3', 'empty')
def attr_multidim(self, p):
    return 'attr_multidim'


@ _('')
def ad3(self, p):
    self.class_table[self.current_class]['vars'][self.latest_var]['size'] *= p[-1]


@ _('')
def ad4(self, p):
    self.class_table[self.current_class]['vars'][self.latest_var]['type'] = p[-1]


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
        self.class_table[self.current_class]['vars'][curr_var] = {
            'type': p[-1]}


@ _('''def_type fd1_current_type FUNCTION ID md3 LPAREN m_parameters 
        RPAREN LCURL md4 var_declaration statements RCURL md5 fd6 
        method_definition''', 'empty')
def method_definition(self, p):
    return 'method_definition'


@ _('')
def md3(self, p):
    if (p[-1] == self.program_name or
            p[-1] in self.class_table or
            p[-1] in self.class_table[self.current_class]['vars'] or
            p[-1] in self.class_table[self.current_class]):
        raise RedefinitionError(p[-1])
    else:
        self.class_table[self.current_class][p[-1]
                                             ] = {'return_type': self.curr_func_type, 'vars': {}}
        self.last_func_added = p[-1]
        self.curr_scope = self.last_func_added


@ _('')
def md4(self, p):
    self.class_table[self.current_class][self.last_func_added]['start'] = self.quad_counter


@ _('')
def md5(self, p):
    # del self.function_table[self.last_func_added]['vars']
    pass


@ _('ID p1 COLON simple_type m2 m_param_choose', 'empty')
def m_parameters(self, p):
    return 'parameters'


@ _('')
def m2(self, p):
    if self.latest_var in self.class_table[self.current_class][self.curr_scope]['vars']:
        raise RedefinitionError({self.latest_var})
    else:
        self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var] = {
            'type': p[-1]}


@ _('COMMA m_parameters', 'empty')
def m_param_choose(self, p):
    return 'm_param_choose'


@ _('')
def out_class(self, p):
    self.current_class = None
    self.curr_scope = self.program_name
