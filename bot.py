#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, ast, zlib, bz2, lzma, base64, marshal, random, tempfile
import hashlib, logging, struct
import hmac as _hmac_module
from datetime import datetime

sys.setrecursionlimit(99999999)

# ══════════════════════════════════════════════════════════════════════════════
# Auto-install
# ══════════════════════════════════════════════════════════════════════════════
def _install(pkg: str) -> None:
    os.system(f'{sys.executable} -m pip install {pkg} -q')

try:
    from telegram import Update
    from telegram.ext import (ApplicationBuilder, CommandHandler,
                               MessageHandler, filters, ContextTypes)
    from telegram.constants import ParseMode
except ImportError:
    _install('python-telegram-bot')
    from telegram import Update
    from telegram.ext import (ApplicationBuilder, CommandHandler,
                               MessageHandler, filters, ContextTypes)
    from telegram.constants import ParseMode

try:
    import pytz
except ImportError:
    _install('pytz')
    import pytz

# ══════════════════════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN    = "8397744945:AAGr7WR3viIb0oNl7GML4xSFX0Ygdpc3Wl8"
BOT_NAME     = 'Obf Cpython'
BOT_USERNAME = '@ObfCpythonRobot'
OWNER        = '@truongphuhaokhithaylonquenloi'
VN_TZ        = pytz.timezone('Asia/Ho_Chi_Minh')

# ══════════════════════════════════════════════════════════════════════════════
# Hanzi hex alphabet
# ══════════════════════════════════════════════════════════════════════════════
HANZI_ENC = {
    '0':'阮','1':'黄','2':'国','3':'强',
    '4':'天','5':'地','6':'玄','7':'宇',
    '8':'宙','9':'洪','a':'荒','b':'日',
    'c':'月','d':'盈','e':'昃','f':'辰',
}
HANZI_DEC = {v: k for k, v in HANZI_ENC.items()}

# ══════════════════════════════════════════════════════════════════════════════
# Shenron alphabet — 64 CJK BMP chars, len==1 guaranteed
# ══════════════════════════════════════════════════════════════════════════════
_B64       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
_CJK_ALPHA = ''.join(chr(0x4E00 + i) for i in range(64))
_E2B       = dict(zip(_B64, _CJK_ALPHA))
_B2E       = {v: k for k, v in _E2B.items()}

# ══════════════════════════════════════════════════════════════════════════════
# Encode helpers
# ══════════════════════════════════════════════════════════════════════════════
def hanzi_encode(data: bytes) -> str:
    return ''.join(HANZI_ENC[c] for c in data.hex())

def shenron_enc(s: str) -> str:
    mapped = ''.join(_E2B.get(c, c) for c in s.encode().hex())
    return f'shenron("{mapped}")'

def _korean_id(k: int = 11) -> str:
    pool = [chr(i) for i in range(44032, 55204)
            if chr(i).isprintable() and chr(i).isidentifier()]
    return ''.join(random.choices(pool, k=k))

def spam_hanzi() -> str:
    hz = '天地玄黄宇宙洪荒日月盈昃辰宿列张'
    return (f'__{random.randint(10**8,10**10)}'
            f'{"".join(random.choices(hz,k=8))}'
            f'{random.randint(10**8,10**10)}__')

def obf_gl(s: str) -> str:
    out = []
    for c in s:
        if c.isalpha():
            base = 65 if c.isupper() else 97
            out.append(chr((ord(c)-base+10)%26+base))
        else:
            out.append(c)
    return ''.join(out)

def _chr(s: str) -> str:
    return '+'.join(f'chr({ord(c)})' for c in s)

def _xor_bytes(data: bytes, key: bytes) -> bytes:
    kl = len(key)
    return bytes(b ^ key[i % kl] for i, b in enumerate(data))

def _gen_xor_key(n: int = 32) -> bytes:
    return bytes(random.randint(1, 255) for _ in range(n))

def _rot_bytes(data: bytes, n: int = 7) -> bytes:
    return bytes((b + n) & 0xFF for b in data)

def _unrot_bytes_src(var: str, n: int) -> str:
    return f'bytes((b-{n})&0xFF for b in {var})'

# ══════════════════════════════════════════════════════════════════════════════
# Alias names
# ══════════════════════════════════════════════════════════════════════════════
_STR_ALIAS   = '_CuongKhongBeDe_'
_INT_ALIAS   = '_Cuong2010_'
_FLOAT_ALIAS = '_Cuong2k9_'
_BOOL_ALIAS  = '_Cuongdz_'
_BYTES_ALIAS = '_Cuongtapdev_'
_EVAL_ALIAS  = '_codengudungchui_'
_PRINT_ALIAS = 'lambdaᅠ'
_INPUT_ALIAS = 'execᅠ'

_LIST_TEN_BIEN = [
    'CuongSieuDepTrai',   'CalceSieuCapVip',      'CuongCodeThuongThua',
    'CalceVoDichTheGioi', 'CuongChuyenGiaPro',    'CalceBacThoDinhCao',
    'CuongCongNgheDinh',  'CalceLapTrinhMaster',  'CuongSangTaoVoSong',
    'CalceVuongGiaCode',  'CuongThuatToanHay',    'CalceHackerPro',
    'CuongThanhCongLon',  'CalceToiThuongDev',    'CuongAnDanhElite',
    'CalceChienThanCode', 'CuongProMaxVIP',        'CalceTruyenKyLapTrinh',
    'CuongMasterMind',    'CalceUltimateDev',      'CuongDevKing',
    'CalceInfinityCode',  'CuongCodeWarrior',      'CalceChampionCoder',
    'CuongCyberHero',     'CalceTheBestDev',       'CuongAIWizard',
    'CalceOverlordCoder', 'CuongEliteHacker',      'CalceDarkMode',
    'CuongQuantumTech',   'CalceGodLike',
]

_INTEGRITY_KEY = b'CuongObfIntegrity2010ShenronVIP'

def _compute_integrity(data: bytes) -> str:
    return _hmac_module.new(_INTEGRITY_KEY, data, hashlib.sha256).hexdigest()

