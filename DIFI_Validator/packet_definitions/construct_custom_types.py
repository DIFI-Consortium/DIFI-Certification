from construct import BitsInteger, Int64ub, Int64sb, Int16sb, ExprAdapter, Int32ub, Int64ub, Int64sb

def UnsignedInt64Scaled():
    return ExprAdapter(Int64ub, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def SignedInt64Scaled():
    return ExprAdapter(Int64sb, lambda obj, ctx: obj / 2.0 ** 20, lambda obj, ctx: int(obj * 2.0 ** 20))

def SignedInt16Scaled():
    return ExprAdapter(Int16sb, lambda obj, ctx: obj / 2.0 ** 7, lambda obj, ctx: int(obj * 2.0 ** 7))

def Bits7Year(): # meant for versionInfo.year field, which is years since 2000
    return ExprAdapter(Bits(7), lambda obj, ctx: obj + 2000, lambda obj, ctx: int(obj - 2000))

# The following are aliased so that they 1) show up yellow and 2) shorter and more concise code
def Bits(N):
    return BitsInteger(N)

def UnsignedInt32():
    return Int32ub

def UnsignedInt64():
    return Int64ub

def SignedInt64():
    return Int64sb
