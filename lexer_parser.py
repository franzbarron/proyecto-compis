from sly import Lexer, Parser
import sys


class UHULexer(Lexer):
    tokens = {
        PROGRAM, VAR, MAIN, CLASS, INT, FLOAT, STRING, BOOL, VOID, READ,
        IF, THEN, ELSE, PRINT, WHILE, DO, INHERITS, RETURN, ATTRIBUTES,
        METHODS, FUNCTION, TRUE, FALSE, FOR, UNTIL, ID, CTE_I, CTE_F,
        CTE_STRING, PLUS, MINUS, MULTIPLY, DIVIDE, EQUALS, LPAREN, RPAREN,
        LCURL, RCURL, LBRACKET, RBRACKET, LT, GT, NEQ, LEQ, GEQ, SAME, COMMA,
        SEMI, COLON, DOT, AND, OR
    }

    ignore = ' \t'

    CTE_F = r'\d+\.\d+(e(\+|\-)?\d+)*'
    CTE_STRING = r'\"[^\"]*\"'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    CTE_I = r'\d+'
    PLUS = r'\+'
    MINUS = r'\-'
    MULTIPLY = r'\*'
    DIVIDE = r'\/'
    SAME = r'=='
    EQUALS = r'='
    LPAREN = r'\('
    RPAREN = r'\)'
    LCURL = r'\{'
    RCURL = r'\}'
    LBRACKET = r'\['
    RBRACKET = r'\]'
    NEQ = r'<>'
    LEQ = r'<='
    GEQ = r'>='
    LT = r'<'
    GT = r'>'
    COMMA = r','
    SEMI = r';'
    COLON = r':'
    DOT = r'\.'
    AND = r'&'
    OR = r'\|'

    ID['program'] = PROGRAM
    ID['var'] = VAR
    ID['main'] = MAIN
    ID['class'] = CLASS
    ID['int'] = INT
    ID['float'] = FLOAT
    ID['string'] = STRING
    ID['bool'] = BOOL
    ID['void'] = VOID
    ID['read'] = READ
    ID['if'] = IF
    ID['then'] = THEN
    ID['else'] = ELSE
    ID['print'] = PRINT
    ID['while'] = WHILE
    ID['do'] = DO
    ID['inherits'] = INHERITS
    ID['return'] = RETURN
    ID['attributes'] = ATTRIBUTES
    ID['methods'] = METHODS
    ID['function'] = FUNCTION
    ID['true'] = TRUE
    ID['false'] = FALSE
    ID['for'] = FOR
    ID['until'] = UNTIL

    def CTE_I(self, t):
        t.value = int(t.value)
        return t

    def CTE_F(self, t):
        t.value = float(t.value)
        return t

    def CTE_STRING(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        print("Illegal character '%s'" % t.value[0])
        self.index += 1


class UHUParser(Parser):
    tokens = UHULexer.tokens
    debugfile = 'parser.out'
    start = 'programa'

    @_('PROGRAM ID SEMI declarations')
    def programa(self, p):
        return 'programa'

    @_('class_declaration var_declaration function_definition main')
    def declarations(self, p):
        return 'declarations'

    @_('CLASS ID inherits LCURL ATTRIBUTES var_declaration METHODS function_definition RCURL class_declaration', 'empty')
    def class_declaration(self, p):
        return 'class_declaration'

    @_('INHERITS ID', 'empty')
    def inherits(self, p):
        return 'inherits'

    @_('VAR ID vector', 'VAR ID simple_var', 'empty')
    def var_declaration(self, p):
        return 'var_declaration'

    @_('LBRACKET CTE_I multidim RBRACKET COLON simple_type SEMI var_declaration')
    def vector(self, p):
        return 'vector'

    @_('COMMA CTE_I', 'empty')
    def multidim(self, p):
        return 'multidim'

    @_('var_list COLON composite_type SEMI', 'var_list COLON simple_type SEMI var_declaration')
    def simple_var(self, p):
        return 'simple_var'

    @_('COMMA ID var_list', 'empty')
    def var_list(self, p):
        return 'var_list'

    @_('def_type FUNCTION ID LPAREN parameters RPAREN LCURL var_declaration statements RCURL function_definition', 'empty')
    def function_definition(self, p):
        return 'function_definition'

    @_('statement statements', 'empty')
    def statements(self, p):
        return 'statements'

    @_('simple_type', 'VOID')
    def def_type(self, p):
        return 'def_type'

    @_('INT', 'FLOAT', 'STRING', 'BOOL')
    def simple_type(self, p):
        return 'simple_type'

    @_('ID')
    def composite_type(self, p):
        return 'composite_type'

    @_('ID COLON simple_type param_choose')
    def parameters(self, p):
        return 'parameters'

    @_('COMMA parameters', 'empty')
    def param_choose(self, p):
        return 'param_choose'

    @_('assignment', 'call_to_void_function', 'function_returns', 'read', 'print',
       'decision_statement', 'repetition_statement', 'expression')
    def statement(self, p):
        return 'statement'

    @_('variable EQUALS expression SEMI')
    def assignment(self, p):
        return 'assignment'

    @_('id_or_attribute', 'id_or_attribute LBRACKET exp RBRACKET',
        'id_or_attribute LBRACKET exp COMMA exp RBRACKET')
    def variable(self, p):
        return 'variable'

    @_('ID', 'ID DOT ID')
    def id_or_attribute(self, p):
        return 'id_or_attribute'

    @_('exp', 'relop', 'logop')
    def expression(self, p):
        return 'expression'

    @_('relop logical_operator relop')
    def logop(self, p):
        return 'logop'

    @_('AND', 'OR')
    def logical_operator(self, p):
        return 'logical_operator'

    @_('exp relational_operator exp')
    def relop(self, p):
        return 'relop'

    @_('LT', 'GT', 'SAME', 'GEQ', 'LEQ', 'NEQ')
    def relational_operator(self, p):
        return 'relational_operator'

    @_('term_or_call', 'term_or_call PLUS term_or_call', 'term_or_call MINUS term_or_call')
    def exp(self, p):
        return 'exp'

    @_('term', 'call_to_function')
    def term_or_call(self, p):
        return 'term_or_call'

    @_('factor_or_call', 'factor_or_call MULTIPLY exp', 'factor_or_call DIVIDE exp')
    def term(self, p):
        return 'term'

    @_('factor', 'call_to_function')
    def factor_or_call(self, p):
        return 'factor_or_call'

    @_('parenthetical', 'constant')
    def factor(self, p):
        return 'factor'

    @_('LPAREN expression RPAREN')
    def parenthetical(self, p):
        return 'parenthetical'

    @_('PLUS var_cte', 'MINUS var_cte', 'var_cte')
    def constant(self, p):
        return 'constant'

    @_('READ LPAREN read_h')
    def read(self, p):
        return 'read'

    @_('id_or_attribute COMMA read_h', 'id_or_attribute RPAREN SEMI')
    def read_h(self, p):
        return 'read_h'

    @_('function_or_method LPAREN func_params RPAREN')
    def call_to_function(self, p):
        return 'call_to_function'

    @_('ID', 'ID DOT ID')
    def function_or_method(self, p):
        return 'function_or_method'

    @_('expression param_list', 'empty')
    def func_params(self, p):
        return 'func_params'

    @_('COMMA expression param_list', 'empty')
    def param_list(self, p):
        return 'param_list'

    @_('PRINT LPAREN res_write RPAREN SEMI')
    def print(self, p):
        return 'print'

    @_('write_h comma_thing')
    def res_write(self, p):
        return 'res_write'

    @_('COMMA res_write', 'empty')
    def comma_thing(self, p):
        return 'comma_thing'

    @_('var_cte', 'expression')
    def write_h(self, p):
        return 'write_h'

    @_('ID', 'ID DOT ID', 'CTE_I', 'CTE_F', 'CTE_STRING', 'cte_bool')
    def var_cte(self, p):
        return 'var_cte'

    @_('TRUE', 'FALSE')
    def cte_bool(self, p):
        return 'cte_bool'

    @_('IF LPAREN expression RPAREN THEN LCURL statements RCURL else_stm')
    def decision_statement(self, p):
        return 'decision_statement'

    @_('ELSE LCURL statements RCURL', 'empty')
    def else_stm(self, p):
        return 'else_stm'

    @_('conditional', 'non_conditional')
    def repetition_statement(self, p):
        return 'repetition_statement'

    @_('WHILE LPAREN expression RPAREN DO LCURL statements RCURL')
    def conditional(self, p):
        return 'conditional'

    @_('FOR variable EQUALS expression UNTIL expression DO LCURL statements RCURL')
    def non_conditional(self, p):
        return 'non_conditional'

    @_('RETURN LPAREN expression RPAREN SEMI')
    def function_returns(self, p):
        return 'function_returns'

    @_('call_to_function SEMI')
    def call_to_void_function(self, p):
        return 'call_to_void_function'

    @_('MAIN LPAREN RPAREN LCURL var_declaration statements RCURL')
    def main(self, p):
        return 'main'

    @_('')
    def empty(self, p):
        pass

    def error(self, p):
        print("Syntax error in input!", p.lineno, p)


if __name__ == '__main__':
    lexer = UHULexer()
    parser = UHUParser()
    filename = 'tests/test.txt'

    if(len(sys.argv) > 1):
        filename = sys.argv[1]

    with open(filename) as fp:
        try:
            result = parser.parse(lexer.tokenize(''.join(fp)))
            print(result)
        except EOFError:
            pass
