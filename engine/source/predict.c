/* Looking ahead in the script, to load what it will need before it is
 * needed: the pictures of the next `scene` / `show` statements and the next
 * music.
 *
 * The scan reads the bytecode from where the VM stopped without running
 * it: it follows jumps and calls (and returns, through the VM's own call
 * stack), takes both sides of every condition and every menu choice, and
 * stops each path after a few more lines of dialogue. Paths are explored
 * breadth first, so what is nearest comes first in the lists. It is cheap
 * (a few thousand instructions at most) and bounded, and it never changes
 * the VM. */

#include "predict.h"

#include "stage.h"

enum {
    OP_NOP = 0x00, OP_END, OP_JMP, OP_JZ, OP_JNZ, OP_CALL, OP_RET, OP_POP, OP_DUP,
    OP_PUSH_NUM = 0x10, OP_PUSH_STR, OP_PUSH_NONE, OP_PUSH_TRUE, OP_PUSH_FALSE, OP_LOAD, OP_STORE,
    OP_ADD = 0x20, OP_NOT = 0x28,
    OP_EQ = 0x2A, OP_GE = 0x2F, OP_CALLF = 0x30, OP_IN = 0x31,
    OP_SAY = 0x40, OP_MENU_BEGIN, OP_MENU_ITEM, OP_MENU, OP_PAUSE, OP_SCENE, OP_SHOW, OP_HIDE,
    OP_WITH, OP_SHOW_ATTR,
    OP_PLAY = 0x50, OP_STOP, OP_WINDOW, OP_MINIGAME,
};

#define MAX_PATHS 48
#define MAX_LOCAL 8
#define MAX_INSNS 6000
#define SEEN 1024   /* (a power of two) */

typedef struct {
    u32 pc;
    u8 dist;        /* interactions (lines, menus, click pauses) passed */
    u8 nlocal;      /* calls made on this path */
    u8 base;        /* returns taken through the VM's own call stack */
    u32 local[MAX_LOCAL];
} Path;

/* What a tag shows along the way, for statements that only change
 * attributes ("show aron smile"). */
typedef struct {
    char tag[32];
    s32 image;
} TagImg;

typedef struct {
    const VM *vm;
    const Game *g;
    const Stage *st;
    Prediction *out;
    int max_dist;
    TagImg tags[MAX_SPRITES];
    int ntags;
    u32 seen[SEEN];
    Path q[MAX_PATHS];
    int qh, qt;
} Scan;

static bool seen(Scan *s, u32 pc, u8 dist)
{
    /* keyed by address and distance: a nearer visit wins */
    u32 key = (pc << 4) | (dist & 15);
    u32 h = (pc * 2654435761u) & (SEEN - 1);
    for (int k = 0; k < 16; k++) {
        u32 *slot = &s->seen[(h + (u32)k) & (SEEN - 1)];
        if (*slot == key + 1)
            return true;
        if (*slot == 0) {
            *slot = key + 1;
            return false;
        }
    }
    return false;
}

static void push(Scan *s, const Path *p)
{
    if (s->qt - s->qh >= MAX_PATHS || p->dist > s->max_dist || seen(s, p->pc, p->dist))
        return;
    s->q[s->qt % MAX_PATHS] = *p;
    s->qt++;
}

static TagImg *tag_slot(Scan *s, const char *tag)
{
    for (int i = 0; i < s->ntags; i++)
        if (!strcmp(s->tags[i].tag, tag))
            return &s->tags[i];
    if (s->ntags >= MAX_SPRITES)
        return NULL;
    TagImg *t = &s->tags[s->ntags++];
    snprintf(t->tag, sizeof(t->tag), "%s", tag);
    t->image = -1;
    return t;
}