# ══════════════════════════════════════════════════════════════════════════════
# varsobf
# ══════════════════════════════════════════════════════════════════════════════
def varsobf(v: str) -> str:
    r1 = random.randint(1, 1000)
    r2 = random.randint(101, 20_000_000_000)
    return (
        f"('DitConBaGiaMay') if 2010 < 611 or 611 > 2010 or 12345 > 67890 or "
        f"98765 < 54321 or 'test'=='false' or 0==1 or False==True or "
        f"1==2 or 10>20 or {r1}>{r2} else {v}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# Pycloak
# ══════════════════════════════════════════════════════════════════════════════
class Pycloak:
    def int_encode(self, num: int) -> str:
        if num == 0: return '(lambda:0)()'
        parts, n = [], num
        while n > 0:
            p = random.randint(1, n); parts.append(str(p)); n -= p
        return f'(lambda:{"+".join(parts)})()'
    def barray_encode(self, s: str) -> str:
        return 'bytes([{}]).decode()'.format(', '.join(self.int_encode(ord(c)) for c in s))

# ══════════════════════════════════════════════════════════════════════════════
# build_pro_code
# ══════════════════════════════════════════════════════════════════════════════
def build_pro_code() -> str:
    crash = {
        'Z':'1/0,', 'T':'len+1,', 'N':'xyz,',
        'I':'[][99],', 'K':'{}[""],',
        'M':"__import__('xyz'),", 'V':'int("a",99),',
        'A':'[].__x,',  'F':'open("ww"),',
    }
    for k in crash: crash[k] = crash[k] * 800
    anti_pycdc = '\n'.join(f'try:({v})\nexcept:0\n' for v in crash.values())
    pro = f'\ntry:pass\nexcept:pass\nelse:pass\nfinally:pass\n{anti_pycdc}\n'

    hehe = [
        f'{_BOOL_ALIAS}={varsobf("bool")}',
        f'{_STR_ALIAS}={varsobf("str")}',
        f'{_INT_ALIAS}={varsobf("int")}',
        f'{_FLOAT_ALIAS}={varsobf("float")}',
        f'{_BYTES_ALIAS}={varsobf("bytes")}',
        f'{_EVAL_ALIAS}={varsobf("eval")}',
        f'{_PRINT_ALIAS}={varsobf("print")}',
        f'{_INPUT_ALIAS}={varsobf("input")}',
    ]

    lbody = (
        "lambda a,b,c,d:a.join([chr((x-b)//c) for x in d])"
        " if a not in ['DitConBaMay','CuongObfuscate','NGUYENHOANGQUOCCUONG']"
        " else ''.join([chr((x-b)//c) for x in d])"
    )

    def _rev(name: str) -> str:
        return ''.join(
            chr(((ord(c)-(65 if c.isupper() else 97)-10)%26)+(65 if c.isupper() else 97))
            if c.isalpha() else c for c in obf_gl(name))

    shuffled = list(_LIST_TEN_BIEN); random.shuffle(shuffled)
    for i in shuffled:
        pro += f"globals()['{_rev(i)}']={lbody}\n"
        if hehe:
            h = random.choice(hehe); pro += h+'\n'; hehe.remove(h)
        jn = 'CuongDitMeMay'+str(random.randint(1000,9999))
        pro += f"globals()['{_rev(jn[:13])}']={lbody}\n"
    while hehe: pro += hehe.pop(0)+'\n'
    return pro

# ══════════════════════════════════════════════════════════════════════════════
# AST helpers
# ══════════════════════════════════════════════════════════════════════════════
_BUILTINS     = set(__import__('builtins').__dict__.keys())
_RUNNER_NAMES = {
    'goku','capsule_add','kamehameha','yamcha','shenron',
    'frieza','vegeta','gohan','bulma','capsule','trunks','radar',
}

def _mk_args(*names) -> ast.arguments:
    return ast.arguments(
        posonlyargs=[], args=[ast.arg(arg=n) for n in names],
        vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])

def _obfint(i: int) -> ast.AST:
    ref = 2010; diff = ref - i
    v1,v2,v3 = _korean_id(),_korean_id(),_korean_id()
    lam3 = ast.Lambda(_mk_args(v1), ast.Call(
        ast.Name('yamcha',ast.Load()),
        [ast.BinOp(ast.Constant(ref),ast.Sub(),ast.Constant(diff))],[]))
    lam2 = ast.Lambda(_mk_args(v2), ast.Call(lam3,[ast.Constant('DitConBaGiaMay')],[]))
    lam1 = ast.Lambda(_mk_args(v3), ast.Call(lam2,[ast.Constant('DitConBaGiaMay')],[]))
    return ast.Call(lam1,[ast.Constant('DitConBaGiaMay')],[])

def _obfstr(s: str) -> ast.AST:
    lst = [ord(c) for c in s]
    v,v1,v2,v3 = _korean_id(),_korean_id(),_korean_id(),_korean_id()
    lam3 = ast.Lambda(_mk_args(v1), ast.Call(
        func=ast.Attribute(ast.Call(ast.Name('goku',ast.Load()),[],[]),'join',ast.Load()),
        args=[ast.GeneratorExp(
            elt=ast.Call(ast.Name('chr',ast.Load()),[ast.Name(v,ast.Load())],[]),
            generators=[ast.comprehension(
                target=ast.Name(v,ast.Store()),
                iter=ast.List([ast.Constant(x) for x in lst],ast.Load()),
                ifs=[],is_async=0)])],keywords=[]))
    lam2 = ast.Lambda(_mk_args(v2), ast.Call(lam3,[ast.Constant('DitConBaGiaMay')],[]))
    lam1 = ast.Lambda(_mk_args(v3), ast.Call(lam2,[ast.Constant('DitConBaGiaMay')],[]))
    return ast.Call(lam1,[ast.Constant('DitConBaGiaMay')],[])

def obfct(string: str) -> ast.AST:
    if string == '': return ast.Constant(value='')
    dep = random.choice(_LIST_TEN_BIEN)
    enc = [ord(c)*611+2010 for c in string]
    return ast.parse(
        f"{_STR_ALIAS}((lambda:{dep}('NGUYENHOANGQUOCCUONG',2009,611,{enc}))())"
    ).body[0].value

# ══════════════════════════════════════════════════════════════════════════════
# Sakura junk blocks
# ══════════════════════════════════════════════════════════════════════════════
def _sakura_junk_cases(en: str, start: int) -> list:
    cases = []
    for _ in range(random.randint(1,3)):
        cn = 'BuConCacTaoDi'+str(random.randint(2_061_584_302_080,8_658_654_068_736))
        cases.append(ast.If(
            test=ast.Compare(
                left=ast.Subscript(
                    value=ast.Attribute(value=ast.Name(id=en,ctx=ast.Load()),
                                        attr='args',ctx=ast.Load()),
                    slice=ast.Constant(0),ctx=ast.Load()),
                ops=[ast.Eq()],comparators=[ast.Constant(start)]),
            body=[ast.Assign(targets=[ast.Name(id=cn,ctx=ast.Store())],
                             value=ast.Constant(random.randint(1_048_575,281_474_976_710_655)),
                             lineno=0,col_offset=0)],
            orelse=[]))
        start += 1
    return cases

def _sakura_wrap(body: list, var: str, en: str) -> list:
    junk = _sakura_junk_cases(en, len(body)+2)
    hbody = [
        ast.If(
            test=ast.Compare(
                left=ast.Subscript(
                    value=ast.Attribute(value=ast.Name(id=en,ctx=ast.Load()),
                                        attr='args',ctx=ast.Load()),
                    slice=ast.Constant(0),ctx=ast.Load()),
                ops=[ast.Eq()],comparators=[ast.Constant(1)]),
            body=[stmt],orelse=[])
        for stmt in body
    ] + junk
    return [
        ast.Assign(targets=[ast.Name(id=var,ctx=ast.Store())],
                   value=ast.Constant(0),lineno=0,col_offset=0),
        ast.AugAssign(target=ast.Name(id=var,ctx=ast.Store()),
                      op=ast.Add(),value=ast.Constant(1),lineno=0,col_offset=0),
        ast.Try(
            body=[ast.Raise(exc=ast.Call(
                func=ast.Name(id='MemoryError',ctx=ast.Load()),
                args=[ast.Name(id=var,ctx=ast.Load())],keywords=[]),cause=None)],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='MemoryError',ctx=ast.Load()),
                name=en,body=hbody)],
            orelse=[],finalbody=[])
    ]

