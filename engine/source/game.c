#include "game.h"

#include <stdarg.h>

typedef struct {
    const u8 *p;
    u32 size;
} Section;

static u8 *read_file(const char *path, u32 *size)
{
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    u8 *buf = n > 0 ? malloc((size_t)n) : NULL;
    if (buf && fread(buf, 1, (size_t)n, f) != (size_t)n) {
        free(buf);
        buf = NULL;
    }
    fclose(f);
    if (buf)
        *size = (u32)n;
    return buf;
}

static bool find_section(const u8 *data, u32 size, const char *tag, Section *out)
{
    u32 n = rd_u32(data + 8);
    for (u32 i = 0; i < n; i++) {
        const u8 *e = data + 12 + i * 12;
        if (12 + (i + 1) * 12 > size)
            return false;
        if (memcmp(e, tag, 4) == 0) {
            u32 off = rd_u32(e + 4), len = rd_u32(e + 8);
            if (off + len > size)
                return false;
            out->p = data + off;
            out->size = len;
            return true;
        }
    }
    return false;
}

static void set_err(char *err, size_t len, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(err, len, fmt, ap);
    va_end(ap);
}

const char *game_str(const Game *g, u32 idx)
{
    if (idx == NONE_STR || idx >= g->nstrings)
        return NULL;
    return g->strings[idx];
}

static void split_words(ImageDef *im)
{
    im->words = strdup(im->name ? im->name : "");
    im->nattrs = 0;
    im->tag = "";
    char *p = im->words;
    int i = 0;
    while (*p) {
        while (*p == ' ')
            *p++ = 0;
        if (!*p)
            break;
        if (i == 0)
            im->tag = p;
        else if (im->nattrs < MAX_ATTRS)
            im->attrs[im->nattrs++] = p;
        i++;
        while (*p && *p != ' ')
            p++;
    }
}

