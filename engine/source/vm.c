#include "vm.h"

#include <ctype.h>
#include <stdarg.h>

enum {
    OP_NOP = 0x00, OP_END, OP_JMP, OP_JZ, OP_JNZ, OP_CALL, OP_RET, OP_POP, OP_DUP,
    OP_PUSH_NUM = 0x10, OP_PUSH_STR, OP_PUSH_NONE, OP_PUSH_TRUE, OP_PUSH_FALSE, OP_LOAD, OP_STORE,
    OP_ADD = 0x20, OP_SUB, OP_MUL, OP_DIV, OP_FLOORDIV, OP_MOD, OP_POW, OP_NEG, OP_NOT,
    OP_EQ = 0x2A, OP_NE, OP_LT, OP_LE, OP_GT, OP_GE, OP_CALLF, OP_IN,
    OP_SAY = 0x40, OP_MENU_BEGIN, OP_MENU_ITEM, OP_MENU, OP_PAUSE, OP_SCENE, OP_SHOW, OP_HIDE,
    OP_WITH, OP_SHOW_ATTR,
    OP_PLAY = 0x50, OP_STOP, OP_WINDOW, OP_MINIGAME,
};

/* ---- values ------------------------------------------------------------ */

void value_free(Value *v)
{
    if (v->type == VAL_STR)
        free(v->str);
    v->type = VAL_NONE;
    v->str = NULL;
    v->num = 0;
}

void value_set_str(Value *v, const char *s)
{
    value_free(v);
    v->type = VAL_STR;
    v->str = strdup(s ? s : "");
}

static Value v_num(double d) { Value v = {VAL_NUM, d, NULL}; return v; }
static Value v_bool(bool b) { Value v = {VAL_BOOL, b ? 1 : 0, NULL}; return v; }

static Value v_str(const char *s)
{
    Value v = {VAL_STR, 0, strdup(s ? s : "")};
    return v;
}

static Value v_copy(const Value *src)
{
    Value v = *src;
    if (v.type == VAL_STR)
        v.str = strdup(src->str ? src->str : "");
    return v;
}

static bool truthy(const Value *v)
{
    switch (v->type) {
    case VAL_BOOL:
    case VAL_NUM: return v->num != 0;
    case VAL_STR: return v->str && v->str[0];
    default: return false;
    }
}

static double as_num(const Value *v)
{
    if (v->type == VAL_NUM || v->type == VAL_BOOL)
        return v->num;
    if (v->type == VAL_STR && v->str)
        return atof(v->str);
    return 0;
}

static void to_string(const Value *v, char *buf, size_t len)
{
    switch (v->type) {
    case VAL_NONE: snprintf(buf, len, "None"); break;
    case VAL_BOOL: snprintf(buf, len, "%s", v->num ? "True" : "False"); break;
    case VAL_STR: snprintf(buf, len, "%s", v->str ? v->str : ""); break;
    default:
        if (v->num == floor(v->num) && fabs(v->num) < 1e15)
            snprintf(buf, len, "%.0f", v->num);
        else
            snprintf(buf, len, "%.12g", v->num);
    }
}

/* ---- VM ---------------------------------------------------------------- */

static void fail(VM *vm, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(vm->error, sizeof(vm->error), fmt, ap);
    va_end(ap);
    LOG("script error at %06x: %s", (unsigned)vm->pc, vm->error);
    vm->state = VM_ERROR;
}

static void push(VM *vm, Value v)
{
    if (vm->sp >= VM_STACK) {
        value_free(&v);
        fail(vm, "expression stack overflow");
        return;
    }
    vm->stack[vm->sp++] = v;
}

static Value pop(VM *vm)
{
    if (vm->sp <= 0) {
        fail(vm, "expression stack underflow");
        Value v = {VAL_NONE, 0, NULL};
        return v;
    }
    return vm->stack[--vm->sp];
}

void vm_init(VM *vm, const Game *g)
{
    memset(vm, 0, sizeof(*vm));
    vm->g = g;
    vm->vars = calloc(g->nvars + 1, sizeof(Value));
    vm->state = VM_ENDED;
}