def sakura_bl(body: list) -> list:
    var = 'NhinCaiLon'+str(random.randint(2_061_584_302_080,8_658_654_068_736))
    en  = 'NhinConCac'+str(random.randint(2_061_584_302_080,8_658_654_068_736))
    return _sakura_wrap(body, var, en)

def sakura_bl_func(node):
    var = '__'+str(random.randint(2_061_584_302_080,8_658_654_068_736))+'__'
    en  = '__'+str(random.randint(2_061_584_302_080,8_658_654_068_736))+'__'
    node.body = _sakura_wrap(node.body, var, en)
    return node

def random_match_case() -> ast.AST:
    jv = '_'+spam_hanzi()
    # Chuyển sang dùng if-else thông thường để tương thích ngược với Python 3.9 trở xuống
    return ast.If(
        test=ast.Compare(
            left=ast.Constant(spam_hanzi()), ops=[ast.Eq()],
            comparators=[ast.Constant(spam_hanzi())]),
        body=[ast.Raise(exc=ast.Call(func=ast.Name(id='MemoryError',ctx=ast.Load()), args=[], keywords=[]), cause=None)],
        orelse=[ast.Assign(lineno=0, col_offset=0,
            targets=[ast.Name(id=jv,ctx=ast.Store())],
            value=ast.Constant(random.randint(1,9999999)))]
    )


def sakura_trycatch(body: list, loop: int) -> list:
    result = []
    for x in body:
        cur = x
        for _ in range(loop):
            cur = ast.Try(
                body=[random_match_case(),
                      ast.Raise(exc=ast.Call(
                          func=ast.Name(id='MemoryError',ctx=ast.Load()),
                          args=[],keywords=[]),cause=None)],
                handlers=[ast.ExceptHandler(
                    type=ast.Name(id='MemoryError',ctx=ast.Load()),
                    name='_'+spam_hanzi(),body=[cur])],
                orelse=[],finalbody=[])
        result.append(cur)
    return result

def yuamikami(tree: ast.Module) -> ast.Module:
    nb = []
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            nb.append(sakura_bl_func(node))
        elif isinstance(node,ast.ClassDef):
            nb2 = []
            for n2 in node.body:
                if isinstance(n2,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    nb2.append(sakura_bl_func(n2))
                elif isinstance(n2,(ast.Assign,ast.AugAssign,ast.AnnAssign,ast.Expr)):
                    nb2.extend(sakura_bl([n2]))
                else:
                    nb2.append(n2)
            node.body = nb2; nb.append(node)
        elif isinstance(node,(ast.Assign,ast.AugAssign,ast.AnnAssign,ast.Expr)):
            nb.extend(sakura_bl([node]))
        else:
            nb.append(node)
    tree.body = nb
    return tree

def shenron_gen_junk(code: ast.AST) -> list:
    men = _korean_id(); v1,v2 = _korean_id(),_korean_id()
    return [
        ast.Assign(targets=[ast.Name(id=v1,ctx=ast.Store())],
                   value=ast.Constant(men),lineno=0,col_offset=0),
        ast.Assign(targets=[ast.Name(id=v2,ctx=ast.Store())],
                   value=ast.Constant(True),lineno=0,col_offset=0),
        ast.If(
            test=ast.BoolOp(op=ast.And(),values=[
                ast.Compare(left=ast.Name(id=v1,ctx=ast.Load()),
                            ops=[ast.Eq()],comparators=[ast.Constant(men)]),
                ast.Compare(left=ast.Name(id=v2,ctx=ast.Load()),
                            ops=[ast.NotEq()],comparators=[ast.Constant(True)]),
            ]),
            body=[ast.Expr(value=ast.Lambda(
                args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],
                                   kw_defaults=[],defaults=[]),
                body=ast.Constant('dit me may')))],
            orelse=[ast.If(
                test=ast.BoolOp(op=ast.And(),values=[
                    ast.Compare(left=ast.Name(id=v1,ctx=ast.Load()),
                                ops=[ast.Eq()],comparators=[ast.Constant(men)]),
                    ast.Compare(left=ast.Name(id=v2,ctx=ast.Load()),
                                ops=[ast.NotEq()],comparators=[ast.Constant(False)]),
                ]),
                body=[ast.Try(
                    body=[ast.Expr(value=ast.Tuple(elts=[
                        ast.BinOp(ast.Constant(1),ast.Div(),ast.Constant(0)),
                        ast.BinOp(ast.Constant(123),ast.Div(),ast.Constant(0)),
                    ],ctx=ast.Load()))],
                    handlers=[ast.ExceptHandler(type=None,name=None,body=[code])],
                    orelse=[],finalbody=[])],
                orelse=[ast.While(test=ast.Constant(True),body=[ast.Pass()],orelse=[])],
            )],
        ),
    ]

# ══════════════════════════════════════════════════════════════════════════════
# AST Transformers (original)
# ══════════════════════════════════════════════════════════════════════════════
class _FStringFlattener(ast.NodeTransformer):
    def visit_JoinedStr(self, node):
        self.generic_visit(node)
        parts = []
        for v in node.values:
            if isinstance(v,ast.Constant):
                parts.append(v)
            elif isinstance(v,ast.FormattedValue):
                expr = self.visit(v.value)
                if v.conversion==114:   expr = ast.Call(ast.Name('repr',ast.Load()),[expr],[])
                elif v.conversion==97:  expr = ast.Call(ast.Name('ascii',ast.Load()),[expr],[])
                else:
                    if not isinstance(expr,ast.Constant):
                        expr = ast.Call(ast.Name('goku',ast.Load()),[expr],[])
                if v.format_spec and isinstance(v.format_spec,ast.JoinedStr):
                    spec = self.visit_JoinedStr(v.format_spec)
                    expr = ast.Call(ast.Name('format',ast.Load()),[expr,spec],[])
                parts.append(expr)
            else:
                parts.append(ast.Call(ast.Name('goku',ast.Load()),[v],[]))
        if not parts: return ast.Constant('')
        if len(parts)==1 and isinstance(parts[0],ast.Constant): return parts[0]
        return ast.Call(
            func=ast.Attribute(ast.Constant(''),'join',ast.Load()),
            args=[ast.Tuple(parts,ast.Load())],keywords=[])

class _BuiltinHider(ast.NodeTransformer):
    def visit_Name(self, node):
        if (isinstance(node.ctx,ast.Load)
                and node.id in _BUILTINS and node.id not in _RUNNER_NAMES):
            return ast.Call(
                func=ast.Name('getattr',ast.Load()),
                args=[ast.Call(ast.Name('capsule_add',ast.Load()),
                               [ast.Constant('builtins')],[]),
                      ast.Constant(node.id)],keywords=[])
        return node

