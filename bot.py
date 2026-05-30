#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, ast, zlib, bz2, lzma, base64, marshal, random, tempfile, hashlib, logging
import hmac as _hmac_module
from datetime import datetime

sys.setrecursionlimit(99999999)

# ══════════════════════════════════════════════════════════════════════════════
# Auto-install dependencies
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
# Bot config
# ══════════════════════════════════════════════════════════════════════════════
BOT_TOKEN    = "8397744945:AAGr7WR3viIb0oNl7GML4xSFX0Ygdpc3Wl8"
BOT_NAME     = 'Obf Cpython'
BOT_USERNAME = '@ObfCpythonRobot'
OWNER        = '@truongphuhaokhithaylonquenloi'
VN_TZ        = pytz.timezone('Asia/Ho_Chi_Minh')

# ══════════════════════════════════════════════════════════════════════════════
# Hanzi alphabet (hex → CJK)
# ══════════════════════════════════════════════════════════════════════════════
HANZI_ENC = {
    '0':'阮','1':'黄','2':'国','3':'强',
    '4':'天','5':'地','6':'玄','7':'宇',
    '8':'宙','9':'洪','a':'荒','b':'日',
    'c':'月','d':'盈','e':'昃','f':'辰',
}
HANZI_DEC = {v: k for k, v in HANZI_ENC.items()}

# ══════════════════════════════════════════════════════════════════════════════
# Emoji base-64 alphabet (shenron encoder)
# ══════════════════════════════════════════════════════════════════════════════
_B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
_EMOJI_RAW = [
    '🐉','🐲','⭐','✨','💫','🌠','⚡','🔥','💥','🌀',
    '🥋','🥊','👊','🙌','👐','🟠','🔴','🟡','🟢','🔵',
    '🟣','⚫','⚪','👽','🤖','👺','🐢','🐒','🦍','💎',
    '🔮','🍑','🍗','🍚','🍶','🏯','🤜','🤛','😡','😤',
    '🥵','🤯','🌌','🌍','🌑','🎯','🎲','🎭','🎪','🎨',
    '🎬','🎤','🎧','🎸','🎹','🎺','🎻','🥁','🎮','🎠',
    '🎡','🎢','🏆','🥇',
]
_EMOJI_POOL = [e for e in _EMOJI_RAW if len(e) == 1]
_EMOJI_SUPPLEMENT = [
    chr(i) for i in range(0x2600, 0x26FF)
    if len(chr(i)) == 1 and chr(i).isprintable()
]
_seen_e: set = set()
_EMOJI_LIST: list = []
for _ch in _EMOJI_POOL + _EMOJI_SUPPLEMENT:
    if _ch not in _seen_e and len(_EMOJI_LIST) < 64:
        _seen_e.add(_ch)
        _EMOJI_LIST.append(_ch)
_EMOJI_ALPHA = ''.join(_EMOJI_LIST[:64])

_E2B = dict(zip(_B64, _EMOJI_ALPHA))
_B2E = {v: k for k, v in _E2B.items()}

# ══════════════════════════════════════════════════════════════════════════════
# Core encode helpers
# ══════════════════════════════════════════════════════════════════════════════
def hanzi_encode(data: bytes) -> str:
    """Encode bytes → Hanzi string via hex."""
    return ''.join(HANZI_ENC[c] for c in data.hex())


def shenron_enc(s: str) -> str:
    """Encode a plain string as a shenron("…") call expression."""
    mapped = ''.join(_E2B.get(c, c) for c in s.encode().hex())
    return f'shenron("{mapped}")'


def _korean_id(k: int = 11) -> str:
    """Generate a random Korean-syllable identifier."""
    pool = [chr(i) for i in range(44032, 55204)
            if chr(i).isprintable() and chr(i).isidentifier()]
    return ''.join(random.choices(pool, k=k))


def spam_hanzi() -> str:
    hz = '天地玄黄宇宙洪荒日月盈昃辰宿列张'
    return (f'__{random.randint(10**8, 10**10)}'
            f'{"".join(random.choices(hz, k=8))}'
            f'{random.randint(10**8, 10**10)}__')


def obf_gl(s: str) -> str:
    """ROT-10 on alphabetic characters."""
    out = []
    for c in s:
        if c.isalpha():
            base = 65 if c.isupper() else 97
            out.append(chr((ord(c) - base + 10) % 26 + base))
        else:
            out.append(c)
    return ''.join(out)


def _chr(s: str) -> str:
    """Encode a string as chr(n)+chr(n)+… expression."""
    return '+'.join(f'chr({ord(c)})' for c in s)

# ══════════════════════════════════════════════════════════════════════════════
# Alias names injected into obfuscated source
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
    'CuongSieuDepTrai',    'CalceSieuCapVip',       'CuongCodeThuongThua',
    'CalceVoDichTheGioi',  'CuongChuyenGiaPro',     'CalceBacThoDinhCao',
    'CuongCongNgheDinh',   'CalceLapTrinhMaster',   'CuongSangTaoVoSong',
    'CalceVuongGiaCode',   'CuongThuatToanHay',     'CalceHackerPro',
    'CuongThanhCongLon',   'CalceToiThuongDev',     'CuongAnDanhElite',
    'CalceChienThanCode',  'CuongProMaxVIP',         'CalceTruyenKyLapTrinh',
    'CuongMasterMind',     'CalceUltimateDev',       'CuongDevKing',
    'CalceInfinityCode',   'CuongCodeWarrior',       'CalceChampionCoder',
    'CuongCyberHero',      'CalceTheBestDev',        'CuongAIWizard',
    'CalceOverlordCoder',  'CuongEliteHacker',       'CalceDarkMode',
    'CuongQuantumTech',    'CalceGodLike',
]

# ══════════════════════════════════════════════════════════════════════════════
# HMAC-SHA256 integrity
# ══════════════════════════════════════════════════════════════════════════════
_INTEGRITY_KEY = b'CuongObfIntegrity2010ShenronVIP'

