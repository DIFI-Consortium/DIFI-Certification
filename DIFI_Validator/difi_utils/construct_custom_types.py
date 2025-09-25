from construct import BitsInteger, Int64ub, Int64sb, Int16sb, ExprAdapter

def Int64ubScaled():
    return ExprAdapter(Int64ub, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int64sbScaled():
    return ExprAdapter(Int64sb, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def Int16sbScaled():
    return ExprAdapter(Int16sb, lambda obj, ctx: obj / 2.0 ** 7, lambda obj, ctx: int(obj * 2.0 ** 7))

# This is aliased so that it 1) shows up yellow instead of green, and 2) shorter and more concise code
def Bits(N):
    return BitsInteger(N)