static void clear_state(VM *vm)
{
    while (vm->sp > 0) {
        Value v = pop(vm);
        value_free(&v);
    }
    for (u32 i = 0; i < vm->g->nvars; i++)
        value_free(&vm->vars[i]);
    vm->ncalls = 0;
    vm->nchoices = 0;
    vm->last_char = 0;
    vm->last_text[0] = 0;
    vm->error[0] = 0;
}

void vm_free(VM *vm)
{
    if (!vm->g)
        return;
    clear_state(vm);
    free(vm->vars);
    vm->vars = NULL;
}

void vm_new_game(VM *vm)
{
    clear_state(vm);
    vm->pc = vm->g->init_addr;
    vm->resume_pc = vm->pc;
    vm->state = VM_RUNNING;
}

static int find_var(const Game *g, const char *name, size_t len)
{
    for (u32 i = 0; i < g->nvars; i++) {
        const char *n = g->var_names[i];
        if (n && strlen(n) == len && memcmp(n, name, len) == 0)
            return (int)i;
    }
    return -1;
}

void vm_interpolate(const VM *vm, const char *src, char *out, size_t len)
{
    size_t o = 0;
    if (len == 0)
        return;
    while (*src && o + 1 < len) {
        if (src[0] == '[' && src[1] == '[') {
            out[o++] = '[';
            src += 2;
            continue;
        }
        if (src[0] == '[') {
            const char *end = strchr(src, ']');
            if (!end) {
                out[o++] = *src++;
                continue;
            }
            const char *name = src + 1;
            while (name < end && *name == ' ')
                name++;
            size_t n = 0;
            while (name + n < end && name[n] != '!' && name[n] != ':' && name[n] != ' ')
                n++;
            char conv = 0;
            const char *bang = memchr(name, '!', (size_t)(end - name));
            if (bang && bang + 1 < end)
                conv = bang[1];
            char buf[256] = "";
            int vi = find_var(vm->g, name, n);
            if (vi >= 0)
                to_string(&vm->vars[vi], buf, sizeof(buf));
            for (char *c = buf; *c; c++) {
                if (conv == 'u')
                    *c = (char)toupper((unsigned char)*c);
                else if (conv == 'l')
                    *c = (char)tolower((unsigned char)*c);
            }
            if ((conv == 'c' || conv == 't') && buf[0])
                buf[0] = (char)toupper((unsigned char)buf[0]);
            for (char *c = buf; *c && o + 1 < len; c++)
                out[o++] = *c;
            src = end + 1;
            continue;
        }
        out[o++] = *src++;
    }
    out[o] = 0;
}

static void binop(VM *vm, u8 op)
{
    Value b = pop(vm), a = pop(vm);
    Value r = {VAL_NONE, 0, NULL};
    if (op == OP_ADD && (a.type == VAL_STR || b.type == VAL_STR)) {
        char sa[VM_TEXT], sb[VM_TEXT];
        to_string(&a, sa, sizeof(sa));
        to_string(&b, sb, sizeof(sb));
        size_t la = strlen(sa), lb = strlen(sb);
        r.type = VAL_STR;
        r.str = malloc(la + lb + 1);
        memcpy(r.str, sa, la);
        memcpy(r.str + la, sb, lb + 1);
    } else if (op == OP_MUL && (a.type == VAL_STR || b.type == VAL_STR)) {
        const Value *s = a.type == VAL_STR ? &a : &b;
        int times = (int)as_num(a.type == VAL_STR ? &b : &a);
        size_t ls = strlen(s->str);
        if (times < 0)
            times = 0;
        if (ls * (size_t)times > 4096)
            times = (int)(4096 / (ls ? ls : 1));
        r.type = VAL_STR;
        r.str = malloc(ls * (size_t)times + 1);
        for (int i = 0; i < times; i++)
            memcpy(r.str + ls * (size_t)i, s->str, ls);
        r.str[ls * (size_t)times] = 0;
    } else {
        double x = as_num(&a), y = as_num(&b);
        double v = 0;
        switch (op) {
        case OP_ADD: v = x + y; break;
        case OP_SUB: v = x - y; break;
        case OP_MUL: v = x * y; break;
        case OP_DIV:
        case OP_FLOORDIV:
        case OP_MOD:
            if (y == 0) {
                fail(vm, "division by zero");
                break;
            }
            if (op == OP_DIV)
                v = x / y;
            else if (op == OP_FLOORDIV)
                v = floor(x / y);
            else
                v = x - y * floor(x / y);
            break;
        case OP_POW: v = pow(x, y); break;
        }
        r = v_num(v);
    }
    value_free(&a);
    value_free(&b);
    push(vm, r);
}