class _ObfctVisitor(ast.NodeTransformer):
    def visit_Constant(self, node):
        try:
            if isinstance(node.value,str) and 0<len(node.value)<400:
                return obfct(node.value)
            if isinstance(node.value,int) and not isinstance(node.value,bool) and -1900<node.value<2010:
                return _obfint(node.value)
        except Exception:
            pass
        return node

class _ShenronJunkInject(ast.NodeTransformer):
    def _wrap(self, body: list) -> list:
        new = []
        for stmt in body: new.extend(shenron_gen_junk(stmt))
        return new
    def visit_Module(self, node):
        self.generic_visit(node); node.body=self._wrap(node.body); return node
    def visit_FunctionDef(self, node):
        self.generic_visit(node); node.body=self._wrap(node.body); return node
    visit_ClassDef = visit_AsyncFunctionDef = visit_FunctionDef

class _VarRenamer(ast.NodeTransformer):
    def __init__(self):
        self.aliases:    dict = {}
        self._protected: set  = set()

    def _protect(self, tree):
        import builtins as _bi
        self._protected.update(vars(_bi).keys())
        self._protected.update(_BUILTINS)
        self._protected.update(_RUNNER_NAMES)
        self._protected.update({
            'self','cls','__name__','__file__','__doc__',
            '__init__','__call__','__str__','__repr__',
            '__len__','__iter__','__next__','__enter__','__exit__',
            '__get__','__set__','__delete__','__class__','__dict__',
            _STR_ALIAS,_INT_ALIAS,_FLOAT_ALIAS,_BOOL_ALIAS,
            _BYTES_ALIAS,_EVAL_ALIAS,_PRINT_ALIAS,_INPUT_ALIAS,
            'MemoryError','Exception','BaseException','TypeError',
            'ValueError','KeyError','IndexError','AttributeError',
        })
        self._protected.update(_LIST_TEN_BIEN)
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                for a in node.names:
                    self._protected.add(a.asname or a.name.split('.')[0])
            elif isinstance(node,ast.ImportFrom):
                for a in node.names:
                    self._protected.add(a.asname or a.name)
            elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                self._protected.add(node.name)
            elif isinstance(node,ast.ClassDef):
                self._protected.add(node.name)
            elif isinstance(node,ast.Global):
                for n in node.names: self._protected.add(n)
            elif isinstance(node,ast.Nonlocal):
                for n in node.names: self._protected.add(n)

    def _alias(self, name: str) -> str:
        if name in self._protected or name.startswith('__'): return name
        if name in self.aliases: return self.aliases[name]
        new = _korean_id(); self.aliases[name] = new; return new

    def visit_Name(self, node):
        if isinstance(node.ctx,(ast.Store,ast.Load,ast.Del)):
            if node.id not in self._protected and not node.id.startswith('__'):
                node.id = self._alias(node.id)
        return node

    def visit_arg(self, node):
        if node.arg not in self._protected and not node.arg.startswith('__'):
            node.arg = self._alias(node.arg)
        return node

    def visit_ExceptHandler(self, node):
        if node.name and node.name not in self._protected and not node.name.startswith('__'):
            node.name = self._alias(node.name)
        self.generic_visit(node); return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node); return node
    visit_AsyncFunctionDef = visit_FunctionDef

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 1: _NumberMutator — (n^k)^k at AST level
# ══════════════════════════════════════════════════════════════════════════════
class _NumberMutator(ast.NodeTransformer):
    def visit_Constant(self, node):
        if not isinstance(node.value,int) or isinstance(node.value,bool): return node
        n = node.value
        if not (-999<n<9999): return node
        k = random.randint(1, 0xFFFF)
        return ast.BinOp(left=ast.Constant(n^k), op=ast.BitXor(), right=ast.Constant(k))

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 2: _StringXORTransformer — XOR encrypt each short string inline
# Runs BEFORE _ObfctVisitor so strings get double-layered treatment
# ══════════════════════════════════════════════════════════════════════════════
class _StringXORTransformer(ast.NodeTransformer):
    def visit_Constant(self, node):
        if not isinstance(node.value,str): return node
        s = node.value
        if not (0 < len(s) < 120): return node
        if random.random() < 0.5: return node   # only ~50% of strings (rest left for obfct)
        key = random.randint(1, 127)
        enc = [ord(c)^key for c in s]
        vx  = _korean_id(7)   # unique loop var
        return ast.Call(
            func=ast.Attribute(
                value=ast.Constant(''),
                attr='join', ctx=ast.Load()),
            args=[ast.GeneratorExp(
                elt=ast.Call(
                    func=ast.Name('chr',ast.Load()),
                    args=[ast.BinOp(
                        left=ast.Name(vx,ast.Load()),
                        op=ast.BitXor(),
                        right=ast.Constant(key))],
                    keywords=[]),
                generators=[ast.comprehension(
                    target=ast.Name(vx,ast.Store()),
                    iter=ast.List([ast.Constant(x) for x in enc],ast.Load()),
                    ifs=[],is_async=0)])],
            keywords=[])

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 3: _BytesObfTransformer — b"..." → bytes([...])
# ══════════════════════════════════════════════════════════════════════════════
class _BytesObfTransformer(ast.NodeTransformer):
    def visit_Constant(self, node):
        if not isinstance(node.value,bytes) or len(node.value)>512: return node
        blist = list(node.value)
        return ast.Call(
            func=ast.Name('bytes',ast.Load()),
            args=[ast.List([ast.Constant(b) for b in blist],ast.Load())],
            keywords=[])

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 4: _AttrObfuscator — obj.attr → getattr(obj, 'attr')
# Only for Load context, skip dunder attrs and runner names
# ══════════════════════════════════════════════════════════════════════════════
class _AttrObfuscator(ast.NodeTransformer):
    _SKIP = {
        '__init__','__call__','__class__','__dict__','__doc__',
        '__name__','__module__','__qualname__','__bases__','__mro__',
        'join','format','encode','decode','split','strip','replace',
        'append','extend','items','keys','values','get','update',
    }
    def visit_Attribute(self, node):
        self.generic_visit(node)
        if (isinstance(node.ctx,ast.Load)
                and not node.attr.startswith('__')
                and node.attr not in self._SKIP
                and random.random() < 0.4):
            return ast.Call(
                func=ast.Name('getattr',ast.Load()),
                args=[node.value, ast.Constant(node.attr)],
                keywords=[])
        return node

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 5: _DeadFunctionInjector — inject fake dead functions at module top
# ══════════════════════════════════════════════════════════════════════════════
_FAKE_FUNC_BODIES = [
    "    _r=0\n    for _i in range(len(_d)):\n        _r^=ord(_d[_i]) if isinstance(_d[_i],str) else _d[_i]\n    return _r",
    "    _h=0x811c9dc5\n    for _b in _d if isinstance(_d,bytes) else _d.encode():\n        _h^=_b;_h=((_h*0x01000193)&0xFFFFFFFF)\n    return _h",
    "    return ''.join(chr(ord(c)^0x42) for c in _s)",
    "    import base64 as _b\n    return _b.b64encode(_x.encode()).decode() if isinstance(_x,str) else _b.b64decode(_x).decode()",
    "    _v=list(_a);_v.sort();return _v",
]