def _compute_integrity(payload_bytes: bytes) -> str:
    return _hmac_module.new(
        _INTEGRITY_KEY, payload_bytes, hashlib.sha256
    ).hexdigest()

# ══════════════════════════════════════════════════════════════════════════════
# varsobf — wrap a builtin name in a dead-branch expression
# ══════════════════════════════════════════════════════════════════════════════
def varsobf(v: str) -> str:
    r1 = random.randint(1, 1000)
    r2 = random.randint(101, 20_000_000_000)
    return (
        f"('DitConBaGiaMay') if 2010 < 611 or 611 > 2010 or 12345 > 67890 or "
        f"98765 < 54321 or 'test' == 'false' or 0 == 1 or False == True or "
        f"1 == 2 or 10 > 20 or {r1} > {r2} else {v}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# Pycloak — encode integers / strings as lambda call expressions
# ══════════════════════════════════════════════════════════════════════════════
class Pycloak:
    def encode(self, data):
        if isinstance(data, str):
            return self.barray_encode(data)
        if isinstance(data, int):
            return self.int_encode(data)

    def int_encode(self, num: int) -> str:
        if num == 0:
            return '(lambda: 0)()'
        parts, n = [], num
        while n > 0:
            p = random.randint(1, n)
            parts.append(str(p))
            n -= p
        return f'(lambda: {" + ".join(parts)})()'

    def barray_encode(self, s: str) -> str:
        return 'bytes([{}]).decode("utf-8")'.format(
            ', '.join(self.int_encode(ord(c)) for c in s))

# ══════════════════════════════════════════════════════════════════════════════
# build_pro_code — generates the junk/anti-decompile header injected into runner
# ══════════════════════════════════════════════════════════════════════════════
def build_pro_code() -> str:
    crash_exprs = {
        'Z': '1/0,', 'T': 'len+1,', 'N': 'xyz,',
        'I': '[][99],', 'K': '{}[""],',
        'M': "__import__('xyz'),", 'V': 'int("a",99),',
        'A': '[].__x,',  'F': 'open("ww"),',
    }
    for k in crash_exprs:
        crash_exprs[k] = crash_exprs[k] * 800
    anti_pycdc = '\n'.join(
        f'try:({v})\nexcept:0\n' for v in crash_exprs.values()
    )
    pro = f'\ntry:pass\nexcept:pass\nelse:pass\nfinally:pass\n{anti_pycdc}\n'

    Hehe = [
        f'{_BOOL_ALIAS} = {varsobf("bool")}',
        f'{_STR_ALIAS} = {varsobf("str")}',
        f'{_INT_ALIAS} = {varsobf("int")}',
        f'{_FLOAT_ALIAS} = {varsobf("float")}',
        f'{_BYTES_ALIAS} = {varsobf("bytes")}',
        f'{_EVAL_ALIAS} = {varsobf("eval")}',
        f'{_PRINT_ALIAS} = {varsobf("print")}',
        f'{_INPUT_ALIAS} = {varsobf("input")}',
    ]

    _lambda_body = (
        "lambda concacmemaybeolam, jackbocon, meomeo, bucuanhdi: ("
        "concacmemaybeolam.join("
        "[chr((DIT_ME_MAY - jackbocon) // meomeo) for DIT_ME_MAY in bucuanhdi]"
        ") if concacmemaybeolam not in "
        "[\"DitConBaMay\", \"CuongObfuscate\", \"NGUYENHOANGQUOCCUONG\"]"
        " else (\"\").join("
        "[chr((DIT_ME_MAY - jackbocon) // meomeo) for DIT_ME_MAY in bucuanhdi]))"
    )

    def _rev(name: str) -> str:
        return ''.join([
            chr(((ord(c) - (65 if c.isupper() else 97) - 10) % 26)
                + (65 if c.isupper() else 97))
            if c.isalpha() else c
            for c in obf_gl(name)
        ])

    shuffled = list(_LIST_TEN_BIEN)
    random.shuffle(shuffled)
    for i in shuffled:
        pro += f"globals()['{_rev(i)}'] = {_lambda_body}\n"
        if Hehe:
            hello = random.choice(Hehe)
            pro += hello + '\n'
            Hehe.remove(hello)
        junk_name = 'CuongDitMeMay' + str(random.randint(1000, 9999))
        pro += f"globals()['{_rev(junk_name[:13])}'] = {_lambda_body}\n"
    while Hehe:
        pro += Hehe.pop(0) + '\n'
    return pro

# ══════════════════════════════════════════════════════════════════════════════
# AST helpers
# ══════════════════════════════════════════════════════════════════════════════
_BUILTINS = set(__import__('builtins').__dict__.keys())
_RUNNER_NAMES = {
    'goku', 'capsule_add', 'kamehameha', 'yamcha', 'shenron',
    'frieza', 'vegeta', 'gohan', 'bulma', 'capsule', 'trunks', 'radar',
}

def _mk_args(name: str) -> ast.arguments:
    return ast.arguments(
        posonlyargs=[], args=[ast.arg(arg=name)],
        vararg=None, kwonlyargs=[], kw_defaults=[],
        kwarg=None, defaults=[])


def _obfint(i: int) -> ast.AST:
    """Obfuscate an integer literal via nested lambda + yamcha(int)."""
    ref  = 2010
    diff = ref - i
    v1, v2, v3 = _korean_id(), _korean_id(), _korean_id()
    lam3 = ast.Lambda(_mk_args(v1), ast.Call(
        ast.Name('yamcha', ast.Load()),
        [ast.BinOp(ast.Constant(ref), ast.Sub(), ast.Constant(diff))], []))
    lam2 = ast.Lambda(_mk_args(v2),
                      ast.Call(lam3, [ast.Constant('DitConBaGiaMay')], []))
    lam1 = ast.Lambda(_mk_args(v3),
                      ast.Call(lam2, [ast.Constant('DitConBaGiaMay')], []))
    return ast.Call(lam1, [ast.Constant('DitConBaGiaMay')], [])


def _obfstr(s: str) -> ast.AST:
    """Obfuscate a string literal via chr-list generator + nested lambdas."""
    lst = [ord(c) for c in s]
    v, v1, v2, v3 = _korean_id(), _korean_id(), _korean_id(), _korean_id()
    lam3 = ast.Lambda(_mk_args(v1), ast.Call(
        func=ast.Attribute(
            value=ast.Call(ast.Name('goku', ast.Load()), [], []),
            attr='join', ctx=ast.Load()),
        args=[ast.GeneratorExp(
            elt=ast.Call(ast.Name('chr', ast.Load()),
                         [ast.Name(v, ast.Load())], []),
            generators=[ast.comprehension(
                target=ast.Name(v, ast.Store()),
                iter=ast.List([ast.Constant(x) for x in lst], ast.Load()),
                ifs=[], is_async=0)])],
        keywords=[]))
    lam2 = ast.Lambda(_mk_args(v2),
                      ast.Call(lam3, [ast.Constant('DitConBaGiaMay')], []))
    lam1 = ast.Lambda(_mk_args(v3),
                      ast.Call(lam2, [ast.Constant('DitConBaGiaMay')], []))
    return ast.Call(lam1, [ast.Constant('DitConBaGiaMay')], [])


def obfct(string: str) -> ast.AST:
    """Encode a string constant via the lambda-table (_LIST_TEN_BIEN) approach."""
    if string == '':
        return ast.Constant(value='')
    dep_trai = random.choice(_LIST_TEN_BIEN)
    encoded  = [ord(c) * 611 + 2010 for c in string]
    return ast.parse(
        f"{_STR_ALIAS}((lambda: {dep_trai}"
        f"('NGUYENHOANGQUOCCUONG', 2009, 611, {encoded}))())"
    ).body[0].value

# ══════════════════════════════════════════════════════════════════════════════
# Sakura junk-injection helpers
# ══════════════════════════════════════════════════════════════════════════════
def sakura_junk_cases(en: str, start_line: int) -> list:
    cases = []
    for _ in range(random.randint(1, 3)):
        cname = 'BuConCacTaoDi' + str(random.randint(2_061_584_302_080,
                                                       8_658_654_068_736))
        cases.append(ast.If(
            test=ast.Compare(
                left=ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Name(id=en, ctx=ast.Load()),
                        attr='args', ctx=ast.Load()),
                    slice=ast.Constant(0), ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(start_line)]),
            body=[ast.Assign(
                targets=[ast.Name(id=cname, ctx=ast.Store())],
                value=ast.Constant(random.randint(1_048_575, 281_474_976_710_655)),
                lineno=0, col_offset=0)],
            orelse=[]))
        start_line += 1
    return cases


