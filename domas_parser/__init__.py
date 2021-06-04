from sly import Parser
from domas_lexer.domas_lexer import DomasLexer
from .domas_errors import ReservedWordError


class DomasParser(Parser):
    # Parser directives
    tokens = DomasLexer.tokens
    debugfile = 'parser.out'
    start = 'programa'
    # Tables
    function_table = {}
    class_table = {}
    # Stacks
    stack_operands = []
    stack_operators = []
    stack_vars = []
    # Lists
    quadruples = []
    jumps = []
    # Counters
    quad_counter = 1
    param_counter = 1
    temp_counter = 1
    # Aux vars
    current_class = None
    last_type = None

    from ._programa import programa, pro0, pro1
    from ._classes import ad1, ad2, ad3, ad4, ad5, attr_multidim, attr_simple_var, attr_var_list, attr_vector, attribute_declaration, cd1, cd3, class_declaration, inherits, m_param_choose, m_parameters, m2, md3, md4, md5, method_definition, out_class
    from ._variables import gvd1, simple_var, gvd2, gvd3, gvd4, gvd5, multidim, var_declaration, var_list, vector
    from ._functions import fd1, fd3, fd4, fd5, fd6
    from ._assignment import ass1, ass2, assignment

    @ _('class_declaration out_class var_declaration function_definition main')
    def declarations(self, p):
        return 'declarations'

    @_('assignment', 'call_to_void_function', 'function_returns', 'read', 'print',
       'decision_statement', 'repetition_statement')
    def statement(self, p):
        return 'statement'

    @ _('')
    def empty(self, p):
        pass

    def error(self, p):
        print(p.value in DomasLexer.reserved_words)
        if p.value in DomasLexer.reserved_words:
            raise ReservedWordError(p.value)
        else:
            print("Syntax error in input!", p.lineno, p)
