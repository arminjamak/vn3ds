#include "app.h"
#include "video.h"

/* Stereoscopy: every element has a depth (positive = behind the screen,
 * negative = in front). Each eye's copy is shifted horizontally by
 * depth * strength, in opposite directions, where strength comes from the
 * 3D slider. Behind-screen layers get uncrossed disparity (left eye image to
 * the left), in-front layers crossed disparity. */

/* Below this 3D strength (slider x depth setting) stereo videos play flat. */
#define STEREO_MIN 0.3f

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

/* The stage being drawn: its `camera` statement moves everything. */
static const Stage *cam_stage;

/* Orbiting the camera by one degree moves something at depth 1 this many
 * pixels (and something in front of the screen the other way), which is
 * what makes a turn read as a new angle on the same room. */
#define ORBIT_PX_PER_DEG 7.0f

static void camera(float depth, float *cx, float *cy, float *zoom, float *roll)
{
    const Game *g = &E.game;
    *cx = *cy = *roll = 0;
    *zoom = 1;
    float p = parallax(depth);
    if (g->cam_drift > 0 && g->cam_period > 0) {
        float t = E.time * 6.2831853f / g->cam_period;
        *cx = g->cam_drift * p * sinf(t);
        *cy = g->cam_drift * 0.45f * p * sinf(t * 0.73f + 1.1f);
        *zoom = 1.0f + g->cam_zoom * p * (0.5f + 0.5f * sinf(t * 0.51f));
    }
    if (cam_stage && cam_stage->has_camera) {
        const float *v = cam_stage->camera.xf.v;
        float sc = g->scale;
        /* moving the camera right moves the picture left, near layers most */
        *cx += -v[P_XOFFSET] * sc * p - v[P_YROTATE] * ORBIT_PX_PER_DEG * depth;
        *cy += -v[P_YOFFSET] * sc * p + v[P_XROTATE] * ORBIT_PX_PER_DEG * depth;
        /* zoom is a lens zoom (everything alike); zpos dollies the camera in,
         * so near layers grow faster than far ones */
        float dolly = 1.0f + v[P_ZPOS] / 1000.0f * p * p;
        *zoom *= v[P_ZOOM] * fmaxf(0.2f, dolly);
        *roll = v[P_ROTATE] * 3.14159265f / 180.0f;
    }
}

/* Apply the camera to a box around the screen centre; `angle` gets the roll. */
static void cam_box(float depth, float *x, float *y, float *w, float *h, float *angle)
{
    float cx, cy, z, roll;
    camera(depth, &cx, &cy, &z, &roll);
    if (z == 1 && cx == 0 && cy == 0 && roll == 0)
        return;
    float mx = TOP_W / 2.0f, my = TOP_H / 2.0f;
    float bx = *x + *w / 2, by = *y + *h / 2;   /* box centre */
    float dx = (bx - mx) * z, dy = (by - my) * z;
    if (roll != 0) {
        float c = cosf(roll), s = sinf(roll);
        float rx = dx * c - dy * s, ry = dx * s + dy * c;
        dx = rx;
        dy = ry;
        *angle += roll;
    }
    *w *= z;
    *h *= z;
    *x = mx + dx + cx - *w / 2;
    *y = my + dy + cy - *h / 2;
}

/* How far the camera can push a full-screen picture off an edge right now. */
static float cam_margin(float depth)
{
    float cx, cy, z, roll;
    camera(depth, &cx, &cy, &z, &roll);
    float m = fabsf(cx) + fabsf(cy) * 0.5f + fabsf(sinf(roll)) * TOP_W * 0.35f;
    if (z < 1)
        m += (1 - z) * TOP_W / 2;
    return m;
}

/* A procedural starfield in a layer's box: positions come from the seed, so
 * every showing of the picture gets a slightly different sky. */