static bool values_equal(const Value *a, const Value *b)
{
    if (a->type == VAL_STR || b->type == VAL_STR) {
        if (a->type != b->type)
            return false;
        return strcmp(a->str, b->str) == 0;
    }
    if (a->type == VAL_NONE || b->type == VAL_NONE)
        return a->type == b->type;
    return a->num == b->num;
}

static void compare(VM *vm, u8 op)
{
    Value b = pop(vm), a = pop(vm);
    bool r;
    if (op == OP_EQ || op == OP_NE) {
        r = values_equal(&a, &b) == (op == OP_EQ);
    } else {
        int c;
        if (a.type == VAL_STR && b.type == VAL_STR) {
            c = strcmp(a.str, b.str);
        } else {
            double x = as_num(&a), y = as_num(&b);
            c = x < y ? -1 : (x > y ? 1 : 0);
        }
        switch (op) {
        case OP_LT: r = c < 0; break;
        case OP_LE: r = c <= 0; break;
        case OP_GT: r = c > 0; break;
        default: r = c >= 0; break;
        }
    }
    value_free(&a);
    value_free(&b);
    push(vm, v_bool(r));
}

static void callf(VM *vm, u8 fn, u8 nargs)
{
    Value args[8];
    if (nargs > 8) {
        fail(vm, "too many arguments");
        return;
    }
    for (int i = nargs - 1; i >= 0; i--)
        args[i] = pop(vm);
    Value r = {VAL_NONE, 0, NULL};
    char buf[VM_TEXT];
    switch (fn) {
    case 0: { /* randint */
        long lo = nargs > 0 ? (long)as_num(&args[0]) : 0;
        long hi = nargs > 1 ? (long)as_num(&args[1]) : lo;
        if (hi < lo)
            hi = lo;
        r = v_num((double)(lo + rand() % (hi - lo + 1)));
        break;
    }
    case 1: r = v_num((double)rand() / ((double)RAND_MAX + 1.0)); break;
    case 2:
        r = v_num(nargs && args[0].type == VAL_STR ? (double)utf8_len(args[0].str) : 0);
        break;
    case 3:
        to_string(nargs ? &args[0] : &r, buf, sizeof(buf));
        r = v_str(nargs ? buf : "");
        break;
    case 4:
        r = v_num(nargs ? trunc(args[0].type == VAL_STR ? strtod(args[0].str, NULL) : as_num(&args[0])) : 0);
        break;
    case 5: r = v_num(nargs ? as_num(&args[0]) : 0); break;
    case 6: r = v_num(nargs ? fabs(as_num(&args[0])) : 0); break;
    case 7:
    case 8:
        if (nargs) {
            int best = 0;
            for (int i = 1; i < nargs; i++) {
                double x = as_num(&args[i]), y = as_num(&args[best]);
                if (fn == 7 ? x < y : x > y)
                    best = i;
            }
            r = v_copy(&args[best]);
        }
        break;
    case 9: {
        double x = nargs ? as_num(&args[0]) : 0;
        int digits = nargs > 1 ? (int)as_num(&args[1]) : 0;
        double m = pow(10, digits);
        r = v_num(round(x * m) / m);
        break;
    }
    case 10: r = v_bool(nargs ? truthy(&args[0]) : false); break;
    case 11: /* s[i] */
    case 12: { /* s[a:b] */
        const char *s = nargs && args[0].type == VAL_STR ? args[0].str : "";
        long n = (long)utf8_len(s);
        long a, b;
        if (fn == 11) {
            a = nargs > 1 ? (long)as_num(&args[1]) : 0;
            if (a < 0)
                a += n;
            if (a < 0 || a >= n) {
                fail(vm, "string index out of range");
                break;
            }
            b = a + 1;
        } else {
            a = nargs > 1 && args[1].type != VAL_NONE ? (long)as_num(&args[1]) : 0;
            b = nargs > 2 && args[2].type != VAL_NONE ? (long)as_num(&args[2]) : n;
            if (a < 0)
                a += n;
            if (b < 0)
                b += n;
            a = a < 0 ? 0 : (a > n ? n : a);
            b = b < a ? a : (b > n ? n : b);
        }
        size_t oa = utf8_offset(s, (size_t)a), ob = utf8_offset(s, (size_t)b);
        r.type = VAL_STR;
        r.str = malloc(ob - oa + 1);
        memcpy(r.str, s + oa, ob - oa);
        r.str[ob - oa] = 0;
        break;
    }
    case 13: case 14: case 15: case 16: case 17: { /* upper lower title strip capitalize */
        char *s = strdup(nargs && args[0].type == VAL_STR ? args[0].str : "");
        if (fn == 16) {
            char *b = s;
            while (*b && isspace((unsigned char)*b))
                b++;
            memmove(s, b, strlen(b) + 1);
            size_t l = strlen(s);
            while (l > 0 && isspace((unsigned char)s[l - 1]))
                s[--l] = 0;
        } else {
            bool start = true;
            for (char *c = s; *c; c++) {
                unsigned char ch = (unsigned char)*c;
                if (fn == 13 || (fn == 15 && start) || (fn == 17 && c == s))
                    *c = (char)toupper(ch);
                else if (fn == 14 || fn == 15 || fn == 17)
                    *c = (char)tolower(ch);
                start = !isalpha(ch);
            }
        }
        r.type = VAL_STR;
        r.str = s;
        break;
    }
    default: fail(vm, "unknown builtin %d", fn); break;
    }
    for (int i = 0; i < nargs; i++)
        value_free(&args[i]);
    push(vm, r);
}

