/* Lantern Rhythm: placeholder until the real game lands. */
#include "minigame.h"

static float t;

static void start(u32 seed) { (void)seed; t = 0; }

static bool update(const Input *in, float dt, bool cheat)
{
    (void)cheat;
    t += dt;
    return !(in->down & KEY_A_) || t < 0.3f;
}

static void draw_top(int eye)
{
    mg_sky(eye, RGBA(20, 30, 60, 255), RGBA(60, 40, 90, 255));
    mg_text_centered(eye, "Lantern Rhythm\n(coming soon)\nPress A", TOP_W / 2, 90, 0.6f, -0.2f, MG_WHITE);
}

static int score(void) { return 50; }

const MiniGame MG_LANTERN = {
    .id = "lantern", .title = "Lantern Rhythm", .rules = "Coming soon.", .controls = "A: finish",
    .cheat = "Nothing yet", .start = start, .update = update, .draw_top = draw_top,
    .score = score,
};
