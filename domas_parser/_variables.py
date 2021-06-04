from sly.yacc import _decorator as _
from .domas_errors import RedefinitionError


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


@ _('COMMA CTE_I gvd3', 'empty')
def multidim(self, p):
    return 'multidim'


@ _('var_list COLON composite_type gvd5 SEMI', 'var_list COLON simple_type gvd5 SEMI var_declaration')
def simple_var(self, p):
    return 'simple_var'


@ _('COMMA ID gvd1 var_list', 'empty')
def var_list(self, p):
    return 'var_list'


@ _('')
def gvd3(self, p):
    # If we're dealing with a method of a class
    if self.current_class != None:
        self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var]['size'] *= p[-1]

    else:
        self.function_table[self.curr_scope]['vars'][self.latest_var]['size'] *= p[-1]


@ _('')
def gvd4(self, p):
    # If we're dealing with a method of a class
    if self.current_class != None:
        self.class_table[self.current_class][self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]

    else:
        self.function_table[self.curr_scope]['vars'][self.latest_var]['type'] = p[-1]


@ _('')
def gvd5(self, p):
    while len(self.stack_vars) > 0:
        curr_var = self.stack_vars.pop()
        # If we're dealing with a method of a class
        if self.current_class != None:
            self.class_table[self.current_class][self.curr_scope]['vars'][curr_var] = {
                'type': p[-1]}
        else:
            self.function_table[self.curr_scope]['vars'][curr_var] = {
                'type': p[-1]}
