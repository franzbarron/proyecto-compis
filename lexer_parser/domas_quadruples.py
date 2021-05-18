# Quadruple generator
class Quadruple:
    def __init__(self, lo, ro, op, res):
        self.lo = lo
        self.ro = ro
        self.op = op
        self.res = res

    def __str__(self):
        return f'({self.lo}, {self.ro}, {self.op}, {self.res})'