static void add_image(Scan *s, const char *spec, const char *as_tag, bool scene, u8 dist)
{
    if (!spec)
        return;
    char tag[32];
    if (as_tag) {
        snprintf(tag, sizeof(tag), "%s", as_tag);
    } else {
        size_t n = strcspn(spec, " ");
        if (n >= sizeof(tag))
            n = sizeof(tag) - 1;
        memcpy(tag, spec, n);
        tag[n] = 0;
    }
    if (scene)
        s->ntags = 0;
    TagImg *t = tag_slot(s, tag);
    Sprite cur;
    memset(&cur, 0, sizeof(cur));
    cur.image = t ? t->image : -1;
    s32 im = stage_resolve(s->g, spec, cur.image >= 0 ? &cur : NULL);
    if (im < 0)
        return;
    if (t)
        t->image = im;
    Prediction *o = s->out;
    for (int i = 0; i < o->nimages; i++)
        if (o->images[i] == im)
            return;
    if (o->nimages < PREDICT_MAX_IMAGES) {
        o->images[o->nimages] = im;
        o->image_dist[o->nimages] = dist;
        o->nimages++;
    }
}

/* The mouth-open frame of the speaker's sprite (talk.c flaps between it
 * and the sprite while the line types out). */
static void add_talk(Scan *s, s32 ch, u8 dist)
{
    const Game *g = s->g;
    if (!g->speaking_attr || ch < 0 || (u32)ch >= g->nchars || !g->chars[ch].image_tag)
        return;
    const char *tag = g->chars[ch].image_tag;
    s32 cur = -1;
    for (int i = 0; i < s->ntags; i++)
        if (!strcmp(s->tags[i].tag, tag))
            cur = s->tags[i].image;
    if (cur < 0 || (u32)cur >= g->nimages)
        return;
    const ImageDef *im = &g->images[cur];
    char spec[160];
    size_t o = (size_t)snprintf(spec, sizeof(spec), "%s", im->tag);
    for (int i = 0; i < im->nattrs && o < sizeof(spec); i++)
        o += (size_t)snprintf(spec + o, sizeof(spec) - o, " %s", im->attrs[i]);
    snprintf(spec + o, sizeof(spec) - o, " %s", g->speaking_attr);
    Sprite sp;
    memset(&sp, 0, sizeof(sp));
    sp.image = cur;
    s32 talk = stage_resolve(g, spec, &sp);
    if (talk < 0 || talk == cur || g->images[talk].nattrs != im->nattrs + 1)
        return;
    Prediction *out = s->out;
    for (int i = 0; i < out->nimages; i++)
        if (out->images[i] == talk)
            return;
    if (out->nimages < PREDICT_MAX_IMAGES) {
        out->images[out->nimages] = talk;
        out->image_dist[out->nimages] = dist;
        out->nimages++;
    }
}

#define NEED(n)                              \
    do {                                     \
        if (p.pc + (n) > g->code_size)       \
            goto next_path;                  \
    } while (0)

