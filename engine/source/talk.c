/* Talking: mouth flaps and machine voices while a line of dialogue types out.
 *
 * Mouths follow Ren'Py's config.speaking_attribute: while a character speaks,
 * their sprite alternates between its image and the same image with the
 * speaking attribute added (e.g. "aron tired" <-> "aron tired talk").
 *
 * Voices are speech-like syllables in no language (vn3ds.json "voices"):
 * one plays at each vowel group as the letters appear, pitched per
 * character, with a falling or rising contour before . ? and !. The music
 * is ducked a little while someone talks so the two blend. */

#include "app.h"

#define FLAP_OPEN 0.11f
#define FLAP_SHUT 0.09f
#define SYLLABLE_GAP 0.085f

static struct {
    int sprite;
    s32 base, talk;
    float t;
    bool open;
} F = {-1, -1, -1, 0, false};

static size_t vox_prev;
static float vox_cool;
static float duck = 1.0f;

static bool is_vowel(u32 cp)
{
    if (cp < 128) {
        u32 c = cp | 0x20;
        return c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'y';
    }
    /* Latin-1 vowels with accents */
    return (cp >= 0xC0 && cp <= 0xC6) || (cp >= 0xC8 && cp <= 0xCF) || (cp >= 0xD2 && cp <= 0xD6) ||
           (cp >= 0xD9 && cp <= 0xDC) || (cp >= 0xE0 && cp <= 0xE6) || (cp >= 0xE8 && cp <= 0xEF) ||
           (cp >= 0xF2 && cp <= 0xF6) || (cp >= 0xF9 && cp <= 0xFC);
}

static void flap_set(bool open)
{
    if (F.sprite < 0 || F.sprite >= E.stage.n)
        return;
    E.stage.s[F.sprite].image = open ? F.talk : F.base;
    F.open = open;
}

void talk_end(void)
{
    if (F.sprite >= 0)
        flap_set(false);
    F.sprite = -1;
    audio_music_duck(duck = 1.0f);
}

void talk_begin(void)
{
    const Game *g = &E.game;
    const VM *vm = &E.vm;
    talk_end();
    vox_prev = (size_t)E.text_shown;
    vox_cool = 0;
    if (!g->speaking_attr || vm->say_char < 0 || (u32)vm->say_char >= g->nchars)
        return;
    const char *tag = g->chars[vm->say_char].image_tag;
    if (!tag)
        return;
    int idx = stage_find(&E.stage, tag);
    if (idx < 0)
        return;
    const Sprite *sp = &E.stage.s[idx];
    const ImageDef *im = &g->images[sp->image];
    char spec[160];
    size_t o = (size_t)snprintf(spec, sizeof(spec), "%s", im->tag);
    for (int i = 0; i < im->nattrs && o < sizeof(spec); i++)
        o += (size_t)snprintf(spec + o, sizeof(spec) - o, " %s", im->attrs[i]);
    snprintf(spec + o, sizeof(spec) - o, " %s", g->speaking_attr);
    s32 talk = stage_resolve(g, spec, sp);
    if (talk < 0 || talk == sp->image)
        return;
    /* only a real mouth frame: it must be the base image plus the attribute */
    if (g->images[talk].nattrs != im->nattrs + 1)
        return;
    F.sprite = idx;
    F.base = sp->image;
    F.talk = talk;
    F.t = 0;
    F.open = false;
    texcache_get(g->images[talk].res);
}

/* Pitch movement near the end of a sentence: falls before '.', rises before '?'. */
static float contour(const char *s, size_t at)
{
    int words = 0;
    for (const char *p = s + at; *p; p++) {
        if (*p == ' ' || *p == '\n')
            words++;
        if (*p == '.' || *p == '?' || *p == '!' || *p == ',') {
            if (words > 1)
                return 1.0f;
            return *p == '?' ? 1.13f : *p == '!' ? 1.06f : *p == ',' ? 1.02f : 0.9f;
        }
    }
    return words <= 1 ? 0.92f : 1.0f;
}

void talk_update(float dt)
{
    const Game *g = &E.game;
    const VM *vm = &E.vm;
    bool speaking = vm->state == VM_SAY && !E.text_done && !E.tr.active && !E.skip;

    /* mouth */
    if (F.sprite >= 0) {
        if (speaking) {
            F.t += dt;
            if (F.t >= (F.open ? FLAP_OPEN : FLAP_SHUT)) {
                F.t = 0;
                flap_set(!F.open);
            }
        } else if (F.open) {
            flap_set(false);
        }
    }

    /* voice */
    float pitch = (g->vox_pitch && vm->say_char >= 0 && (u32)vm->say_char < g->nchars)
                      ? g->vox_pitch[vm->say_char] : 0;
    bool voiced = speaking && pitch > 0 && g->nvox > 0 && !audio_playing(CH_VOICE);
    float want = voiced ? g->vox_duck : 1.0f;
    duck += (want - duck) * fminf(1.0f, dt * 6.0f);
    audio_music_duck(duck);
    vox_cool -= dt;
    size_t now = (size_t)E.text_shown;
    if (!voiced) {
        vox_prev = now;
        return;
    }
    size_t off = utf8_offset(E.wrapped, vox_prev);
    u32 prev_cp = 0;
    if (vox_prev > 0) {
        size_t po = utf8_offset(E.wrapped, vox_prev - 1);
        utf8_decode(E.wrapped + po, &prev_cp);
    }
    for (size_t i = vox_prev; i < now; i++) {
        u32 cp;
        int k = utf8_decode(E.wrapped + off, &cp);
        if (k <= 0)
            break;
        bool start = (is_vowel(cp) && !is_vowel(prev_cp)) || (cp >= 0x3000 && (i % 2) == 0);
        if (start && vox_cool <= 0) {
            u32 h = (u32)(i * 2654435761u) ^ cp;
            float jitter = 1.0f + ((float)((h >> 8) % 81) - 40.0f) / 1000.0f;
            audio_vox_play((int)(h % (u32)g->nvox), pitch * contour(E.wrapped, off) * jitter,
                           g->vox_volume * E.set.sound_vol);
            vox_cool = SYLLABLE_GAP;
        }
        prev_cp = cp;
        off += (size_t)k;
    }
    vox_prev = now;
}

void talk_load_bank(void)
{
    const Game *g = &E.game;
    if (g->nvox <= 0)
        return;
    static char paths[32][400];
    const char *ptrs[32];
    for (int i = 0; i < g->nvox; i++) {
        game_res_path(g, g->vox_res[i], paths[i], sizeof(paths[i]));
        ptrs[i] = paths[i];
    }
    audio_vox_load(ptrs, g->nvox);
}
