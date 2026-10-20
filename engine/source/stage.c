#include "stage.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void xform_default(XForm *xf)
{
    memset(xf, 0, sizeof(*xf));
    /* Ren'Py's default transform: bottom centre. */
    xf->v[P_XPOS] = 0.5f;
    xf->v[P_YPOS] = 1.0f;
    xf->v[P_XANCHOR] = 0.5f;
    xf->v[P_YANCHOR] = 1.0f;
    xf->v[P_XZOOM] = 1.0f;
    xf->v[P_YZOOM] = 1.0f;
    xf->v[P_ZOOM] = 1.0f;
    xf->v[P_ALPHA] = 1.0f;
}

void stage_clear(Stage *st)
{
    st->n = 0;
}

int stage_find(const Stage *st, const char *tag)
{
    for (int i = 0; i < st->n; i++)
        if (strcmp(st->s[i].tag, tag) == 0)
            return i;
    return -1;
}

static bool has_attr(const ImageDef *im, const char *a, size_t len)
{
    for (int i = 0; i < im->nattrs; i++)
        if (strlen(im->attrs[i]) == len && memcmp(im->attrs[i], a, len) == 0)
            return true;
    return false;
}

typedef struct {
    const char *p;
    size_t len;
} Word;

static int split(const char *s, Word *out, int max)
{
    int n = 0;
    while (*s && n < max) {
        while (*s == ' ')
            s++;
        if (!*s)
            break;
        const char *b = s;
        while (*s && *s != ' ')
            s++;
        out[n].p = b;
        out[n].len = (size_t)(s - b);
        n++;
    }
    return n;
}

/* Ren'Py-style attribute resolution: the image must carry every requested
 * attribute; among those, prefer keeping the currently shown attributes and
 * having as few extra ones as possible. */
s32 stage_resolve(const Game *g, const char *spec, const Sprite *current)
{
    Word w[MAX_ATTRS + 1];
    int nw = split(spec, w, MAX_ATTRS + 1);
    if (nw == 0)
        return -1;
    const ImageDef *cur = NULL;
    if (current && current->image >= 0 && (u32)current->image < g->nimages) {
        cur = &g->images[current->image];
        if (strlen(cur->tag) != w[0].len || memcmp(cur->tag, w[0].p, w[0].len) != 0)
            cur = NULL;
    }
    int nwant = 0;
    for (int i = 1; i < nw; i++)
        if (w[i].p[0] != '-')
            nwant++;
    if (cur && nwant == 0) {
        bool removes_current = false;
        for (int i = 1; i < nw; i++)
            if (w[i].p[0] == '-' && has_attr(cur, w[i].p + 1, w[i].len - 1))
                removes_current = true;
        if (!removes_current)
            return current->image;
    }

    s32 best = -1;
    int best_score = -1000000;
    for (u32 i = 0; i < g->nimages; i++) {
        const ImageDef *im = &g->images[i];
        if (strlen(im->tag) != w[0].len || memcmp(im->tag, w[0].p, w[0].len) != 0)
            continue;
        bool ok = true;
        for (int k = 1; k < nw && ok; k++) {
            if (w[k].p[0] == '-')
                ok = !has_attr(im, w[k].p + 1, w[k].len - 1);
            else
                ok = has_attr(im, w[k].p, w[k].len);
        }
        if (!ok)
            continue;
        int score = 0;
        for (int a = 0; a < im->nattrs; a++) {
            const char *at = im->attrs[a];
            bool wanted = false;
            for (int k = 1; k < nw; k++)
                if (w[k].p[0] != '-' && strlen(at) == w[k].len && memcmp(at, w[k].p, w[k].len) == 0)
                    wanted = true;
            if (wanted)
                continue;
            if (cur && has_attr(cur, at, strlen(at)))
                score += 10;
            else
                score -= 1;
        }
        if (score > best_score) {
            best_score = score;
            best = (s32)i;
        }
    }
    return best;
}

static void runner_reset(AtlRunner *r, s16 prog)
{
    memset(r, 0, sizeof(*r));
    r->prog = prog;
}

static float warp(int w, float t)
{
    switch (w) {
    case 1: return 0.5f - cosf((float)M_PI * t) / 2.0f;
    case 2: return cosf((1.0f - t) * (float)M_PI / 2.0f);
    case 3: return 1.0f - cosf(t * (float)M_PI / 2.0f);
    default: return t;
    }
}