def sakura_bl(body: list) -> list:
    var = 'NhinCaiLon' + str(random.randint(2_061_584_302_080, 8_658_654_068_736))
    en  = 'NhinConCac' + str(random.randint(2_061_584_302_080, 8_658_654_068_736))
    junk_cases = sakura_junk_cases(en, len(body) + 2)
    handler_body = [
        ast.If(
            test=ast.Compare(
                left=ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Name(id=en, ctx=ast.Load()),
                        attr='args', ctx=ast.Load()),
                    slice=ast.Constant(0), ctx=ast.Load()),
                ops=[ast.Eq()], comparators=[ast.Constant(1)]),
            body=[stmt], orelse=[])
        for stmt in body
    ] + junk_cases
    return [
        ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=ast.Constant(0), lineno=0, col_offset=0),
        ast.AugAssign(
            target=ast.Name(id=var, ctx=ast.Store()),
            op=ast.Add(), value=ast.Constant(1), lineno=0, col_offset=0),
        ast.Try(
            body=[ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id='MemoryError', ctx=ast.Load()),
                    args=[ast.Name(id=var, ctx=ast.Load())], keywords=[]),
                cause=None)],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='MemoryError', ctx=ast.Load()),
                name=en, body=handler_body)],
            orelse=[], finalbody=[])
    ]


def sakura_bl_func(node):
    olb = node.body
    var = '__' + str(random.randint(2_061_584_302_080, 8_658_654_068_736)) + '__'
    en  = '__' + str(random.randint(2_061_584_302_080, 8_658_654_068_736)) + '__'
    junk_cases  = sakura_junk_cases(en, len(olb) + 2)
    handler_body = [
        ast.If(
            test=ast.Compare(
                left=ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Name(id=en, ctx=ast.Load()),
                        attr='args', ctx=ast.Load()),
                    slice=ast.Constant(0), ctx=ast.Load()),
                ops=[ast.Eq()], comparators=[ast.Constant(1)]),
            body=[stmt], orelse=[])
        for stmt in olb
    ] + junk_cases
    node.body = [
        ast.Assign(
            targets=[ast.Name(id=var, ctx=ast.Store())],
            value=ast.Constant(0), lineno=0, col_offset=0),
        ast.AugAssign(
            target=ast.Name(id=var, ctx=ast.Store()),
            op=ast.Add(), value=ast.Constant(1), lineno=0, col_offset=0),
        ast.Try(
            body=[ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id='MemoryError', ctx=ast.Load()),
                    args=[ast.Name(id=var, ctx=ast.Load())], keywords=[]),
                cause=None)],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='MemoryError', ctx=ast.Load()),
                name=en, body=handler_body)],
            orelse=[], finalbody=[])
    ]
    return node