bool game_load(Game *g, const char *dir, const char *id, char *err, size_t errlen)
{
    memset(g, 0, sizeof(*g));
    snprintf(g->dir, sizeof(g->dir), "%s", dir);
    snprintf(g->id, sizeof(g->id), "%s", id);
    char path[300];
    snprintf(path, sizeof(path), "%s/game.bin", dir);
    g->data = read_file(path, &g->size);
    if (!g->data) {
        set_err(err, errlen, "cannot read %s", path);
        return false;
    }
    const u8 *d = g->data;
    if (g->size < 12 || memcmp(d, "VN3D", 4) != 0) {
        set_err(err, errlen, "%s is not a vn3ds game", path);
        goto fail;
    }
    if (rd_u32(d + 4) != 1) {
        set_err(err, errlen, "game.bin version %u is not supported; update vn3ds",
                (unsigned)rd_u32(d + 4));
        goto fail;
    }
    g->crc = crc32_update(0, d, g->size);

    Section s;
    if (!find_section(d, g->size, "STR ", &s))
        goto corrupt;
    g->nstrings = rd_u32(s.p);
    g->strings = calloc(g->nstrings + 1, sizeof(char *));
    const char *blob = (const char *)s.p + 4 + 4 * g->nstrings;
    for (u32 i = 0; i < g->nstrings; i++)
        g->strings[i] = blob + rd_u32(s.p + 4 + 4 * i);

    if (!find_section(d, g->size, "META", &s) || s.size < 60)
        goto corrupt;
    const u8 *m = s.p;
    g->title = game_str(g, rd_u32(m));
    g->version = game_str(g, rd_u32(m + 4));
    g->game_w = rd_u16(m + 8);
    g->game_h = rd_u16(m + 10);
    g->scale = rd_f32(m + 12);
    g->view_x = rd_f32(m + 16);
    g->view_y = rd_f32(m + 20);
    g->view_w = rd_f32(m + 24);
    g->view_h = rd_f32(m + 28);
    g->init_addr = rd_u32(m + 32);
    g->nvars = rd_u32(m + 36);
    g->depth_bg = rd_f32(m + 40);
    g->depth_sprite = rd_f32(m + 44);
    g->depth_ui = rd_f32(m + 48);
    g->max_shift = rd_f32(m + 52);
    g->title_image = rd_s32(m + 56);
    if (!g->title)
        g->title = id;

    if (!find_section(d, g->size, "VARS", &s))
        goto corrupt;
    u32 nv = rd_u32(s.p);
    g->var_names = calloc(nv + 1, sizeof(char *));
    for (u32 i = 0; i < nv; i++)
        g->var_names[i] = game_str(g, rd_u32(s.p + 4 + 4 * i));

    if (!find_section(d, g->size, "RES ", &s))
        goto corrupt;
    g->nres = rd_u32(s.p);
    g->res = calloc(g->nres + 1, sizeof(char *));
    for (u32 i = 0; i < g->nres; i++)
        g->res[i] = game_str(g, rd_u32(s.p + 4 + 4 * i));

    if (!find_section(d, g->size, "IMGS", &s))
        goto corrupt;
    g->nimages = rd_u32(s.p);
    g->images = calloc(g->nimages + 1, sizeof(ImageDef));
    for (u32 i = 0; i < g->nimages; i++) {
        const u8 *e = s.p + 4 + 28 * i;
        ImageDef *im = &g->images[i];
        im->name = game_str(g, rd_u32(e));
        im->res = rd_s32(e + 4);
        im->color = rd_u32(e + 8);
        im->w = rd_f32(e + 12);
        im->h = rd_f32(e + 16);
        im->flags = rd_u32(e + 20);
        im->depth = rd_f32(e + 24);
        im->patch_res = -1;
        split_words(im);
    }

    if (find_section(d, g->size, "LAYR", &s)) {
        u32 n = rd_u32(s.p);
        const u8 *e = s.p + 4;
        for (u32 i = 0; i < n && e + 8 <= s.p + s.size; i++) {
            u32 img = rd_u32(e), nl = rd_u32(e + 4);
            e += 8;
            if (img < g->nimages && nl > 0 && nl < 64 && e + 40 * nl <= s.p + s.size) {
                ImageDef *im = &g->images[img];
                im->layers = calloc(nl, sizeof(ImageLayer));
                im->nlayers = (int)nl;
                for (u32 k = 0; k < nl; k++) {
                    const u8 *l = e + 40 * k;
                    im->layers[k].res = rd_s32(l);
                    im->layers[k].depth = rd_f32(l + 4);
                    im->layers[k].x = rd_f32(l + 8);
                    im->layers[k].y = rd_f32(l + 12);
                    im->layers[k].w = rd_f32(l + 16);
                    im->layers[k].h = rd_f32(l + 20);
                    im->layers[k].anim = rd_u32(l + 24);
                    im->layers[k].a = rd_f32(l + 28);
                    im->layers[k].b = rd_f32(l + 32);
                    im->layers[k].period = rd_f32(l + 36);
                }
                /* base picture + patch: an ordinary image with a composite texture */
                if (nl == 2 && im->layers[1].anim == ANIM_PATCH && im->layers[0].res == im->res &&
                    im->layers[1].res >= 0 && im->layers[1].a >= 0 && im->layers[1].b >= 0) {
                    im->patch_res = im->layers[1].res;
                    im->patch_x = (int)im->layers[1].a;
                    im->patch_y = (int)im->layers[1].b;
                    free(im->layers);
                    im->layers = NULL;
                    im->nlayers = 0;
                }
            }
            e += 40 * nl;
        }
    }

    if (!find_section(d, g->size, "CHRS", &s))
        goto corrupt;
    g->nchars = rd_u32(s.p);
    g->chars = calloc(g->nchars + 1, sizeof(CharDef));
    for (u32 i = 0; i < g->nchars; i++) {
        const u8 *e = s.p + 4 + 28 * i;
        CharDef *c = &g->chars[i];
        c->name = game_str(g, rd_u32(e));
        c->image_tag = game_str(g, rd_u32(e + 4));
        c->name_color = rd_u32(e + 8);
        c->text_color = rd_u32(e + 12);
        c->prefix = game_str(g, rd_u32(e + 16));
        c->suffix = game_str(g, rd_u32(e + 20));
        c->kind = e[24];
    }

    if (!find_section(d, g->size, "TRAN", &s))
        goto corrupt;
    g->ntrans = rd_u32(s.p);
    g->trans = calloc(g->ntrans + 1, sizeof(TransDef));
    for (u32 i = 0; i < g->ntrans; i++) {
        const u8 *e = s.p + 4 + 20 * i;
        TransDef *t = &g->trans[i];
        t->type = e[0];
        t->warper = e[1];
        t->dir = e[2];
        t->a = rd_f32(e + 4);
        t->b = rd_f32(e + 8);
        t->c = rd_f32(e + 12);
        t->color = rd_u32(e + 16);
    }

    if (!find_section(d, g->size, "ATL ", &s))
        goto corrupt;
    g->natl = rd_u32(s.p);
    g->atl = calloc(g->natl + 1, sizeof(AtlProg));
    const u8 *atl_data = s.p + 4 + 4 * g->natl;
    for (u32 i = 0; i < g->natl; i++) {
        const u8 *p = atl_data + rd_u32(s.p + 4 + 4 * i);
        AtlProg *prog = &g->atl[i];
        prog->nsteps = rd_u16(p);
        p += 2;
        prog->steps = calloc(prog->nsteps + 1, sizeof(AtlStep));
        for (u16 k = 0; k < prog->nsteps; k++) {
            AtlStep *st = &prog->steps[k];
            st->kind = p[0];
            st->warper = p[1];
            st->nprops = p[2];
            st->dur = rd_f32(p + 4);
            st->target = rd_u16(p + 8);
            st->count = rd_u16(p + 10);
            st->props = p + 12;
            p += 12 + 8 * st->nprops;
        }
    }

    if (!find_section(d, g->size, "CODE", &s))
        goto corrupt;
    g->code = s.p;
    g->code_size = s.size;
    if (find_section(d, g->size, "LABL", &s))
        g->labels = s.p;
    if (find_section(d, g->size, "CAM ", &s) && s.size >= 12) {
        g->cam_drift = rd_f32(s.p);
        g->cam_period = rd_f32(s.p + 4);
        g->cam_zoom = rd_f32(s.p + 8);
    }
    if (find_section(d, g->size, "MINI", &s) && s.size >= 4) {
        u32 n = rd_u32(s.p);
        for (u32 i = 0; i < n && i < 16 && 8 + 4 * i <= s.size; i++)
            if (game_str(g, rd_u32(s.p + 4 + 4 * i)))
                g->minigames[g->nminigames++] = game_str(g, rd_u32(s.p + 4 + 4 * i));
    }
    if (find_section(d, g->size, "AUDN", &s) && s.size >= 4 && 4 + 8 * rd_u32(s.p) <= s.size)
        g->audio_names = s.p;
    if (find_section(d, g->size, "MUSM", &s) && s.size >= 4 && 4 + 12 * (u64)rd_u32(s.p) <= s.size) {
        g->music_meta = s.p + 4;
        g->nmusic_meta = rd_u32(s.p);
    }
    if (find_section(d, g->size, "TALK", &s) && s.size >= 4)
        g->speaking_attr = game_str(g, rd_u32(s.p));
    if (find_section(d, g->size, "VOX ", &s) && s.size >= 4) {
        u32 n = rd_u32(s.p);
        const u8 *e = s.p + 4;
        for (u32 i = 0; i < n && i < 32; i++)
            g->vox_res[g->nvox++] = rd_s32(e + 4 * i);
        e += 4 * n;
        g->vox_volume = rd_f32(e);
        g->vox_duck = rd_f32(e + 4);
        u32 nc = rd_u32(e + 8);
        g->vox_pitch = calloc(g->nchars + 1, sizeof(float));
        for (u32 i = 0; i < nc && i < g->nchars; i++)
            g->vox_pitch[i] = rd_f32(e + 12 + 4 * i);
    }
    return true;

corrupt:
    set_err(err, errlen, "%s is damaged (missing section)", path);
fail:
    game_free(g);
    return false;
}