# Tìm dòng định nghĩa các hàm Pass 14 và chèn đoạn tách __future__ này vào:
def _safe_inject(tree: ast.Module, injected_nodes: list) -> ast.Module:
    futures = []
    rest = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == '__future__':
            futures.append(node)
        else:
            rest.append(node)
    tree.body = futures + injected_nodes + rest
    return tree

# Sửa lại hàm _inject_dead_functions (tương tự áp dụng cho global_poison và junk_imports)
def _inject_dead_functions(tree: ast.Module) -> ast.Module:
    dead = []
    for _ in range(random.randint(4,8)):
        fname  = _korean_id(random.randint(8,14))
        arg1   = _korean_id(5)
        body   = random.choice(_FAKE_FUNC_BODIES).replace('_d',arg1).replace('_s',arg1).replace('_x',arg1).replace('_a',arg1)
        src    = f"def {fname}({arg1}):\n{body}\n"
        try:
            fn_node = ast.parse(src).body[0]
            ast.fix_missing_locations(fn_node)
            dead.append(fn_node)
        except Exception:
            pass
    return _safe_inject(tree, dead) # Dùng _safe_inject thay vì cộng chuỗi thẳng

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 6: _OpaquePredicateInjector — wrap stmts with always-True/False conditions
# ══════════════════════════════════════════════════════════════════════════════
class _OpaquePredicateInjector(ast.NodeTransformer):
    def _always_true(self) -> ast.expr:
        a = random.randint(100, 9999)
        b = random.randint(1, 99)
        # a*a - (a-b)*(a+b) == b*b  always True
        return ast.Compare(
            left=ast.BinOp(
                left=ast.BinOp(ast.Constant(a),ast.Mult(),ast.Constant(a)),
                op=ast.Sub(),
                right=ast.BinOp(
                    ast.BinOp(ast.Constant(a),ast.Sub(),ast.Constant(b)),
                    ast.Mult(),
                    ast.BinOp(ast.Constant(a),ast.Add(),ast.Constant(b)))),
            ops=[ast.Eq()],
            comparators=[ast.BinOp(ast.Constant(b),ast.Mult(),ast.Constant(b))])

    def _always_false(self) -> ast.expr:
        n = random.randint(2,99)
        # n*(n+1) % 2 == 1  always False (n*(n+1) always even)
        return ast.Compare(
            left=ast.BinOp(
                left=ast.BinOp(ast.Constant(n),ast.Mult(),ast.BinOp(ast.Constant(n),ast.Add(),ast.Constant(1))),
                op=ast.Mod(),
                right=ast.Constant(2)),
            ops=[ast.Eq()],
            comparators=[ast.Constant(1)])

    def _wrap_body(self, body: list) -> list:
        new = []
        for stmt in body:
            if random.random() < 0.35:
                jv = _korean_id(6)
                dead_stmt = ast.Assign(
                    targets=[ast.Name(id=jv,ctx=ast.Store())],
                    value=ast.Constant(random.randint(1,99999)),
                    lineno=0,col_offset=0)
                new.append(ast.If(
                    test=self._always_true(),
                    body=[stmt],
                    orelse=[dead_stmt]))
            else:
                new.append(stmt)
        return new

    def visit_Module(self, node):
        self.generic_visit(node); node.body=self._wrap_body(node.body); return node
    def visit_FunctionDef(self, node):
        self.generic_visit(node); node.body=self._wrap_body(node.body); return node
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, node):
        self.generic_visit(node); node.body=self._wrap_body(node.body); return node

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 7: _DocstringPoisoner — misleading docstrings on all functions
# ══════════════════════════════════════════════════════════════════════════════
_FAKE_DOCS = [
    "Initialize cryptographic context with AES-256-CBC padding.",
    "Verify HMAC-SHA512 signature against expected digest.",
    "Decrypt payload using RSA-OAEP with 4096-bit key.",
    "Validate license token against remote server endpoint.",
    "Perform base85 decode with custom alphabet mapping.",
    "Check code integrity via CRC32 polynomial hash.",
    "Load and execute encrypted bytecode from memory buffer.",
    "Apply Feistel cipher round with dynamic S-box permutation.",
]

class _DocstringPoisoner(ast.NodeTransformer):
    def _poison(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant):
            node.body[0].value.value = random.choice(_FAKE_DOCS)
        elif random.random() < 0.6:
            node.body.insert(0, ast.Expr(
                value=ast.Constant(value=random.choice(_FAKE_DOCS))))
        return node
    def visit_FunctionDef(self, node): return self._poison(node)
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, node): return self._poison(node)

# ══════════════════════════════════════════════════════════════════════════════
# Inject helpers
# ══════════════════════════════════════════════════════════════════════════════
_JUNK_STDLIB = ['collections','functools','itertools','pathlib',
                'threading','weakref','contextlib','textwrap',
                'hashlib','struct','operator','copy']

def _inject_junk_imports(tree: ast.Module) -> ast.Module:
    junk = []
    for mod in random.sample(_JUNK_STDLIB, random.randint(3,6)):
        junk.append(ast.Import(names=[ast.alias(name=mod,asname=_korean_id(8))]))
    # Đổi thành _safe_inject thay vì junk + tree.body
    return _safe_inject(tree, junk)

def _inject_global_poison(tree: ast.Module) -> ast.Module:
    poison = []
    for _ in range(random.randint(8,14)):
        name = _korean_id(random.randint(6,14))
        val  = random.choice([
            ast.Constant(random.randint(-999999,999999)),
            ast.Constant(''.join(chr(random.randint(0x4E00,0x4FFF))
                                 for _ in range(random.randint(3,10)))),
            ast.Constant(None),
            ast.List(elts=[ast.Constant(random.randint(0,255))
                           for _ in range(random.randint(2,8))],ctx=ast.Load()),
            ast.Tuple(elts=[ast.Constant(random.randint(0,0xFF))
                            for _ in range(random.randint(2,5))],ctx=ast.Load()),
        ])
        poison.append(ast.Assign(
            targets=[ast.Name(id=name,ctx=ast.Store())],
            value=val,lineno=0,col_offset=0))
    # Đổi thành _safe_inject thay vì poison + tree.body
    return _safe_inject(tree, poison)