static float image_vsize(const Game *g, const Sprite *s, int axis)
{
    const ImageDef *im = &g->images[s->image];
    float z = s->xf.v[P_ZOOM] * s->xf.v[axis ? P_YZOOM : P_XZOOM];
    return (axis ? im->h : im->w) / g->scale * fabsf(z);
}

/* Current value of a property expressed in the requested unit. */
static float prop_as(const Game *g, const Sprite *s, int prop, int want_abs)
{
    float v = s->xf.v[prop];
    if (prop > P_YANCHOR || s->xf.abs[prop] == want_abs)
        return v;
    float size;
    switch (prop) {
    case P_XPOS: size = g->game_w; break;
    case P_YPOS: size = g->game_h; break;
    case P_XANCHOR: size = image_vsize(g, s, 0); break;
    default: size = image_vsize(g, s, 1); break;
    }
    if (want_abs)
        return v * size;
    return size > 0 ? v / size : 0;
}

static void set_prop(Sprite *s, int prop, int is_abs, float v)
{
    s->xf.v[prop] = v;
    if (prop <= P_YANCHOR)
        s->xf.abs[prop] = (u8)is_abs;
    if (prop == P_ZPOS)
        s->xf.zpos_set = 1;
}

static void runner_update(Sprite *s, AtlRunner *r, const Game *g, float dt)
{
    if (r->done || r->prog < 0 || (u32)r->prog >= g->natl) {
        r->done = 1;
        return;
    }
    const AtlProg *p = &g->atl[r->prog];
    for (int guard = 0; guard < 64; guard++) {
        if (r->step >= p->nsteps) {
            r->done = 1;
            return;
        }
        const AtlStep *st = &p->steps[r->step];
        int np = st->nprops < MAX_STEP_PROPS ? st->nprops : MAX_STEP_PROPS;
        switch (st->kind) {
        case STEP_SET:
            for (int i = 0; i < np; i++) {
                const u8 *pp = st->props + 8 * i;
                if (pp[0] < P_COUNT)
                    set_prop(s, pp[0], pp[1], rd_f32(pp + 4));
            }
            r->step++;
            break;
        case STEP_PAUSE:
            r->t += dt;
            dt = 0;
            if (r->t < st->dur)
                return;
            dt = r->t - st->dur;
            r->t = 0;
            r->step++;
            break;
        case STEP_INTERP: {
            if (!r->started) {
                for (int i = 0; i < np; i++) {
                    const u8 *pp = st->props + 8 * i;
                    r->from[i] = pp[0] < P_COUNT ? prop_as(g, s, pp[0], pp[1]) : 0;
                }
                r->started = 1;
                r->t = 0;
            }
            r->t += dt;
            dt = 0;
            float f = st->dur > 0 ? clampf(r->t / st->dur, 0, 1) : 1;
            float k = warp(st->warper, f);
            for (int i = 0; i < np; i++) {
                const u8 *pp = st->props + 8 * i;
                if (pp[0] < P_COUNT)
                    set_prop(s, pp[0], pp[1], lerpf(r->from[i], rd_f32(pp + 4), k));
            }
            if (f < 1)
                return;
            dt = r->t - st->dur;
            r->t = 0;
            r->started = 0;
            r->step++;
            break;
        }
        case STEP_REPEAT:
            if (st->count == 0) {
                r->step = st->target;
            } else {
                if (!r->repeat_armed) {
                    r->repeat_left = st->count;
                    r->repeat_armed = 1;
                }
                if (r->repeat_left > 0) {
                    r->repeat_left--;
                    r->step = st->target;
                } else {
                    r->repeat_armed = 0;
                    r->step++;
                }
            }
            /* A loop that takes no time would spin forever. */
            if (dt <= 0 && r->step == st->target && guard > 32)
                return;
            break;
        default:
            r->step++;
            break;
        }
    }
}