void game_free(Game *g)
{
    if (g->images)
        for (u32 i = 0; i < g->nimages; i++) {
            free(g->images[i].words);
            free(g->images[i].layers);
        }
    if (g->atl)
        for (u32 i = 0; i < g->natl; i++)
            free(g->atl[i].steps);
    free(g->vox_pitch);
    free(g->images);
    free(g->chars);
    free(g->trans);
    free(g->atl);
    free(g->res);
    free(g->var_names);
    free(g->strings);
    free(g->data);
    memset(g, 0, sizeof(*g));
}

s32 game_label(const Game *g, const char *name)
{
    if (!g->labels)
        return -1;
    u32 n = rd_u32(g->labels);
    for (u32 i = 0; i < n; i++) {
        const char *ln = game_str(g, rd_u32(g->labels + 4 + 8 * i));
        if (ln && strcmp(ln, name) == 0)
            return (s32)rd_u32(g->labels + 8 + 8 * i);
    }
    return -1;
}

s32 game_audio_named(const Game *g, const char *name)
{
    if (!g->audio_names)
        return -1;
    u32 n = rd_u32(g->audio_names);
    for (u32 i = 0; i < n; i++) {
        const char *an = game_str(g, rd_u32(g->audio_names + 4 + 8 * i));
        if (an && strcmp(an, name) == 0)
            return rd_s32(g->audio_names + 8 + 8 * i);
    }
    return -1;
}