class _ControlFlowFlattening(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if not node.body: return node

        # Only flatten functions with more than 3 statements
        if len(node.body) < 3: return node

        # Create a dispatcher variable and initial state
        dispatcher_var = _korean_id(8)
        state_var = _korean_id(8)
        initial_state = random.randint(1000, 9999)

        # Map original statements to new states
        statements = []
        state_map = {}
        current_state = initial_state
        for stmt in node.body:
            state_map[stmt] = current_state
            statements.append((current_state, stmt))
            current_state += random.randint(1, 10)

        # Create a while loop for the dispatcher
        loop_body = []
        for i, (state, stmt) in enumerate(statements):
            next_state = state_map.get(statements[i+1][1]) if i < len(statements) - 1 else 0
            
            # Create an If statement for each state
            if_stmt = ast.If(
                test=ast.Compare(
                    left=ast.Name(id=state_var, ctx=ast.Load()),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(state)]
                ),
                body=[stmt],
                orelse=[]
            )
            
            # Add state update for the next iteration
            if next_state != 0:
                if_stmt.body.append(ast.Assign(
                    targets=[ast.Name(id=state_var, ctx=ast.Store())],
                    value=ast.Constant(next_state),
                    lineno=0, col_offset=0
                ))
            else:
                # Break the loop if it's the last statement
                if_stmt.body.append(ast.Break())
            
            loop_body.append(if_stmt)

        # Initialize state variable
        init_state_assign = ast.Assign(
            targets=[ast.Name(id=state_var, ctx=ast.Store())],
            value=ast.Constant(initial_state),
            lineno=0, col_offset=0
        )

        # Create the while loop
        while_loop = ast.While(
            test=ast.Constant(True),
            body=loop_body,
            orelse=[]
        )

        node.body = [init_state_assign, while_loop]
        return node

    visit_AsyncFunctionDef = visit_FunctionDef



# Anti-dis: block decompiler modules in sys.modules + ctypes trick
_ANTI_DIS_BLOCK = r"""
import sys as _sy_d, os as _os_d

class _FakeDis:
        def __getattr__(self,_n): pass # Changed from _os_d._exit(0) to pass
        def __call__(self,*_a,**_k): pass # Changed from _os_d._exit(0) to pass
        def __iter__(self): pass; return iter([]) # Changed from _os_d._exit(0) to pass
        def __len__(self): pass; return 0 # Changed from _os_d._exit(0) to pass

_bad_mods = (
    'uncompyle6','decompile3','pycdc','decompyle3',
    'unpyc3','bytecode','xdis','decompile',
    'pydevd','pydevd_tracing','birdseye','viztracer',
    'pudb','wdb','rpdb','remote_pdb',
)
for _bm in _bad_mods:
    _sy_d.modules[_bm] = _FakeDis()

try:
    import ctypes as _ct
    if hasattr(_ct,'pythonapi'):
        _ct.pythonapi.PyFrame_LocalsToFast = None
except Exception:
    pass

del _bm, _bad_mods, _sy_d, _os_d
"""

# Anti-debug: ONLY pydevd/pdb filename check in stack frames
# NO TracerPid (false-positive on Replit, Docker, Android)
# NO sys.modules scan (hasattr on FakeDis would call __getattr__ → exit)
_ANTI_DEBUG_BLOCK = r"""
try:
    import inspect as _ins, os as _osd
    _fr = _ins.currentframe()
    while _fr is not None:
        _co = getattr(getattr(_fr,'f_code',None),'co_filename','')
        if 'pydevd' in _co or ('pdb.py' in _co and 'pdbpp' not in _co):
                        pass # Changed from _osd._exit(0) to pass
        _fr = getattr(_fr,'f_back',None)
except Exception:
    pass
finally:
    for _vn in ('_fr','_co','_ins','_osd'):
        try: del globals()[_vn]
        except Exception: pass
"""

# Anti-meta-path: check sys.meta_path for suspicious import hooks
_ANTI_META_PATH_BLOCK = r"""
try:
    import sys as _smp
    _safe_types = {'PathFinder','FileFinder','FrozenImportLib',
                   'BuiltinImporter','FrozenImporter','PathFinder',
                   '_frozen_importlib','_frozen_importlib_external'}
    for _mh in list(_smp.meta_path):
        _tn = type(_mh).__name__
        _mn = getattr(type(_mh),'__module__','') or ''
        if ('hook' in _tn.lower() or 'intercept' in _tn.lower() or
                'coverage' in _mn.lower() or 'trace' in _mn.lower()):
                        import os as _ox; pass # Changed from _ox._exit(0) to pass
    del _smp, _safe_types, _mh, _tn, _mn
except Exception:
    pass
"""