static void draw_stars(const ImageLayer *L, float x, float y, float w, float h, float alpha,
                       u32 seed)
{
    u32 r = seed * 2654435761u + 0x9E3779B9u;
    int n = (int)L->a;
    float big = L->b > 0 ? L->b : 2.0f;
    for (int i = 0; i < n && i < 400; i++) {
        r ^= r << 13; r ^= r >> 17; r ^= r << 5;
        float u = (float)(r & 0xFFFF) / 65535.0f, v = (float)(r >> 16) / 65535.0f;
        r ^= r << 13; r ^= r >> 17; r ^= r << 5;
        float sz = 0.8f + big * ((r & 0xFF) / 255.0f) * ((r & 0xFF) / 255.0f);
        float tw = 0.55f + 0.45f * sinf(E.time * (0.7f + (float)((r >> 8) & 0xFF) / 120.0f) +
                                       (float)(r >> 20));
        u8 warm = (u8)((r >> 4) & 0x3F);
        gfx_rect(x + u * w, y + v * h, sz, sz,
                 RGBA(255 - warm / 3, 245 - warm / 4, 230 + warm / 3, (u8)(255 * alpha * tw)));
    }
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
        float m = edge_depth * g->max_shift * 2.0f + g->cam_drift * 1.3f + TOP_W * g->cam_zoom +
                  cam_margin(edge_depth) + 2;
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
            GfxTex *tex = NULL;
            if (L->anim == ANIM_VIDEO) {
                /* A stereo clip's own relief (rendered with parallel
                 * cameras: far things line up, near ones come forward) sits
                 * on top of the layer's depth; with the 3D low it plays flat. */
                float mid;
                if (g->max_shift > 0 && strength / g->max_shift >= STEREO_MIN)
                    tex = video_tex_stereo(L->res, eye, &mid);
                if (!tex)
                    tex = video_tex(L->res);
            } else if (L->anim != ANIM_STARS) {
                tex = texcache_get(L->res);
            }
            if (!tex && L->anim != ANIM_STARS)
                continue;
            float lshift = eye_sign(eye) * L->depth * strength;
            float lx = r.x + L->x * sx, ly = r.y + L->y * sy;
            float lw = L->w * sx, lh = L->h * sy, la = r.alpha, langle = r.angle;
            cam_box(L->depth, &lx, &ly, &lw, &lh, &langle);
            lx += lshift;
            if (L->anim == ANIM_STARS) {
                draw_stars(L, lx, ly, lw, lh, la, s->order + (u32)k * 7919u);
                continue;
            }
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
                gfx_image(tex, lx, ly + off + back, lw, lh, langle, la);
                ly += off;
                break;
            }
            }
            gfx_image(tex, lx, ly, lw, lh, langle, la);
        }
        return;
    }

    float shift = eye_sign(eye) * depth * strength;
    {
        float aw0 = fabsf(r.w), ah0 = fabsf(r.h);
        float x0 = r.x, y0 = r.y;
        cam_box(depth, &x0, &y0, &aw0, &ah0, &r.angle);
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
    if (im->flags & IMG_VIDEO) {
        /* A stereo video carries its own depth: each eye gets its own view,
         * not the layer's shift. Its disparity was made for full 3D; other
         * slider settings move its median plane by (1 - k) of itself (the
         * relief stays as encoded), and below STEREO_MIN it plays flat. */
        float k = g->max_shift > 0 ? clampf(strength / g->max_shift, 0, 2) : 0, mid = 0;
        GfxTex *st = k >= STEREO_MIN ? video_tex_stereo(im->res, eye, &mid) : NULL;
        if (st) {
            float s2 = -eye_sign(eye) * (1.0f - k) * mid * aw / 2;
            gfx_image(st, r.x + s2, r.y, r.w, r.h, r.angle, r.alpha);
            return;
        }
    }
    GfxTex *tex = (im->flags & IMG_VIDEO) ? video_tex(im->res) : texcache_image(im);
    if (tex && (im->flags & IMG_STEREO) && (eye == EYE_LEFT || eye == EYE_RIGHT) &&
        g->max_shift > 0 && strength / g->max_shift >= STEREO_MIN) {
        /* A stereo scene carries its own depth, as a stereo video does:
         * each eye its own view (texcache_image gave the left one). */
        int tw, th;
        gfx_tex_size(tex, &tw, &th);
        gfx_tex_window(tex, eye == EYE_RIGHT ? tw / 2 : 0, 0, tw / 2, th);
        gfx_image(tex, r.x, r.y, r.w, r.h, r.angle, r.alpha);
        gfx_tex_window(tex, 0, 0, tw / 2, th);
        return;
    }
    if (tex)
        gfx_image(tex, r.x + shift, r.y, r.w, r.h, r.angle, r.alpha);
}

void render_stage(const Stage *st, int eye, const float (*off)[2], float offk)
{
    cam_stage = st;
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