def random_match_case() -> ast.AST:
    v1 = ast.Constant(value=spam_hanzi())
    v2 = ast.Constant(value=spam_hanzi())
    return ast.Match(
        subject=ast.Compare(left=v1, ops=[ast.Eq()], comparators=[v2]),
        cases=[
            ast.match_case(
                pattern=ast.MatchValue(value=ast.Constant(value=True)),
                body=[ast.Assign(
                    lineno=0, col_offset=0, targets=[],
                    value=ast.Raise(exc=ast.Call(
                        func=ast.Name(id='MemoryError', ctx=ast.Load()),
                        args=[], keywords=[])))]
            ),
            ast.match_case(
                pattern=ast.MatchValue(value=ast.Constant(value=True)),
                body=[
                    ast.Assign(
                        lineno=0, col_offset=0,
                        targets=[ast.Name(id='_' + spam_hanzi(), ctx=ast.Store())],
                        value=ast.Constant(value=[True, False])),
                    ast.Expr(
                        lineno=0, col_offset=0,
                        value=ast.Call(
                            func=ast.Name(id=_STR_ALIAS, ctx=ast.Load()),
                            args=[ast.Constant(value='_' + spam_hanzi())],
                            keywords=[]))
                ]
            ),
        ]
    )


def sakura_trycatch(body: list, loop: int) -> list:
    result = []
    for x in body:
        cur = x
        for _ in range(loop):
            cur = ast.Try(
                body=[
                    random_match_case(),
                    ast.Raise(
                        exc=ast.Call(
                            func=ast.Name(id='MemoryError', ctx=ast.Load()),
                            args=[], keywords=[]),
                        cause=None),
                ],
                handlers=[ast.ExceptHandler(
                    type=ast.Name(id='MemoryError', ctx=ast.Load()),
                    name='_' + spam_hanzi(),
                    body=[cur])],
                orelse=[], finalbody=[])
        result.append(cur)
    return result


def yuamikami(tree: ast.Module) -> ast.Module:
    nb = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nb.append(sakura_bl_func(node))
        elif isinstance(node, ast.ClassDef):
            nb2 = []
            for n2 in node.body:
                if isinstance(n2, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nb2.append(sakura_bl_func(n2))
                elif isinstance(n2, (ast.Assign, ast.AugAssign,
                                     ast.AnnAssign, ast.Expr)):
                    nb2.extend(sakura_bl([n2]))
                elif isinstance(n2, ast.ClassDef):
                    inner = []
                    for n3 in n2.body:
                        if isinstance(n3, (ast.FunctionDef,
                                           ast.AsyncFunctionDef)):
                            inner.append(sakura_bl_func(n3))
                        else:
                            inner.append(n3)
                    n2.body = inner
                    nb2.append(n2)
                else:
                    nb2.append(n2)
            node.body = nb2
            nb.append(node)
        elif isinstance(node, (ast.Assign, ast.AugAssign,
                                ast.AnnAssign, ast.Expr)):
            nb.extend(sakura_bl([node]))
        else:
            nb.append(node)
    tree.body = nb
    return tree


def shenron_gen_junk(code: ast.AST) -> list:
    men = _korean_id()
    v1, v2 = _korean_id(), _korean_id()
    return [
        ast.Assign(
            targets=[ast.Name(id=v1, ctx=ast.Store())],
            value=ast.Constant(men), lineno=0, col_offset=0),
        ast.Assign(
            targets=[ast.Name(id=v2, ctx=ast.Store())],
            value=ast.Constant(True), lineno=0, col_offset=0),
        ast.If(
            test=ast.BoolOp(op=ast.And(), values=[
                ast.Compare(
                    left=ast.Name(id=v1, ctx=ast.Load()),
                    ops=[ast.Eq()], comparators=[ast.Constant(men)]),
                ast.Compare(
                    left=ast.Name(id=v2, ctx=ast.Load()),
                    ops=[ast.NotEq()], comparators=[ast.Constant(True)]),
            ]),
            body=[ast.Expr(value=ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[],
                    kw_defaults=[], defaults=[]),
                body=ast.Constant('dit me may')))],
            orelse=[ast.If(
                test=ast.BoolOp(op=ast.And(), values=[
                    ast.Compare(
                        left=ast.Name(id=v1, ctx=ast.Load()),
                        ops=[ast.Eq()], comparators=[ast.Constant(men)]),
                    ast.Compare(
                        left=ast.Name(id=v2, ctx=ast.Load()),
                        ops=[ast.NotEq()], comparators=[ast.Constant(False)]),
                ]),
                body=[ast.Try(
                    body=[ast.Expr(value=ast.Tuple(elts=[
                        ast.BinOp(
                            left=ast.Constant(1),
                            op=ast.Div(),
                            right=ast.Constant(0)),
                        ast.BinOp(
                            left=ast.Constant(123),
                            op=ast.Div(),
                            right=ast.Constant(0)),
                    ], ctx=ast.Load()))],
                    handlers=[ast.ExceptHandler(
                        type=None, name=None, body=[code])],
                    orelse=[], finalbody=[])],
                orelse=[ast.While(
                    test=ast.Constant(True),
                    body=[ast.Pass()], orelse=[])],
            )],
        ),
    ]

# ══════════════════════════════════════════════════════════════════════════════
# AST node transformers
# ══════════════════════════════════════════════════════════════════════════════
class _FStringFlattener(ast.NodeTransformer):
    """Replace f-strings with explicit str() join calls (hides them from tools)."""
    def visit_JoinedStr(self, node):
        self.generic_visit(node)
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(v)
            elif isinstance(v, ast.FormattedValue):
                expr = self.visit(v.value)
                if v.conversion == 114:   # !r
                    expr = ast.Call(ast.Name('repr', ast.Load()), [expr], [])
                elif v.conversion == 97:  # !a
                    expr = ast.Call(ast.Name('ascii', ast.Load()), [expr], [])
                else:
                    if not isinstance(expr, ast.Constant):
                        expr = ast.Call(ast.Name('goku', ast.Load()),
                                        [expr], [])
                if (v.format_spec and
                        isinstance(v.format_spec, ast.JoinedStr)):
                    spec = self.visit_JoinedStr(v.format_spec)
                    expr = ast.Call(
                        ast.Name('format', ast.Load()), [expr, spec], [])
                parts.append(expr)
            else:
                parts.append(
                    ast.Call(ast.Name('goku', ast.Load()), [v], []))
        if not parts:
            return ast.Constant('')
        if len(parts) == 1 and isinstance(parts[0], ast.Constant):
            return parts[0]
        return ast.Call(
            func=ast.Attribute(ast.Constant(''), 'join', ast.Load()),
            args=[ast.Tuple(parts, ast.Load())], keywords=[])