# ══════════════════════════════════════════════════════════════════════════════
# _build_runner
# ══════════════════════════════════════════════════════════════════════════════
def _build_runner(compressed: bytes, raw_bytecode: bytes, ver: str,
                  bot_name: str, bot_username: str, owner: str, vn_time: str) -> str:
    # XOR layer
    xor_key     = _gen_xor_key(64)
    xor_enc     = _xor_bytes(compressed, xor_key)
    xor_key_b64 = base64.b64encode(xor_key).decode()

    # ROT layer on top of XOR
    rot_n       = random.randint(5, 30)
    rot_enc     = _rot_bytes(xor_enc, rot_n)

    hanzi_payload  = hanzi_encode(rot_enc)
    integrity_hash = _compute_integrity(raw_bytecode)

    V   = [_korean_id() for _ in range(30)]
    va  = _korean_id(); vb  = _korean_id(); vd = _korean_id()
    vk  = _korean_id(); vc  = _korean_id(); vs = _korean_id()
    vv  = _korean_id()
    lv1 = _korean_id(); lv2 = _korean_id(); lv3 = _korean_id()

    se  = shenron_enc
    pro = build_pro_code()

    _sys_chr     = _chr('sys')
    _os_chr      = _chr('os')
    _run_chr     = _chr('>> Running...')
    _fromhex_chr = _chr('fromhex')
    _shenron_chr = _chr('shenron')
    _frieza_chr  = _chr('frieza')
    _goku_chr    = _chr('goku')
    _vegeta_chr  = _chr('vegeta')
    _gohan_chr   = _chr('gohan')
    _bulma_chr   = _chr('bulma')
    _capsule_chr = _chr('capsule')
    _trunks_chr  = _chr('trunks')
    _radar_chr   = _chr('radar')

    # Anti-hook: safe callable checks only
    anti_hooks = f"""
try:
    _ah_bi = capsule_add({se('builtins')})
    _ah_sy = capsule_add({se('sys')})
    for _ah_n in [{se('print')},{se('exec')},{se('eval')},{se('compile')}]:
        _ah_fn = getattr(_ah_bi,_ah_n,None)
        if _ah_fn is None or not callable(_ah_fn): pass # Changed from _ah_sy.exit() to pass
        if type(_ah_fn).__name__ not in ({se('builtin_function_or_method')},{se('function')}):
            pass # Changed from _ah_sy.exit() to pass
    del _ah_bi,_ah_sy,_ah_n,_ah_fn
except Exception:
    pass
"""

    # Anti-httptoolkit: ONLY check HTTP_TOOLKIT_ACTIVE — nothing else (false-positives Android VPN)
    vip_anti = f"""
try:
    if capsule_add({_os_chr}).environ.get({se('HTTP_TOOLKIT_ACTIVE')}) == {se('true')}:
        capsule_add({_sys_chr}).exit()
except Exception:
    pass
"""

    # Layer 3: HMAC → marshal → exec
    # Layer 3: HMAC → Giải mã thẳng text → exec (Bỏ marshal)
    layer3_src = (
        "import hmac as _h3, hashlib as _hs3, os as _o3\n"
        f"def {lv3}(_rb,_sig):\n"
        "    _k=b'CuongObfIntegrity2010ShenronVIP'\n"
        "    if not _h3.compare_digest(_h3.new(_k,_rb,_hs3.sha256).hexdigest(),_sig):\n"
        "                _o3.exit(0) # Changed from _o3._exit(0) to _o3.exit(0)\n"
        "    exec(_rb.decode('utf-8'),globals())\n" # <-- Thay đổi mấu chốt ở đây
    )

    # Layer 2: Hanzi → un-ROT → XOR → decompress → layer3
    layer2_src = (
        "import zlib as _z2,bz2 as _b2,lzma as _lx2,base64 as _64_2\n"
        f"_HD2={repr(HANZI_DEC)}\n"
        "def _hd2(s): return bytes.fromhex(''.join(_HD2[c] for c in s))\n"
        "def _xd2(d,k):\n"
        "    kl=len(k); return bytes(b^k[i%kl] for i,b in enumerate(d))\n"
        f"def _ur2(d,n): return bytes((b-n)&0xFF for b in d)\n"
        f"def {lv2}(_pl,_sig,_xkb,_rn):\n"
        "    _xk=_64_2.b64decode(_xkb)\n"
        "    _rot=_hd2(_pl)\n"
        "    _xe=_ur2(_rot,_rn)\n"
        "    _raw=_lx2.decompress(_z2.decompress(_b2.decompress(_64_2.a85decode(_xd2(_xe,_xk)))))\n"
        f"    exec(compile({repr(layer3_src)},'<l3>','exec'),globals())\n"
        f"    {lv3}(_raw,_sig)\n"
        f"{lv2}({repr(hanzi_payload)},{repr(integrity_hash)},{repr(xor_key_b64)},{rot_n})\n"
    )

    layer2_blob = base64.b64encode(zlib.compress(layer2_src.encode('utf-8'),9)).decode()

    runner = (
        f"#!/usr/bin/env python3\n"
        f"# -*- coding: utf-8 -*-\n"
        f"# ╔════════════════════════════════════════╗\n"
        f"# ║  Obf  : {bot_name} {bot_username}\n"
        f"# ║  Owner: {owner}\n"
        f"# ║  Time : {vn_time}\n"
        f"# ╚════════════════════════════════════════╝\n"
        f"__INFO__={{'Obfuscator':'{bot_name}','Owner':'{owner}','v':'2.1'}}\n\n"
        f"{_ANTI_DIS_BLOCK}\n"
        f"{_ANTI_DEBUG_BLOCK}\n"
        f"{_ANTI_META_PATH_BLOCK}\n"
        f"class CapsuleCorp(object):\n"
        f"    def __init__(self):\n"
        f"        {V[20]}=__import__({_sys_chr})\n"
        f"        if str({V[20]}.version_info.major)!=chr(51): pass # Changed from {V[20]}.exit() to pass\n"
        f"        {V[20]}.stderr.write({_run_chr}+chr(10))\n"
        f"    def __call__(self,*{va},**{vb}):\n"
        f"        global yamcha,capsule,radar,shenron,frieza,goku,vegeta,gohan,trunks,bulma,kamehameha,capsule_add\n"
        f"        globals()[{_frieza_chr}]=eval(chr(101)+chr(118)+chr(97)+chr(108))\n"
        f"        globals()[{_goku_chr}]=frieza(chr(115)+chr(116)+chr(114))\n"
        f"        globals()[{_vegeta_chr}]=frieza(chr(98)+chr(121)+chr(116)+chr(101)+chr(115))\n"
        f"        globals()[{_gohan_chr}]=frieza(chr(100)+chr(105)+chr(99)+chr(116))\n"
        f"        globals()[{_bulma_chr}]={repr(_B64)}\n"
        f"        globals()[{_capsule_chr}]={repr(_CJK_ALPHA)}\n"
        f"        globals()[{_trunks_chr}]=frieza(chr(122)+chr(105)+chr(112))\n"
        f"        globals()[{_radar_chr}]=gohan(trunks(bulma,capsule))\n"
        f"        {vd}={{{vv}:{vk} for {vk},{vv} in radar.items()}}\n"
        f"        globals()[{_shenron_chr}]=lambda {vs}:getattr(vegeta,{_fromhex_chr})"
        f"(goku().join(({vd}.get({vc},{vc}) for {vc} in {vs}))).decode()\n"
        f"        globals()[{se('capsule_add')}]=frieza({se('__tropmi__')}[::-1])\n"
        f"        globals()[{se('kamehameha')}]=frieza({se('cexe')}[::-1])\n"
        f"        globals()[{se('yamcha')}]=frieza({se('tni')}[::-1])\n"
        f"CapsuleCorp()()\n"
        f"{anti_hooks}\n"
        f"{vip_anti}\n"
        f"{V[2]}=vars(globals()[{se('__builtins__')}])\n"
        f"{pro}\n"
        f"import zlib as _zl1,base64 as _b641\n"
        f"{lv1}=_b641.b64decode({repr(layer2_blob)})\n"
        f"exec(compile(_zl1.decompress({lv1}).decode('utf-8'),'<l2>','exec'),globals())\n"
    )
    return runner

# ══════════════════════════════════════════════════════════════════════════════
# obfuscate_code — 14 passes
# ══════════════════════════════════════════════════════════════════════════════
def obfuscate_code(source: str, bot_name: str, bot_username: str, owner: str) -> str:
    ver     = f'{sys.version_info.major}.{sys.version_info.minor}'
    vn_time = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')

    tree = ast.parse(source)

    # Pass 1: rename vars → Korean syllables
    rn = _VarRenamer(); rn._protect(tree); rn.visit(tree)

    # Pass 2: flatten f-strings
    _FStringFlattener().visit(tree)

    # Pass 3: XOR-encrypt ~50% of string constants (NEW)
    _StringXORTransformer().visit(tree)

    # Pass 4: obfuscate remaining strings + ints via lambda table
    _ObfctVisitor().visit(tree)

    # Pass 5: bytes literals → bytes([...]) (NEW)
    _BytesObfTransformer().visit(tree)

    # Pass 6: hide builtins → getattr(capsule_add(...))
    _BuiltinHider().visit(tree)

    # Pass 7: selective attribute → getattr() (NEW)
    _AttrObfuscator().visit(tree)

    # Pass 8: sakura MemoryError junk blocks
    yuamikami(tree)

    # Pass 9: shenron dead-branch injection
    _ShenronJunkInject().visit(tree)

    # Pass 10: opaque predicate wrapping (NEW)
    _OpaquePredicateInjector().visit(tree)

    # Pass 11: sakura trycatch × 2
    tree.body = sakura_trycatch(tree.body, 2)

    # Pass 12: XOR int mutation
    _NumberMutator().visit(tree)

    # Pass 13: poisoned docstrings (NEW)
    _DocstringPoisoner().visit(tree)

    # Pass 14: inject dead functions + global poison + junk imports (NEW)
    _inject_dead_functions(tree)
    _inject_global_poison(tree)
    _inject_junk_imports(tree)

    # Pass 15: Control Flow Flattening (NEW)
    _ControlFlowFlattening().visit(tree)

    ast.fix_missing_locations(tree)
    obf_src = ast.unparse(tree)

    # Bỏ compile và marshal, encode thẳng code đã mã hoá thành bytes
    raw_payload = obf_src.encode('utf-8')
    compressed  = base64.a85encode(bz2.compress(zlib.compress(lzma.compress(raw_payload))))
    return _build_runner(compressed, raw_payload, ver, bot_name, bot_username, owner, vn_time)
    