#define NEED(n)                                                   \
    do {                                                          \
        if (vm->pc + (n) > g->code_size) {                        \
            fail(vm, "truncated instruction");                    \
            return;                                               \
        }                                                         \
    } while (0)
#define U8() (code[vm->pc++])
#define U32() (vm->pc += 4, rd_u32(code + vm->pc - 4))
#define S32() (vm->pc += 4, rd_s32(code + vm->pc - 4))
#define F32() (vm->pc += 4, rd_f32(code + vm->pc - 4))

static void do_say(VM *vm, u32 at, s32 ch, u32 who, u32 what, u8 flags)
{
    const Game *g = vm->g;
    vm->resume_pc = at;
    if (ch == -2) {
        ch = vm->last_char;
        flags |= SAY_EXTEND;
    }
    if (ch < 0 || (u32)ch >= g->nchars)
        ch = 0;
    const CharDef *c = &g->chars[ch];
    vm->say_char = ch;
    const char *name = who != NONE_STR ? game_str(g, who) : c->name;
    if (name)
        vm_interpolate(vm, name, vm->say_who, sizeof(vm->say_who));
    else
        vm->say_who[0] = 0;

    char text[VM_TEXT];
    vm_interpolate(vm, game_str(g, what) ? game_str(g, what) : "", text, sizeof(text));
    vm->extend_from = 0;
    if (flags & SAY_EXTEND) {
        size_t l = strlen(vm->last_text);
        vm->extend_from = l;
        snprintf(vm->last_text + l, sizeof(vm->last_text) - l, "%s", text);
    } else {
        snprintf(vm->last_text, sizeof(vm->last_text), "%s%s", c->prefix ? c->prefix : "", text);
    }
    snprintf(vm->say_text, sizeof(vm->say_text), "%s%s", vm->last_text, c->suffix ? c->suffix : "");
    vm->last_char = ch;
    vm->say_flags = flags;
}

static void read_show(VM *vm, bool scene)
{
    const Game *g = vm->g;
    const u8 *code = g->code;
    NEED(17);
    u32 spec = U32(), as = U32();
    s32 z = S32();
    u32 behind = U32();
    u8 n = U8();
    NEED(4u * n);
    s32 atl[8];
    int natl = 0;
    for (int i = 0; i < n; i++) {
        s32 a = S32();
        if (natl < 8)
            atl[natl++] = a;
    }
    if (scene)
        eng_scene(game_str(g, spec), game_str(g, as), z, game_str(g, behind), atl, natl);
    else if (spec != NONE_STR)
        eng_show(game_str(g, spec), game_str(g, as), z, game_str(g, behind), atl, natl, false);
}