class _BuiltinHider(ast.NodeTransformer):
    """Replace direct builtin names with getattr(capsule_add('builtins'), name)."""
    def visit_Name(self, node):
        if (isinstance(node.ctx, ast.Load)
                and node.id in _BUILTINS
                and node.id not in _RUNNER_NAMES):
            return ast.Call(
                func=ast.Name('getattr', ast.Load()),
                args=[
                    ast.Call(ast.Name('capsule_add', ast.Load()),
                             [ast.Constant('builtins')], []),
                    ast.Constant(node.id),
                ],
                keywords=[])
        return node


class _ObfctVisitor(ast.NodeTransformer):
    """Obfuscate string and int constants in the AST."""
    def visit_Constant(self, node):
        try:
            if isinstance(node.value, str) and 0 < len(node.value) < 400:
                return obfct(node.value)
            if isinstance(node.value, int) and -1900 < node.value < 2010:
                return _obfint(node.value)
        except Exception:
            pass
        return node


class _ShenronJunkInject(ast.NodeTransformer):
    """Inject dead-branch junk statements around every real statement."""
    def _wrap_body(self, body: list) -> list:
        new = []
        for stmt in body:
            new.extend(shenron_gen_junk(stmt))
        return new

    def visit_Module(self, node):
        self.generic_visit(node)
        node.body = self._wrap_body(node.body)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.body = self._wrap_body(node.body)
        return node

    visit_ClassDef         = visit_FunctionDef
    visit_AsyncFunctionDef = visit_FunctionDef


class _VarRenamer(ast.NodeTransformer):
    """Rename all non-protected identifiers to random Korean syllables."""
    def __init__(self):
        self.aliases:    dict = {}
        self._protected: set  = set()

    def _protect(self, tree: ast.AST) -> None:
        import builtins as _bi
        self._protected.update(vars(_bi).keys())
        self._protected.update(_BUILTINS)
        self._protected.update(_RUNNER_NAMES)
        self._protected.update({
            'self', 'cls',
            '__name__', '__file__', '__doc__',
            '__init__', '__call__', '__str__', '__repr__',
            '__len__', '__iter__', '__next__',
            '__enter__', '__exit__',
            _STR_ALIAS, _INT_ALIAS, _FLOAT_ALIAS, _BOOL_ALIAS,
            _BYTES_ALIAS, _EVAL_ALIAS, _PRINT_ALIAS, _INPUT_ALIAS,
            'MemoryError',
        })
        self._protected.update(_LIST_TEN_BIEN)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self._protected.add(a.asname or a.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    self._protected.add(a.asname or a.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._protected.add(node.name)
            elif isinstance(node, ast.ClassDef):
                self._protected.add(node.name)
            elif isinstance(node, ast.Global):
                for n in node.names:
                    self._protected.add(n)
            elif isinstance(node, ast.Nonlocal):
                for n in node.names:
                    self._protected.add(n)

    def _alias(self, name: str) -> str:
        if name in self._protected or name.startswith('__'):
            return name
        if name in self.aliases:
            return self.aliases[name]
        new = _korean_id()
        self.aliases[name] = new
        return new

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Load, ast.Del)):
            if (node.id not in self._protected
                    and not node.id.startswith('__')):
                node.id = self._alias(node.id)
        return node

    def visit_arg(self, node):
        if (node.arg not in self._protected
                and not node.arg.startswith('__')):
            node.arg = self._alias(node.arg)
        return node

    def visit_ExceptHandler(self, node):
        if (node.name
                and node.name not in self._protected
                and not node.name.startswith('__')):
            node.name = self._alias(node.name)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

# ══════════════════════════════════════════════════════════════════════════════
# Anti-dis block injected at top of every enc file
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# Anti-dis block injected at top of every enc file
# ══════════════════════════════════════════════════════════════════════════════
_ANTI_DIS_BLOCK = r"""
import sys as _sys_ad, os as _os_ad, builtins as _bt_ad

class _FakeDis:
    # kills process on any attribute access
    def __getattr__(self, _n):
        _os_ad._exit(0)
    def __call__(self, *_a, **_kw):
        _os_ad._exit(0)

_blocked_mods = (
    'uncompyle6', 'decompile3', 'pycdc', 'decompyle3',
    'unpyc3', 'bytecode', 'xdis', 'decompile',
    'pydevd', 'pydevd_tracing', 'birdseye',
)

for _bm in _blocked_mods:
    _sys_ad.modules[_bm] = _FakeDis()

def _safe_import(_name, *_a, _real_import=_bt_ad.__import__, **_kw):
    _kill = {
        'uncompyle6','decompile3','pycdc','decompyle3',
        'unpyc3','bytecode','xdis','decompile',
        'pydevd','birdseye',
    }
    if _name in _kill:
        _os_ad._exit(0)
    return _real_import(_name, *_a, **_kw)
_bt_ad.__import__ = _safe_import

try:
    import ctypes as _ct
    if hasattr(_ct, 'pythonapi'):
        _ct.pythonapi.PyFrame_LocalsToFast = None
except Exception:
    pass

del _bm, _blocked_mods
"""