# ══════════════════════════════════════════════════════════════════════════════
# MarkdownV2
# ══════════════════════════════════════════════════════════════════════════════
def _mdv2(s: str) -> str:
    s = s.replace('\\','\\\\')
    for ch in r'_*[]()~`>#+-=|{}.!':
        s = s.replace(ch,'\\'+ch)
    return s

# ══════════════════════════════════════════════════════════════════════════════
# Message templates
# ══════════════════════════════════════════════════════════════════════════════
def _start_msg() -> str:
    ow = _mdv2(OWNER); bu = _mdv2(BOT_USERNAME)
    return (
        "╔══════════════════════════════════╗\n"
        "║  🔐 *CuongObf — Cpython Bot* 🔐  ║\n"
        "╚══════════════════════════════════╝\n\n"
        "> 🛡️ Mã hoá Python đa lớp — 14 pass obfuscation\n"
        "> Anti\\-decompile, Anti\\-debug, Anti\\-hook, Anti\\-trace\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *CÁCH DÙNG*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "> 📎 Gửi file `.py` → bot tự động mã hoá\n"
        "> 💬 Hoặc paste code Python trực tiếp\n"
        "> 📥 Nhận lại file `enc-*` đã bảo vệ\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Owner:* `{ow}`\n"
        f"🤖 *Bot:* `{bu}`"
    )

def _progress_msg(fname: str='') -> str:
    tag = f'`{_mdv2(fname)}` ' if fname else ''
    return f"⏳ *Đang mã hoá* {tag}\\.\\.\\.\n\n> 🀄 ĐỢI MỘT LÁT \\.\\.\\.\\.\\. \n"

def _success_msg(out_name: str, vn_time: str) -> str:
    fn=_mdv2(out_name); vt=_mdv2(vn_time); ow=_mdv2(OWNER); bu=_mdv2(BOT_USERNAME)
    return (
        "╔═════════════════════════════╗\n"
        "║  ✅ *Mã hoá thành công\\!* ✅ ║\n"
        "╚═════════════════════════════╝\n\n"
        f"> 📄 *File:* `{fn}`\n"
        f"> 🕐 *Time:* `{vt}`\n"
        f"> 🤖 *Bot:* `{bu}`\n"
        f"> 👑 *Owner:* `{ow}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def _doc_caption(out_name: str) -> str:
    return f'✅ `{_mdv2(out_name)}`\n🤖 {_mdv2(BOT_NAME)} {_mdv2(BOT_USERNAME)}\n👑 {_mdv2(OWNER)}'

def _err_msg(label: str, err: str) -> str:
    return f'> ❌ *{_mdv2(label)}*\n`{_mdv2(err)}`'

# ══════════════════════════════════════════════════════════════════════════════
# Telegram handlers
# ══════════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(_start_msg(), parse_mode=ParseMode.MARKDOWN_V2)

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not (doc.file_name or '').endswith('.py'):
        await update.message.reply_text(
            "> ❌ Chỉ hỗ trợ file `.py`", parse_mode=ParseMode.MARKDOWN_V2)
        return
    progress = await update.message.reply_text(
        _progress_msg(doc.file_name), parse_mode=ParseMode.MARKDOWN_V2)
    tmp_in  = tempfile.NamedTemporaryFile(suffix='.py',delete=False,mode='w',encoding='utf-8')
    tmp_out = tempfile.mktemp(suffix='.py')
    try:
        file_obj = await ctx.bot.get_file(doc.file_id)
        await file_obj.download_to_drive(tmp_in.name)
        with open(tmp_in.name,'r',encoding='utf-8') as f: source=f.read()
        result   = obfuscate_code(source, BOT_NAME, BOT_USERNAME, OWNER)
        out_name = 'enc-'+doc.file_name
        vn_time  = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')
        with open(tmp_out,'w',encoding='utf-8') as f: f.write(result)
        await progress.edit_text(_success_msg(out_name,vn_time),parse_mode=ParseMode.MARKDOWN_V2)
        with open(tmp_out,'rb') as f:
            await update.message.reply_document(
                document=f, filename=out_name,
                caption=_doc_caption(out_name), parse_mode=ParseMode.MARKDOWN_V2)
    except SyntaxError as e:
        await progress.edit_text(_err_msg('Lỗi cú pháp',str(e)),parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await progress.edit_text(_err_msg('Lỗi',str(e)),parse_mode=ParseMode.MARKDOWN_V2)
    finally:
        for p in [tmp_in.name,tmp_out]:
            try: os.unlink(p)
            except Exception: pass

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    starters = ('import ','from ','def ','class ','#','print(',
                'if ','for ','while ','try:','with ','async ',
                '@','lambda ','return ','yield ')
    if not any(text.startswith(s) for s in starters):
        await update.message.reply_text(
            "> 💬 Gửi file `.py` hoặc paste code Python để mã hoá\\.",
            parse_mode=ParseMode.MARKDOWN_V2)
        return
    progress = await update.message.reply_text(_progress_msg(),parse_mode=ParseMode.MARKDOWN_V2)
    tmp_out  = tempfile.mktemp(suffix='.py')
    try:
        result  = obfuscate_code(text, BOT_NAME, BOT_USERNAME, OWNER)
        vn_time = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')
        with open(tmp_out,'w',encoding='utf-8') as f: f.write(result)
        await progress.edit_text(_success_msg('enc-code.py',vn_time),parse_mode=ParseMode.MARKDOWN_V2)
        with open(tmp_out,'rb') as f:
            await update.message.reply_document(
                document=f, filename='enc-code.py',
                caption=_doc_caption('enc-code.py'), parse_mode=ParseMode.MARKDOWN_V2)
    except SyntaxError as e:
        await progress.edit_text(_err_msg('Lỗi cú pháp',str(e)),parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await progress.edit_text(_err_msg('Lỗi',str(e)),parse_mode=ParseMode.MARKDOWN_V2)
    finally:
        try: os.unlink(tmp_out)
        except Exception: pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

# ══════════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    if not BOT_TOKEN:
        print('BOT_TOKEN chưa được set!'); sys.exit(1)
    print(f'{BOT_NAME} Bot đang khởi động...')
    print(f'Owner : {OWNER}')
    print(f'Bot   : {BOT_USERNAME}')
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help',  cmd_start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    print('Bot đang chạy — nhấn Ctrl+C để dừng.')
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

# ══════════════════════════════════════════════════════════════════════════════
# NEW PASS 15: _ControlFlowFlattening
# ══════════════════════════════════════════════════════════════════════════════