static void scan(Scan *s, int max_insns)
{
    const Game *g = s->g;
    const u8 *code = g->code;
    int insns = 0;
    while (s->qh < s->qt && insns < max_insns) {
        Path p = s->q[s->qh % MAX_PATHS];
        s->qh++;
        while (insns++ < max_insns) {
            if (p.pc >= g->code_size)
                break;
            u32 at = p.pc;
            u8 op = code[p.pc++];
            if (op >= OP_ADD && op <= OP_NOT)
                continue;
            if (op >= OP_EQ && op <= OP_GE)
                continue;
            switch (op) {
            case OP_NOP: case OP_POP: case OP_DUP: case OP_PUSH_NONE: case OP_PUSH_TRUE:
            case OP_PUSH_FALSE: case OP_IN: case OP_MENU_BEGIN:
                break;
            case OP_END: goto next_path;
            case OP_JMP:
                NEED(4);
                p.pc = rd_u32(code + p.pc);
                if (seen(s, p.pc, p.dist))
                    goto next_path;
                break;
            case OP_JZ: case OP_JNZ: {
                NEED(4);
                Path b = p;
                b.pc = rd_u32(code + p.pc);
                push(s, &b);
                p.pc += 4;
                break;
            }
            case OP_CALL:
                NEED(4);
                if (p.nlocal >= MAX_LOCAL)
                    goto next_path;
                p.local[p.nlocal++] = p.pc + 4;
                p.pc = rd_u32(code + p.pc);
                break;
            case OP_RET:
                if (p.nlocal > 0) {
                    p.pc = p.local[--p.nlocal];
                } else if (p.base < s->vm->ncalls) {
                    p.pc = s->vm->calls[s->vm->ncalls - 1 - p.base];
                    p.base++;
                } else {
                    goto next_path;
                }
                break;
            case OP_PUSH_NUM: NEED(8); p.pc += 8; break;
            case OP_PUSH_STR: case OP_LOAD: case OP_STORE: case OP_HIDE: case OP_WITH:
                NEED(4);
                p.pc += 4;
                break;
            case OP_CALLF: NEED(2); p.pc += 2; break;
            case OP_SAY:
                NEED(13);
                add_talk(s, rd_s32(code + p.pc), p.dist);
                p.pc += 13;
                if (++p.dist > s->max_dist)
                    goto next_path;
                break;
            case OP_MENU_ITEM: {
                NEED(8);
                Path b = p;
                b.pc = rd_u32(code + p.pc + 4);
                b.dist++;
                push(s, &b);
                p.pc += 8;
                break;
            }
            case OP_MENU: goto next_path;   /* the choices were queued as paths */
            case OP_PAUSE: {
                NEED(1);
                u8 timed = code[p.pc++];
                if (!timed && ++p.dist > s->max_dist)
                    goto next_path;
                break;
            }
            case OP_SCENE: case OP_SHOW: {
                NEED(17);
                u32 spec = rd_u32(code + p.pc), as = rd_u32(code + p.pc + 4);
                u8 n = code[p.pc + 16];
                NEED(17 + 4u * n);
                p.pc += 17 + 4u * n;
                const char *as_tag = game_str(g, as);
                if (as_tag && !strcmp(as_tag, "@camera"))
                    break;
                add_image(s, game_str(g, spec), as_tag, op == OP_SCENE, p.dist);
                break;
            }
            case OP_SHOW_ATTR:
                NEED(4);
                add_image(s, game_str(g, rd_u32(code + p.pc)), NULL, false, p.dist);
                p.pc += 4;
                break;
            case OP_PLAY: {
                NEED(14);
                u8 ch = code[p.pc];
                s32 res = rd_s32(code + p.pc + 1);
                u8 flags = code[p.pc + 5];
                p.pc += 14;
                Prediction *o = s->out;
                if (ch == CH_MUSIC && res >= 0 && o->music_res < 0) {
                    o->music_res = res;
                    o->music_flags = flags;
                    o->music_dist = p.dist;
                }
                break;
            }
            case OP_STOP: NEED(5); p.pc += 5; break;
            case OP_WINDOW: NEED(1); p.pc += 1; break;
            case OP_MINIGAME:
                if (++p.dist > s->max_dist)
                    goto next_path;
                break;
            default:
                (void)at;
                goto next_path;   /* something new: don't guess */
            }
        }
    next_path:;
    }
}

void predict_scan(const VM *vm, const Stage *st, int max_dist, Prediction *out)
{
    static Scan s;   /* (a few KB: not on the stack) */
    memset(&s, 0, sizeof(s));
    memset(out, 0, sizeof(*out));
    out->music_res = -1;
    s.vm = vm;
    s.g = vm->g;
    s.st = st;
    s.out = out;
    s.max_dist = max_dist;
    for (int i = 0; i < st->n; i++) {
        TagImg *t = tag_slot(&s, st->s[i].tag);
        if (t)
            t->image = st->s[i].image;
    }
    if (vm->state == VM_ENDED || vm->state == VM_ERROR || !vm->g->code)
        return;
    Path p;
    memset(&p, 0, sizeof(p));
    p.pc = vm->pc;
    if (vm->state == VM_MENU) {   /* waiting for a choice: the choices are the paths */
        for (int i = 0; i < vm->nchoices; i++) {
            Path b = p;
            b.pc = vm->choices[i].addr;
            push(&s, &b);
        }
    } else {
        push(&s, &p);
    }
    scan(&s, MAX_INSNS);
}