# ══════════════════════════════════════════════════════════════════════════════
# _build_runner — build the 3-stage nested-exec runner source
# ══════════════════════════════════════════════════════════════════════════════
def _build_runner(compressed: bytes, raw_bytecode: bytes, ver: str,
                  bot_name: str, bot_username: str,
                  owner: str, vn_time: str) -> str:

    # Encode payload + sign
    hanzi_payload  = hanzi_encode(compressed)
    integrity_hash = _compute_integrity(raw_bytecode) # Tính hash trên bytecode chưa nén


    # Random variable names for the runner skeleton
    V   = [_korean_id() for _ in range(30)]
    va  = _korean_id(); vb  = _korean_id(); vd = _korean_id()
    vk  = _korean_id(); vc  = _korean_id(); vs = _korean_id()
    vv  = _korean_id(); varg = _korean_id()

    # Random names for layer variables
    lv1 = _korean_id()   # layer-1 compressed blob variable
    lv2 = _korean_id()   # layer-2 function name
    lv3 = _korean_id()   # layer-3 function name

    se  = shenron_enc
    pro = build_pro_code()

    # chr() encoded module/function names (anti static analysis)
    _sys_chr     = _chr('sys')
    _os_chr      = _chr('os')
    _ver_chr     = _chr(ver)
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
    _exit_str    = _chr('<built-in function exit>')
    _print_str   = _chr('<built-in function print>')
    _exec_str    = _chr('<built-in function exec>')
    _len_str     = _chr('<built-in function len>')
    _loads_str   = _chr('<built-in function loads>')
    _hook_str    = _chr('Hook ha con trai')

    # ── Anti-hook checks (verify builtins have not been monkeypatched) ────────
    anti_hooks = f"""
if goku(capsule_add({se('sys')}).exit) != {_exit_str}:
    print({_hook_str}); capsule_add({se('sys')}).exit()
if goku(getattr(capsule_add({se('builtins')}),{se('print')})) != {_print_str}:
    print({_hook_str}); capsule_add({se('sys')}).exit()
if goku(getattr(capsule_add({se('builtins')}),{se('exec')})) != {_exec_str}:
    print({_hook_str}); capsule_add({se('sys')}).exit()
if goku(getattr(capsule_add({se('builtins')}),{se('len')})) != {_len_str}:
    print({_hook_str}); capsule_add({se('sys')}).exit()
if goku(capsule_add({se('marshal')}).loads) != {_loads_str}:
    print({_hook_str}); capsule_add({se('sys')}).exit()
"""

    # ── Anti-proxy / anti-httptoolkit ─────────────────────────────────────────
    vip_anti = f"""
if capsule_add({_os_chr}).environ.get({se('HTTP_TOOLKIT_ACTIVE')}) == {se('true')}:
    capsule_add({_sys_chr}).exit()
for {V[0]} in [{se('SSL_CERT_FILE')},{se('NODE_EXTRA_CA_CERTS')},{se('PYTHONPATH')}]:
    if ({V[0]} in capsule_add({_os_chr}).environ and
            {se('httptoolkit')} in capsule_add({_os_chr}).environ[{V[0]}].lower()):
        capsule_add({_sys_chr}).exit()
for {V[1]} in [{se('HTTP_PROXY')},{se('HTTPS_PROXY')},{se('http_proxy')},{se('https_proxy')}]:
    if ({V[1]} in capsule_add({_os_chr}).environ and
            {se('127.0.0.1')} in capsule_add({_os_chr}).environ[{V[1]}]):
        capsule_add({_sys_chr}).exit()
"""

    # ══ Layer 3: HMAC verify → marshal.loads → exec ═══════════════════════════
    # NOTE: uses raw string – no f-string interpolation inside
    layer3_src = (
        "import marshal as _m3, hmac as _h3, hashlib as _hs3, os as _o3\n"
        f"def {lv3}(_rb, _sig):\n"
        "    _key = b'CuongObfIntegrity2010ShenronVIP'\n"
        "    _exp = _h3.new(_key, _rb, _hs3.sha256).hexdigest()\n"
        "    if not _h3.compare_digest(_sig, _exp):\n"
        "        _o3._exit(0)\n"
        "    _co = _m3.loads(_rb)\n"
        "    exec(_co, globals())\n"

    )

    # ══ Layer 2: decode Hanzi → decompress → call layer3 ═════════════════════
    # Compression order (encode): lzma → zlib → bz2 → a85encode
    # Decompression order (decode): a85decode → bz2 → zlib → lzma
    layer2_src = (
        "import zlib as _z2, bz2 as _b2, lzma as _lx2, base64 as _64_2\n"
        f"_HD2 = {repr(HANZI_DEC)}\n"
        "def _hd2(s): return bytes.fromhex(''.join(_HD2[c] for c in s))\n"
        f"def {lv2}(_pl, _sig):\n"
        # Đã sửa lại đúng thứ tự: a85decode -> bz2 -> zlib -> lzma
        "    _raw = _lx2.decompress(_z2.decompress(_b2.decompress(_64_2.a85decode(_hd2(_pl)))))\n"
        f"    exec(compile({repr(layer3_src)}, '<l3>', 'exec'), globals())\n"
        f"    {lv3}(_raw, _sig)\n"
        f"{lv2}({repr(hanzi_payload)}, {repr(integrity_hash)})\n"
    )

    # Compress layer2 source → base64 (used by layer1)
    layer2_blob = base64.b64encode(
        zlib.compress(layer2_src.encode('utf-8'), 9)
    ).decode()

    # ══ Assemble final runner (layer1 = top-level executable) ════════════════
    runner = (
        f"#!/usr/bin/env python3\n"
        f"# -*- coding: utf-8 -*-\n"
        f"# ╔══════════════════════════════════════════╗\n"
        f"# ║  Obf by : {bot_name} ({bot_username})\n"
        f"# ║  Owner  : {owner}\n"
        f"# ║  Time   : {vn_time}\n"
        f"# ║  Python : 3.13 \n"
        f"# ╚══════════════════════════════════════════╝\n"
        f"\n"
        f"__INFO__ = {{\n"
        f"    'Obfuscator': '{bot_name}',\n"
        f"    'Owner': '{owner}',\n"
        f"    'Version': '1.0',\n"
        f"    'Python': 13,\n"
        f"}}\n"
        f"\n"
        f"{_ANTI_DIS_BLOCK}\n"
        f"\n"
        f"class CapsuleCorp(object):\n"
        f"\n"
        f"    def __init__(self):\n"
        f"        {V[20]} = __import__({_sys_chr})\n"
        f"        if str({V[20]}.version_info.major) != chr(51):\n"
        f"            {V[20]}.exit()\n"
        f"        else:\n"
        f"            {V[20]}.stderr.write({_run_chr}+chr(10))\n"
        f"\n"
        f"    def __call__(self, *{va}, **{vb}):\n"
        f"        global yamcha, capsule, radar, shenron, frieza, goku, vegeta, gohan, trunks, bulma, kamehameha, capsule_add\n"
        f"        globals()[{_frieza_chr}] = eval(chr(101)+chr(118)+chr(97)+chr(108))\n"
        f"        globals()[{_goku_chr}] = frieza(chr(115)+chr(116)+chr(114))\n"
        f"        globals()[{_vegeta_chr}] = frieza(chr(98)+chr(121)+chr(116)+chr(101)+chr(115))\n"
        f"        globals()[{_gohan_chr}] = frieza(chr(100)+chr(105)+chr(99)+chr(116))\n"
        f"        globals()[{_bulma_chr}] = {repr(_B64)}\n"
        f"        globals()[{_capsule_chr}] = {repr(_EMOJI_ALPHA)}\n"
        f"        globals()[{_trunks_chr}] = frieza(chr(122)+chr(105)+chr(112))\n"
        f"        globals()[{_radar_chr}] = gohan(trunks(bulma, capsule))\n"
        f"        {vd} = {{{vv}: {vk} for {vk}, {vv} in radar.items()}}\n"
        f"        globals()[{_shenron_chr}] = lambda {vs}: getattr(vegeta, {_fromhex_chr})"
        f"(goku().join(({vd}.get({vc}, {vc}) for {vc} in {vs}))).decode()\n"
        f"        globals()[{se('capsule_add')}] = frieza({se('__tropmi__')}[::-1])\n"
        f"        globals()[{se('kamehameha')}] = frieza({se('cexe')}[::-1])\n"
        f"        globals()[{se('yamcha')}] = frieza({se('tni')}[::-1])\n"
        f"\n"
        f"CapsuleCorp()()\n"
        f"{anti_hooks}\n"
        f"{vip_anti}\n"
        f"{V[2]} = vars(globals()[{se('__builtins__')}])\n"
        f"\n"
        f"{pro}\n"
        f"# ── Layer 1: decompress → exec Layer 2 ──────────────────────────────\n"
        f"import zlib as _zl1, base64 as _b641\n"
        f"{lv1} = _b641.b64decode({repr(layer2_blob)})\n"
        f"exec(compile(_zl1.decompress({lv1}).decode('utf-8'), '<l2>', 'exec'), globals())\n"
    )
    return runner

