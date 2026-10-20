#include "app.h"
#include "video.h"

/* Stereoscopy: every element has a depth (positive = behind the screen,
 * negative = in front). Each eye's copy is shifted horizontally by
 * depth * strength, in opposite directions, where strength comes from the
 * 3D slider. Behind-screen layers get uncrossed disparity (left eye image to
 * the left), in-front layers crossed disparity. */

static inline float eye_sign(int eye)
{
    return eye == EYE_LEFT ? -1.0f : 1.0f;
}

static float warp(int w, float t)
{
    switch (w) {
    case 1: return 0.5f - cosf(3.14159265f * t) / 2.0f;
    case 2: return cosf((1.0f - t) * 3.14159265f / 2.0f);
    case 3: return 1.0f - cosf(t * 3.14159265f / 2.0f);
    default: return t;
    }
}

/* The drifting camera: a slow pan and a slight zoom "breath". Elements move
 * by their parallax factor, so far layers barely move and near ones move
 * most, which makes depth readable even with the 3D slider down. */
static float parallax(float depth)
{
    return 1.0f / (1.0f + 0.55f * fmaxf(depth, -0.8f));
}

static void camera(float depth, float *cx, float *cy, float *zoom)
{
    const Game *g = &E.game;
    *cx = *cy = 0;
    *zoom = 1;
    if (g->cam_drift <= 0 || g->cam_period <= 0)
        return;
    float t = E.time * 6.2831853f / g->cam_period;
    float p = parallax(depth);
    *cx = g->cam_drift * p * sinf(t);
    *cy = g->cam_drift * 0.45f * p * sinf(t * 0.73f + 1.1f);
    *zoom = 1.0f + g->cam_zoom * p * (0.5f + 0.5f * sinf(t * 0.51f));
}

/* Apply the camera to a box around the screen centre. */
static void cam_box(float depth, float *x, float *y, float *w, float *h)
{
    float cx, cy, z;
    camera(depth, &cx, &cy, &z);
    if (z == 1 && cx == 0 && cy == 0)
        return;
    float mx = TOP_W / 2.0f, my = TOP_H / 2.0f;
    *x = mx + (*x - mx) * z + cx;
    *y = my + (*y - my) * z + cy;
    *w *= z;
    *h *= z;
}

void render_sprite(const Sprite *s, int eye, int rank, float dx, float dy)
{
    const Game *g = &E.game;
    if (s->image < 0 || (u32)s->image >= g->nimages)
        return;
    const ImageDef *im = &g->images[s->image];
    SpriteRect r;
    sprite_rect(g, s, &r);
    if (r.alpha <= 0.0f)
        return;
    r.x += dx + E.punch_x;
    r.y += dy + E.punch_y;
    float depth = sprite_depth(g, s, rank);
    float strength = app_strength();

    /* A picture that spans the whole width would show a black strip on one
     * side once shifted; enlarge it just enough to cover the largest shift.
     * Layered pictures use their deepest full-width layer and scale every
     * layer together so they stay aligned. */
    float aw = fabsf(r.w), ah = fabsf(r.h);
    float edge_depth = fabsf(depth);
    if (im->nlayers) {
        edge_depth = 0;
        for (int k = 0; k < im->nlayers; k++)
            if (im->layers[k].w >= im->w * 0.98f)
                edge_depth = fmaxf(edge_depth, fabsf(im->layers[k].depth));
    }
    if (edge_depth > 0 && r.x <= 0.5f && r.x + aw >= TOP_W - 0.5f) {
        float m = edge_depth * g->max_shift * 2.0f + g->cam_drift * 1.3f + TOP_W * g->cam_zoom;
        float cx = TOP_W / 2.0f;
        float need = fmaxf((cx + m) / (cx - r.x), (TOP_W - cx + m) / (r.x + aw - cx));
        if (need > 1.0f) {
            float cy = r.y + ah / 2.0f;
            r.x = cx - (cx - r.x) * need;
            r.y = cy - (cy - r.y) * need;
            r.w *= need;
            r.h *= need;
            aw *= need;
            ah *= need;
        }
    }

    if (im->nlayers) {
        float sx = aw / im->w, sy = ah / im->h;
        for (int k = 0; k < im->nlayers; k++) {
            const ImageLayer *L = &im->layers[k];
            GfxTex *tex = texcache_get(L->res);
            if (!tex)
                continue;
            float lshift = eye_sign(eye) * L->depth * strength;
            float lx = r.x + L->x * sx, ly = r.y + L->y * sy;
            float lw = L->w * sx, lh = L->h * sy, la = r.alpha;
            cam_box(L->depth, &lx, &ly, &lw, &lh);
            lx += lshift;
            float ph = L->period > 0 ? E.time * 6.2831853f / L->period : 0;
            switch (L->anim) {
            case ANIM_SWAY:
                lx += L->a * sx * sinf(ph);
                ly += L->b * sy * sinf(ph * 0.5f + 1.3f);
                break;
            case ANIM_PULSE:
                la *= L->a + (1.0f - L->a) * (0.5f + 0.5f * sinf(ph));
                break;
            case ANIM_BREATHE: {
                float k2 = 1.0f + L->a * (0.5f + 0.5f * sinf(ph));
                lx -= lw * (k2 - 1) / 2;
                ly -= lh * (k2 - 1);
                lw *= k2;
                lh *= k2;
                break;
            }
            case ANIM_FALL:
            case ANIM_RISE: {
                /* Seamless loop: draw the layer twice, one loop-length apart. */
                float dist = L->a * sy;
                float off = fmodf(E.time / L->period, 1.0f) * dist;
                if (L->anim == ANIM_RISE)
                    off = -off;
                float back = L->anim == ANIM_RISE ? dist : -dist;
                gfx_image(tex, lx, ly + off + back, lw, lh, r.angle, la);
                ly += off;
                break;
            }
            }
            gfx_image(tex, lx, ly, lw, lh, r.angle, la);
        }
        return;
    }

    float shift = eye_sign(eye) * depth * strength;
    {
        float aw0 = fabsf(r.w), ah0 = fabsf(r.h);
        float x0 = r.x, y0 = r.y;
        cam_box(depth, &x0, &y0, &aw0, &ah0);
        float k = fabsf(r.w) > 0 ? aw0 / fabsf(r.w) : 1;
        r.x = x0;
        r.y = y0;
        r.w *= k;
        r.h *= k;
        aw = fabsf(r.w);
        ah = fabsf(r.h);
    }
    if (im->flags & IMG_SOLID) {
        gfx_rect(r.x + shift, r.y, aw, ah, rgba_alpha(im->color, r.alpha));
        return;
    }
    GfxTex *tex = (im->flags & IMG_VIDEO) ? video_tex(im->res) : texcache_get(im->res);
    if (tex)
        gfx_image(tex, r.x + shift, r.y, r.w, r.h, r.angle, r.alpha);
}