/* Test hook: the desktop runner stops a recording when the script reaches a
 * label (e.g. the next chapter). */
s32 vm_watch_addr = -1;
bool vm_watch_hit;

static void step(VM *vm)
{
    const Game *g = vm->g;
    const u8 *code = g->code;
    if (vm->pc >= g->code_size) {
        fail(vm, "jumped outside the script");
        return;
    }
    u32 at = vm->pc;
    if ((s32)at == vm_watch_addr)
        vm_watch_hit = true;
    u8 op = code[vm->pc++];
    switch (op) {
    case OP_NOP: break;
    case OP_END: vm->state = VM_ENDED; break;
    case OP_JMP: NEED(4); vm->pc = U32(); break;
    case OP_JZ:
    case OP_JNZ: {
        NEED(4);
        u32 addr = U32();
        Value v = pop(vm);
        if (truthy(&v) == (op == OP_JNZ))
            vm->pc = addr;
        value_free(&v);
        break;
    }
    case OP_CALL:
        NEED(4);
        if (vm->ncalls >= VM_CALLS) {
            fail(vm, "call stack overflow (too deep recursion)");
            break;
        }
        vm->calls[vm->ncalls++] = vm->pc + 4;
        vm->pc = U32();
        break;
    case OP_RET:
        if (vm->ncalls == 0)
            vm->state = VM_ENDED;
        else
            vm->pc = vm->calls[--vm->ncalls];
        break;
    case OP_POP: {
        Value v = pop(vm);
        value_free(&v);
        break;
    }
    case OP_DUP:
        if (vm->sp <= 0) {
            fail(vm, "stack underflow");
            break;
        }
        push(vm, v_copy(&vm->stack[vm->sp - 1]));
        break;
    case OP_PUSH_NUM: NEED(8); push(vm, v_num(rd_f64(code + vm->pc))); vm->pc += 8; break;
    case OP_PUSH_STR: NEED(4); push(vm, v_str(game_str(g, U32()))); break;
    case OP_PUSH_NONE: { Value v = {VAL_NONE, 0, NULL}; push(vm, v); break; }
    case OP_PUSH_TRUE: push(vm, v_bool(true)); break;
    case OP_PUSH_FALSE: push(vm, v_bool(false)); break;
    case OP_LOAD: {
        NEED(4);
        u32 i = U32();
        if (i >= g->nvars) {
            fail(vm, "bad variable");
            break;
        }
        push(vm, v_copy(&vm->vars[i]));
        break;
    }
    case OP_STORE: {
        NEED(4);
        u32 i = U32();
        Value v = pop(vm);
        if (i >= g->nvars) {
            value_free(&v);
            fail(vm, "bad variable");
            break;
        }
        value_free(&vm->vars[i]);
        vm->vars[i] = v;
        break;
    }
    case OP_ADD: case OP_SUB: case OP_MUL: case OP_DIV:
    case OP_FLOORDIV: case OP_MOD: case OP_POW:
        binop(vm, op);
        break;
    case OP_NEG: {
        Value v = pop(vm);
        double x = as_num(&v);
        value_free(&v);
        push(vm, v_num(-x));
        break;
    }
    case OP_NOT: {
        Value v = pop(vm);
        bool t = truthy(&v);
        value_free(&v);
        push(vm, v_bool(!t));
        break;
    }
    case OP_EQ: case OP_NE: case OP_LT: case OP_LE: case OP_GT: case OP_GE:
        compare(vm, op);
        break;
    case OP_CALLF: {
        NEED(2);
        u8 fn = U8(), n = U8();
        callf(vm, fn, n);
        break;
    }
    case OP_IN: {
        Value b = pop(vm), a = pop(vm);
        bool r = a.type == VAL_STR && b.type == VAL_STR && strstr(b.str, a.str) != NULL;
        value_free(&a);
        value_free(&b);
        push(vm, v_bool(r));
        break;
    }
    case OP_SAY: {
        NEED(13);
        s32 ch = S32();
        u32 who = U32(), what = U32();
        u8 flags = U8();
        do_say(vm, at, ch, who, what, flags);
        eng_say_begin();
        vm->state = VM_SAY;
        break;
    }
    case OP_MENU_BEGIN:
        vm->nchoices = 0;
        vm->menu_begin_pc = at;
        break;
    case OP_MENU_ITEM: {
        NEED(8);
        u32 text = U32(), addr = U32();
        Value v = pop(vm);
        if (truthy(&v) && vm->nchoices < VM_CHOICES) {
            Choice *c = &vm->choices[vm->nchoices++];
            vm_interpolate(vm, game_str(g, text) ? game_str(g, text) : "", c->text, sizeof(c->text));
            c->addr = addr;
        }
        value_free(&v);
        break;
    }
    case OP_MENU: {
        NEED(12);
        s32 ch = S32();
        u32 who = U32(), caption = U32();
        if (vm->nchoices == 0)
            break; /* nothing to pick: Ren'Py skips the menu */
        if (caption != NONE_STR) {
            do_say(vm, at, ch, who, caption, 0);
            eng_say_begin();
        } else {
            vm->say_char = 0;
            vm->say_who[0] = 0;
            vm->say_text[0] = 0;
        }
        vm->resume_pc = vm->menu_begin_pc;
        vm->state = VM_MENU;
        break;
    }
    case OP_PAUSE: {
        NEED(1);
        u8 has_time = U8();
        vm->pause_time = -1;
        if (has_time) {
            Value v = pop(vm);
            if (v.type == VAL_NUM || v.type == VAL_BOOL)
                vm->pause_time = (float)v.num;
            value_free(&v);
        }
        vm->resume_pc = vm->pc; /* loading a save skips the pause */
        vm->state = VM_PAUSE;
        break;
    }
    case OP_SCENE: read_show(vm, true); break;
    case OP_SHOW: read_show(vm, false); break;
    case OP_HIDE: NEED(4); eng_hide(game_str(g, U32())); break;
    case OP_WITH: {
        NEED(4);
        s32 t = S32();
        vm->with_trans = t;
        if (eng_with(t))
            vm->state = VM_WITH;
        break;
    }
    case OP_SHOW_ATTR: {
        NEED(4);
        const char *spec = game_str(g, U32());
        if (spec)
            eng_show(spec, NULL, ZORDER_KEEP, NULL, NULL, 0, true);
        break;
    }
    case OP_PLAY: {
        NEED(14);
        u8 ch = U8();
        s32 res = S32();
        u8 flags = U8();
        float fi = F32(), fo = F32();
        eng_play(ch, res, flags, fi, fo);
        break;
    }
    case OP_STOP: {
        NEED(5);
        u8 ch = U8();
        float fo = F32();
        eng_stop(ch, fo);
        break;
    }
    case OP_WINDOW: NEED(1); eng_window(U8()); break;
    case OP_MINIGAME: {
        Value v = pop(vm);
        snprintf(vm->mg_id, sizeof(vm->mg_id), "%s", v.type == VAL_STR ? v.str : "");
        value_free(&v);
        vm->state = VM_GAME;
        break;
    }
    default: fail(vm, "unknown opcode %02x", op); break;
    }
}