# ══════════════════════════════════════════════════════════════════════════════
# obfuscate_code — main entry: AST passes + runner build
# ══════════════════════════════════════════════════════════════════════════════
def obfuscate_code(source: str, bot_name: str,
                   bot_username: str, owner: str) -> str:
    ver     = f'{sys.version_info.major}.{sys.version_info.minor}'
    vn_time = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')

    tree = ast.parse(source)

    # Pass 1: rename variables
    renamer = _VarRenamer()
    renamer._protect(tree)
    renamer.visit(tree)

    # Pass 2: flatten f-strings
    _FStringFlattener().visit(tree)

    # Pass 3: obfuscate constants
    _ObfctVisitor().visit(tree)

    # Pass 4: hide builtins
    _BuiltinHider().visit(tree)

    # Pass 5: MemoryError junk blocks
    yuamikami(tree)

    # Pass 6: dead-branch junk injection
    _ShenronJunkInject().visit(tree)

    # Pass 7: sakura try/catch wrapping
    tree.body = sakura_trycatch(tree.body, 2)

    ast.fix_missing_locations(tree)
    obf_src = ast.unparse(tree)

    # Compile → bytecode → compress stack: lzma → zlib → bz2 → a85
    code_obj   = compile(obf_src, '<CuongObf>', 'exec')
    bytecode   = marshal.dumps(code_obj)
    compressed = base64.a85encode(
        bz2.compress(zlib.compress(lzma.compress(bytecode))))

    return _build_runner(compressed, bytecode, ver, bot_name,
                         bot_username, owner, vn_time)


# ══════════════════════════════════════════════════════════════════════════════
# MarkdownV2 escape helper
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# MarkdownV2 escape helper (ĐÃ SỬA CHUẨN)
# ══════════════════════════════════════════════════════════════════════════════
def _mdv2(s: str) -> str:
    """Escape tất cả các ký tự đặc biệt của MarkdownV2 theo đúng tài liệu Telegram."""
    escaped = ""
    # Các ký tự cần escape ngoài đời thực (nếu không nằm trong code block)
    special_chars = r"_*[]()~`>#+-=|{}.!"
    
    # Phải escape dấu gạch chéo ngược '\' đầu tiên để tránh lỗi trùng lặp
    s = s.replace('\\', '\\\\')
    
    for ch in special_chars:
        s = s.replace(ch, '\\' + ch)
    return s

# ══════════════════════════════════════════════════════════════════════════════
# Telegram message templates
# ══════════════════════════════════════════════════════════════════════════════
def _start_msg() -> str:
    ow = _mdv2(OWNER)
    bu = _mdv2(BOT_USERNAME)
    return (
        "╔══════════════════════════════════╗\n"
        "║  🔐 *CuongObf — Cpython Bot* 🔐  ║\n"
        "╚══════════════════════════════════╝\n"
        "\n"
        "> 🛡️ Bot mã hoá Python đa lớp bảo vệ cao cấp\n"
        "> Kết hợp nhiều kỹ thuật anti\\-decompile tiên tiến\n"  # Đã thêm \ trước dấu -
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *CÁCH DÙNG*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "> 📎 Gửi file `.py` → bot tự động mã hoá\n"
        "> 💬 Hoặc paste code Python trực tiếp vào chat\n"
        "> 📥 Nhận lại file `enc-*` đã được bảo vệ\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Owner:* `{ow}`\n"
        f"🤖 *Bot:* `{bu}`"
    )

