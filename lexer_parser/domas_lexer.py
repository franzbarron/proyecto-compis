from sly import Lexer


class DomasLexer(Lexer):
    tokens = {
        PROGRAM, VAR, MAIN, CLASS, INT, FLOAT, STRING, BOOL, VOID, READ,
        IF, THEN, ELSE, PRINT, WHILE, DO, INHERITS, RETURN, ATTRIBUTES,
        METHODS, FUNCTION, TRUE, FALSE, FOR, UNTIL, ID, CTE_I, CTE_F,
        CTE_STRING, PLUS, MINUS, MULTIPLY, DIVIDE, EQUALS, LPAREN, RPAREN,
        LCURL, RCURL, LBRACKET, RBRACKET, LT, GT, NEQ, LEQ, GEQ, SAME, COMMA,
        SEMI, COLON, DOT, AND, OR
    }

    ignore = ' \t'
    ignore_comment = r'%%.*'

    CTE_F = r'\d+\.\d+(e(\+|\-)?\d+)*'
    CTE_STRING = r'\"[^\"\n]*\"'
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