void vm_run(VM *vm)
{
    /* Bounded so a runaway `while` can't hang the console. */
    for (int i = 0; i < 2000000 && vm->state == VM_RUNNING; i++)
        step(vm);
    if (vm->state == VM_RUNNING)
        fail(vm, "the script ran for too long without showing anything (infinite loop?)");
}

bool vm_new_game_at(VM *vm, u32 addr)
{
    s32 start = game_label(vm->g, "start");
    if (start < 0)
        return false;
    vm_new_game(vm);
    for (int i = 0; i < 2000000 && vm->state == VM_RUNNING && vm->pc != (u32)start; i++)
        step(vm);
    if (vm->state != VM_RUNNING)
        return false;
    vm->pc = addr;
    return true;
}

void vm_choose(VM *vm, int choice)
{
    if (vm->state != VM_MENU || choice < 0 || choice >= vm->nchoices)
        return;
    vm->pc = vm->choices[choice].addr;
    vm->state = VM_RUNNING;
}

void vm_minigame_done(VM *vm, int score)
{
    if (vm->state != VM_GAME)
        return;
    push(vm, v_num(score));
    vm->state = VM_RUNNING;
}

void vm_resume(VM *vm)
{
    if (vm->state == VM_SAY || vm->state == VM_PAUSE || vm->state == VM_WITH)
        vm->state = VM_RUNNING;
}