def _progress_msg(fname: str = '') -> str:
    tag = f'`{_mdv2(fname)}` ' if fname else ''
    return (
        f"⏳ *Đang mã hoá* {tag}\\.\\.\\.\n"  # Đã thêm \ trước các dấu chấm
        "\n"
        "> 🀄 ĐỢI MỘT LÁT \\.\\.\\.\\.\\. \n"  # Đã thêm \ trước các dấu chấm
    )

def _success_msg(out_name: str, vn_time: str) -> str:
    fn = _mdv2(out_name)
    vt = _mdv2(vn_time)
    ow = _mdv2(OWNER)
    bu = _mdv2(BOT_USERNAME)
    return (
        "╔═════════════════════════════╗\n"
        "║  ✅ *Mã hoá thành công\\!* ✅ ║\n"  # Đã thêm \ trước dấu chấm than
        "╚═════════════════════════════╝\n"
        "\n"
        f"> 📄 *File:* `{fn}`\n"
        f"> 🕐 *Time:* `{vt}`\n"
        f"> 🤖 *Bot:* `{bu}`\n"
        f"> 👑 *Owner:* `{ow}`\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

def _doc_caption(out_name: str) -> str:
    fn = _mdv2(out_name)
    bn = _mdv2(BOT_NAME)
    bu = _mdv2(BOT_USERNAME)
    ow = _mdv2(OWNER)
    return f'✅ `{fn}`\n🤖 {bn} {bu}\n👑 {ow}'

def _err_msg(label: str, err: str) -> str:
    return f'> ❌ *{_mdv2(label)}*\n`{_mdv2(err)}`'

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        _start_msg(), parse_mode=ParseMode.MARKDOWN_V2)


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not (doc.file_name or '').endswith('.py'):
        # Thay vì dùng _mdv2, chúng ta viết đúng chuẩn MarkdownV2
        err_txt = "> ❌ Chỉ hỗ trợ file `.py`"
        await update.message.reply_text(err_txt, parse_mode=ParseMode.MARKDOWN_V2)

        return


    progress = await update.message.reply_text(
        _progress_msg(doc.file_name),
        parse_mode=ParseMode.MARKDOWN_V2)

    tmp_in  = tempfile.NamedTemporaryFile(
        suffix='.py', delete=False, mode='w', encoding='utf-8')
    tmp_out = tempfile.mktemp(suffix='.py')

    try:
        file_obj = await ctx.bot.get_file(doc.file_id)
        await file_obj.download_to_drive(tmp_in.name)
        with open(tmp_in.name, 'r', encoding='utf-8') as f:
            source = f.read()

        result   = obfuscate_code(source, BOT_NAME, BOT_USERNAME, OWNER)
        out_name = 'enc-' + doc.file_name
        vn_time  = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')

        with open(tmp_out, 'w', encoding='utf-8') as f:
            f.write(result)

        await progress.edit_text(
            _success_msg(out_name, vn_time),
            parse_mode=ParseMode.MARKDOWN_V2)

        with open(tmp_out, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=out_name,
                caption=_doc_caption(out_name),
                parse_mode=ParseMode.MARKDOWN_V2)

    except SyntaxError as e:
        await progress.edit_text(
            _err_msg('Lỗi cú pháp', str(e)),
            parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await progress.edit_text(
            _err_msg('Lỗi', str(e)),
            parse_mode=ParseMode.MARKDOWN_V2)
    finally:
        for p in [tmp_in.name, tmp_out]:
            try:
                os.unlink(p)
            except Exception:
                pass


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    py_starters = (
        'import ', 'from ', 'def ', 'class ', '#', 'print(',
        'if ', 'for ', 'while ', 'try:', 'with ', 'async ',
        '@', 'lambda ', 'return ', 'yield ',
    )
    if not any(text.startswith(s) for s in py_starters):
        # Thêm \ trước dấu chấm ở cuối câu
        text_err = "> 💬 Gửi file `.py` hoặc paste code Python để mã hoá\\."
        await update.message.reply_text(text_err, parse_mode=ParseMode.MARKDOWN_V2)


        return

    progress = await update.message.reply_text(
        _progress_msg(), parse_mode=ParseMode.MARKDOWN_V2)
    tmp_out = tempfile.mktemp(suffix='.py')

    try:
        result  = obfuscate_code(text, BOT_NAME, BOT_USERNAME, OWNER)
        vn_time = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S (GMT+7)')

        with open(tmp_out, 'w', encoding='utf-8') as f:
            f.write(result)

        await progress.edit_text(
            _success_msg('enc-code.py', vn_time),
            parse_mode=ParseMode.MARKDOWN_V2)

        with open(tmp_out, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename='enc-code.py',
                caption=_doc_caption('enc-code.py'),
                parse_mode=ParseMode.MARKDOWN_V2)

    except SyntaxError as e:
        await progress.edit_text(
            _err_msg('Lỗi cú pháp', str(e)),
            parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await progress.edit_text(
            _err_msg('Lỗi', str(e)),
            parse_mode=ParseMode.MARKDOWN_V2)
    finally:
        try:
            os.unlink(tmp_out)
        except Exception:
            pass
           
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update or polling:", exc_info=context.error)

def main() -> None:
    if not BOT_TOKEN:
        print('BOT_TOKEN chưa được set!')
        sys.exit(1)
    print(f'{BOT_NAME} Bot đang khởi động...')
    print(f'Owner : {OWNER}')
    print(f'Bot   : {BOT_USERNAME}')
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help',  cmd_start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # BẮT BUỘC THÊM DÒNG NÀY ĐỂ BẮT LỖI
    app.add_error_handler(error_handler)
    
    print('Bot đang chạy — nhấn Ctrl+C để dừng.')
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