void game_res_path(const Game *g, s32 res, char *out, size_t len)
{
    if (res < 0 || (u32)res >= g->nres || !g->res[res]) {
        out[0] = 0;
        return;
    }
    snprintf(out, len, "%s/%s", g->dir, g->res[res]);
}

bool game_peek_title(const char *dir, char *out, size_t len)
{
    Game g;
    char err[128];
    if (!game_load(&g, dir, "", err, sizeof(err)))
        return false;
    snprintf(out, len, "%s", g.title ? g.title : "");
    game_free(&g);
    return true;
}

/* ---- small shared helpers -------------------------------------------- */

int utf8_decode(const char *s, u32 *cp)
{
    const u8 *u = (const u8 *)s;
    if (u[0] < 0x80) {
        *cp = u[0];
        return u[0] ? 1 : 0;
    }
    if ((u[0] & 0xE0) == 0xC0 && (u[1] & 0xC0) == 0x80) {
        *cp = ((u32)(u[0] & 0x1F) << 6) | (u[1] & 0x3F);
        return 2;
    }
    if ((u[0] & 0xF0) == 0xE0 && (u[1] & 0xC0) == 0x80 && (u[2] & 0xC0) == 0x80) {
        *cp = ((u32)(u[0] & 0x0F) << 12) | ((u32)(u[1] & 0x3F) << 6) | (u[2] & 0x3F);
        return 3;
    }
    if ((u[0] & 0xF8) == 0xF0 && (u[1] & 0xC0) == 0x80 && (u[2] & 0xC0) == 0x80 &&
        (u[3] & 0xC0) == 0x80) {
        *cp = ((u32)(u[0] & 0x07) << 18) | ((u32)(u[1] & 0x3F) << 12) |
              ((u32)(u[2] & 0x3F) << 6) | (u[3] & 0x3F);
        return 4;
    }
    *cp = 0xFFFD;
    return 1;
}

size_t utf8_offset(const char *s, size_t n)
{
    size_t off = 0;
    u32 cp;
    while (n-- > 0) {
        int k = utf8_decode(s + off, &cp);
        if (k == 0)
            break;
        off += (size_t)k;
    }
    return off;
}

size_t utf8_len(const char *s)
{
    size_t n = 0, off = 0;
    u32 cp;
    int k;
    while ((k = utf8_decode(s + off, &cp)) > 0) {
        off += (size_t)k;
        n++;
    }
    return n;
}

u32 crc32_update(u32 crc, const void *data, size_t len)
{
    static u32 table[256];
    static bool init;
    if (!init) {
        for (u32 i = 0; i < 256; i++) {
            u32 c = i;
            for (int k = 0; k < 8; k++)
                c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : c >> 1;
            table[i] = c;
        }
        init = true;
    }
    const u8 *p = data;
    crc = ~crc;
    while (len--)
        crc = table[(crc ^ *p++) & 0xFF] ^ (crc >> 8);
    return ~crc;
}