bool stage_show(Stage *st, const Game *g, const char *spec, const char *as_tag, s32 zorder,
                const char *behind, const s32 *atl, int natl, bool only_if_shown, bool from_scene)
{
    char key[32];
    if (as_tag) {
        snprintf(key, sizeof(key), "%s", as_tag);
    } else {
        size_t n = strcspn(spec, " ");
        if (n >= sizeof(key))
            n = sizeof(key) - 1;
        memcpy(key, spec, n);
        key[n] = 0;
    }
    int idx = stage_find(st, key);
    if (only_if_shown && idx < 0)
        return true;
    s32 image = stage_resolve(g, spec, idx >= 0 ? &st->s[idx] : NULL);
    if (image < 0) {
        LOG("image '%s' not found", spec);
        return false;
    }
    Sprite *s;
    if (idx < 0) {
        if (st->n >= MAX_SPRITES) {
            LOG("too many images on screen");
            return false;
        }
        s = &st->s[st->n++];
        memset(s, 0, sizeof(*s));
        snprintf(s->tag, sizeof(s->tag), "%s", key);
        xform_default(&s->xf);
        s->zorder = zorder == ZORDER_KEEP ? 0 : zorder;
        st->next_order += 1024;
        s->order = st->next_order;
    } else {
        s = &st->s[idx];
        if (zorder != ZORDER_KEEP)
            s->zorder = zorder;
    }
    s->image = image;
    s->from_scene = from_scene;
    if (natl > 0) {
        if (natl > MAX_RUNNERS)
            natl = MAX_RUNNERS;
        s->natl = (u8)natl;
        for (int i = 0; i < natl; i++)
            runner_reset(&s->atl[i], (s16)atl[i]);
    }
    if (behind) {
        int b = stage_find(st, behind);
        if (b >= 0 && &st->s[b] != s) {
            s->zorder = st->s[b].zorder;
            s->order = st->s[b].order - 1;
        }
    }
    for (int i = 0; i < s->natl; i++)
        runner_update(s, &s->atl[i], g, 0);
    return true;
}

void stage_hide(Stage *st, const char *tag)
{
    int idx = stage_find(st, tag);
    if (idx < 0)
        return;
    memmove(&st->s[idx], &st->s[idx + 1], sizeof(Sprite) * (size_t)(st->n - idx - 1));
    st->n--;
}

void stage_update(Stage *st, const Game *g, float dt)
{
    for (int i = 0; i < st->n; i++) {
        Sprite *s = &st->s[i];
        for (int k = 0; k < s->natl; k++)
            runner_update(s, &s->atl[k], g, dt);
    }
}

int stage_order(const Stage *st, const Sprite **out)
{
    int n = 0;
    for (int i = 0; i < st->n; i++) {
        const Sprite *s = &st->s[i];
        int j = n++;
        while (j > 0 && (out[j - 1]->zorder > s->zorder ||
                         (out[j - 1]->zorder == s->zorder && out[j - 1]->order > s->order))) {
            out[j] = out[j - 1];
            j--;
        }
        out[j] = s;
    }
    return n;
}

void sprite_rect(const Game *g, const Sprite *s, SpriteRect *r)
{
    const ImageDef *im = &g->images[s->image];
    const float *v = s->xf.v;
    float zx = v[P_ZOOM] * v[P_XZOOM], zy = v[P_ZOOM] * v[P_YZOOM];
    float w = im->w * fabsf(zx), h = im->h * fabsf(zy);
    float sc = g->scale;
    float xpos = s->xf.abs[0] ? v[P_XPOS] * sc : v[P_XPOS] * g->view_w;
    float ypos = s->xf.abs[1] ? v[P_YPOS] * sc : v[P_YPOS] * g->view_h;
    float xa = s->xf.abs[2] ? v[P_XANCHOR] * sc : v[P_XANCHOR] * w;
    float ya = s->xf.abs[3] ? v[P_YANCHOR] * sc : v[P_YANCHOR] * h;
    r->x = g->view_x + xpos - xa + v[P_XOFFSET] * sc;
    r->y = g->view_y + ypos - ya + v[P_YOFFSET] * sc;
    r->w = zx < 0 ? -w : w;
    r->h = zy < 0 ? -h : h;
    r->angle = v[P_ROTATE] * (float)M_PI / 180.0f;
    r->alpha = clampf(v[P_ALPHA], 0, 1);
}

float sprite_depth(const Game *g, const Sprite *s, int rank)
{
    if (s->xf.zpos_set)
        return clampf(-s->xf.v[P_ZPOS] / 300.0f, -1.0f, 2.0f);
    const ImageDef *im = &g->images[s->image];
    if (!isnan(im->depth))
        return im->depth;
    if ((im->flags & IMG_FULLSCREEN) || s->from_scene)
        return g->depth_bg;
    return g->depth_sprite - 0.05f * (float)(rank < 4 ? rank : 4);
}