void render_stage(const Stage *st, int eye, const float (*off)[2], float offk)
{
    const Sprite *order[MAX_SPRITES];
    int n = stage_order(st, order);
    int rank = 0;
    for (int i = 0; i < n; i++) {
        const Sprite *s = order[i];
        float dx = 0, dy = 0;
        if (off) {
            ptrdiff_t idx = s - st->s;
            dx = off[idx][0] * offk;
            dy = off[idx][1] * offk;
        }
        render_sprite(s, eye, rank, dx, dy);
        const ImageDef *im = &E.game.images[s->image];
        if (!(im->flags & IMG_FULLSCREEN) && !s->from_scene)
            rank++;
    }
}

void render_scene(int eye)
{
    const Transition *tr = &E.tr;
    if (!tr->active) {
        render_stage(&E.stage, eye, NULL, 0);
        return;
    }
    const TransDef *d = tr->def;
    float p = tr->dur > 0 ? clampf(tr->t / tr->dur, 0, 1) : 1;
    switch (d->type) {
    case TR_DISSOLVE:
        render_stage(&E.stage, eye, NULL, 0);
        gfx_draw_capture(eye, 1.0f - p);
        break;
    case TR_FADE: {
        float t = tr->t;
        u32 color = d->color;
        if (t < d->a) {
            render_stage(&tr->old, eye, NULL, 0);
            gfx_rect(0, 0, TOP_W, TOP_H, rgba_alpha(color, d->a > 0 ? t / d->a : 1));
        } else if (t < d->a + d->b) {
            gfx_rect(0, 0, TOP_W, TOP_H, rgba_alpha(color, 1));
        } else {
            render_stage(&E.stage, eye, NULL, 0);
            float k = d->c > 0 ? (t - d->a - d->b) / d->c : 1;
            gfx_rect(0, 0, TOP_W, TOP_H, rgba_alpha(color, 1.0f - clampf(k, 0, 1)));
        }
        break;
    }
    case TR_MOVE:
    case TR_MOVEIN:
    case TR_MOVEOUT: {
        float k = warp(d->warper, p);
        render_stage(&E.stage, eye, tr->off, 1.0f - k);
        for (int i = 0; i < tr->nleaving; i++)
            render_sprite(&tr->old.s[tr->leaving[i]], eye, 0, tr->loff[i][0] * k,
                          tr->loff[i][1] * k);
        break;
    }
    default:
        render_stage(&E.stage, eye, NULL, 0);
        break;
    }
}
