/* Story points: the home screen's story timeline (home.c).
 *
 * While you play, the first line after a `scene` becomes a story point when
 * no other point is within STORY_GAP lines of it: an ordinary save in slot
 * STORY_SLOT0 + k (written by the background thread, like autosaves), a
 * STORY_W x STORY_H snapshot of the top screen next to it (slotNNN.thm, cut
 * down from the resume snapshot that is taken anyway) and an entry in
 * saves/<id>/story.idx. Points are ordered by E.story_step, the number of
 * lines read since the story began (kept in the saves). A game keeps at most
 * STORY_MAX points, about 1.3 MB: when it is full, the point closest to its
 * neighbours makes room. Playing a stretch again refreshes its points. */

#include "app.h"
#include "bg.h"

#define STORY_GAP 30   /* lines between points, at least */
#define IDX_MAGIC "STI1"

static StoryPoint pts[STORY_MAX];   /* the loaded game's points, by step */
static int npts;
static bool scene_due;   /* a scene began: the next line may be a point */
static int pending = -1; /* a point's save is out, its snapshot not yet */

static void idx_path(const char *id, char *out, size_t len)
{
    snprintf(out, len, "%s/saves/%s/story.idx", E.root, id);
}

int story_read(const char *game_id, StoryPoint *out, int max)
{
    char path[400];
    idx_path(game_id, path, sizeof(path));
    FILE *f = fopen(path, "rb");
    if (!f)
        return 0;
    char magic[4];
    u32 n = 0;
    int got = 0;
    if (fread(magic, 1, 4, f) == 4 && !memcmp(magic, IDX_MAGIC, 4) && fread(&n, 4, 1, f) == 1)
        while (got < max && got < (int)n && fread(&out[got], sizeof(StoryPoint), 1, f) == 1) {
            out[got].preview[sizeof(out[got].preview) - 1] = 0;
            if (out[got].k < STORY_MAX)
                got++;
        }
    fclose(f);
    return got;
}

static void write_index(void)
{
    size_t n = 8 + sizeof(StoryPoint) * (size_t)npts;
    u8 *buf = malloc(n);
    if (!buf)
        return;
    u32 cnt = (u32)npts;
    memcpy(buf, IDX_MAGIC, 4);
    memcpy(buf + 4, &cnt, 4);
    memcpy(buf + 8, pts, sizeof(StoryPoint) * (size_t)npts);
    char path[400];
    idx_path(E.game.id, path, sizeof(path));
    bg_write_file(path, buf, n);
}

void story_game_opened(void)
{
    npts = story_read(E.game.id, pts, STORY_MAX);
    scene_due = false;
    pending = -1;
}

u32 story_latest_step(void)
{
    u32 best = 0, t = 0;
    for (int i = 0; i < npts; i++)
        if (pts[i].time >= t) {
            t = pts[i].time;
            best = pts[i].step;
        }
    return best;
}

void story_scene(void) { scene_due = true; }

/* The slot for a new point: a free one, or the one whose neighbours are
 * closest together (never the first or the last). Removes it from pts. */
static int take_slot(void)
{
    bool used[STORY_MAX] = {false};
    for (int i = 0; i < npts; i++)
        used[pts[i].k] = true;
    for (int k = 0; k < STORY_MAX; k++)
        if (!used[k])
            return k;
    int drop = 1;
    for (int i = 2; i < npts - 1; i++)
        if (pts[i + 1].step - pts[i - 1].step < pts[drop + 1].step - pts[drop - 1].step)
            drop = i;
    int k = pts[drop].k;
    memmove(&pts[drop], &pts[drop + 1], sizeof(StoryPoint) * (size_t)(npts - drop - 1));
    npts--;
    return k;
}

void story_snapshot(void)
{
    if (!scene_due || !E.loaded || E.vm.state != VM_SAY)
        return;
    scene_due = false;
    u32 step = E.story_step, pc = E.vm.resume_pc;
    int same = -1;
    for (int i = 0; i < npts; i++) {
        u32 d = pts[i].step > step ? pts[i].step - step : step - pts[i].step;
        if (pts[i].pc == pc)
            same = i;
        else if (d < STORY_GAP)
            return;   /* a point close by already */
    }
    int k;
    if (same >= 0) {   /* this stretch again: refresh its point */
        k = pts[same].k;
        memmove(&pts[same], &pts[same + 1], sizeof(StoryPoint) * (size_t)(npts - same - 1));
        npts--;
    } else {
        k = take_slot();
    }
    if (!save_write_ex(STORY_SLOT0 + k, true))
        return;
    StoryPoint p;
    memset(&p, 0, sizeof(p));
    p.k = (u16)k;
    p.pc = pc;
    p.step = step;
    p.time = platform_time();
    if (E.vm.say_who[0])
        snprintf(p.preview, sizeof(p.preview), "%s: %s", E.vm.say_who, E.vm.say_text);
    else
        snprintf(p.preview, sizeof(p.preview), "%s", E.vm.say_text);
    for (char *c = p.preview; *c; c++)
        if (*c == '\n')
            *c = ' ';
    int at = npts;
    while (at > 0 && pts[at - 1].step > step)
        at--;
    memmove(&pts[at + 1], &pts[at], sizeof(StoryPoint) * (size_t)(npts - at));
    pts[at] = p;
    npts++;
    pending = k;
}

void story_thumb_path(const char *id, int k, char *out, size_t len)
{
    snprintf(out, len, "%s/saves/%s/slot%02d.thm", E.root, id, STORY_SLOT0 + k);
}

void story_thumb(const u16 *px, int w, int h)
{
    if (pending < 0)
        return;
    int k = pending;
    pending = -1;
    size_t n = 8 + STORY_W * STORY_H * 2;
    u8 *buf = malloc(n);
    if (!buf)
        return;
    u16 wh[2] = {STORY_W, STORY_H}, *out = (u16 *)(buf + 8);
    memcpy(buf, "THM1", 4);
    memcpy(buf + 4, wh, 4);
    /* shrink by averaging the source pixels under each new one (2x2) */
    for (int y = 0; y < STORY_H; y++)
        for (int x = 0; x < STORY_W; x++) {
            int sx = x * w / STORY_W, sy = y * h / STORY_H;
            int sx1 = sx + 1 < w ? sx + 1 : sx, sy1 = sy + 1 < h ? sy + 1 : sy;
            u16 q[4] = {px[sy * w + sx], px[sy * w + sx1], px[sy1 * w + sx], px[sy1 * w + sx1]};
            u32 r = 0, g = 0, b = 0;
            for (int i = 0; i < 4; i++) {
                r += q[i] >> 11;
                g += (q[i] >> 5) & 63;
                b += q[i] & 31;
            }
            out[y * STORY_W + x] = (u16)(((r / 4) << 11) | ((g / 4) << 5) | (b / 4));
        }
    char path[400];
    story_thumb_path(E.game.id, k, path, sizeof(path));
    bg_write_file(path, buf, n);
    write_index();
}
