/* The Big Questions: five questions about philosophy and religion, each
 * harder, faster and worth more than the last. Answers on the touch screen
 * (or D-pad + A). The cheat answers one question for you.
 *
 * Score: level k is worth k points (15 in all); a right answer earns 60% of
 * them plus up to 40% for speed. */

#include "minigame.h"

#define LEVELS 5
#define PER_LEVEL 4

typedef struct {
    const char *q;
    const char *a[4]; /* a[0] is the right answer; shown shuffled */
} Question;

static const Question POOL[LEVELS][PER_LEVEL] = {
    {
        {"Who said \"I think, therefore I am\"?", {"Descartes", "Plato", "Nietzsche", "Confucius"}},
        {"The Quran is the holy book of which religion?", {"Islam", "Hinduism", "Buddhism", "Judaism"}},
        {"How many Noble Truths did the Buddha teach?", {"Four", "Three", "Seven", "Ten"}},
        {"Who drank hemlock after his trial in Athens?", {"Socrates", "Aristotle", "Diogenes", "Epicurus"}},
    },
    {
        {"Plato's prisoners mistake shadows for the real world. Where are they?",
         {"In a cave", "On a ship", "In a garden", "In a tower"}},
        {"Who wrote \"Thus Spoke Zarathustra\"?", {"Nietzsche", "Kant", "Hegel", "Kierkegaard"}},
        {"In Hinduism, the cycle of birth, death and rebirth is called...",
         {"Samsara", "Nirvana", "Dharma", "Moksha"}},
        {"Who said you can never step into the same river twice?",
         {"Heraclitus", "Parmenides", "Thales", "Zeno"}},
    },
    {
        {"Bostrom's simulation argument: which of these is one of its three options?",
         {"Civilisations die out first", "Minds can't be simulated", "We can prove we're simulated",
          "Only one universe exists"}},
        {"The Tao Te Ching is traditionally credited to...", {"Laozi", "Confucius", "Mencius", "Zhuangzi"}},
        {"Whose thought experiment offers a machine of perfect, fake happiness?",
         {"Nozick's", "Searle's", "Schrodinger's", "Locke's"}},
        {"\"The unexamined life is not worth living\" is said at whose trial?",
         {"Socrates'", "Jesus'", "Galileo's", "Joan of Arc's"}},
    },
    {
        {"Kant: act only on a rule you could will to be...",
         {"A universal law", "Profitable", "Forgiven", "Beautiful"}},
        {"Who called human beings \"condemned to be free\"?", {"Sartre", "Camus", "Heidegger", "Spinoza"}},
        {"Pascal's Wager is a bet about...", {"Believing in God", "Free will", "The soul's weight", "Fate"}},
        {"A Zen riddle like \"the sound of one hand clapping\" is a...", {"Koan", "Mantra", "Sutra", "Mudra"}},
    },
    {
        {"Spinoza's phrase \"Deus sive Natura\" makes God the same as...",
         {"Nature", "The State", "Reason alone", "The self"}},
        {"Who argued that ours is the best of all possible worlds?", {"Leibniz", "Voltaire", "Hume", "Berkeley"}},
        {"Gnostic texts call the lesser maker of the material world the...",
         {"Demiurge", "Logos", "Pleroma", "Paraclete"}},
        {"Who wrote \"The Consolation of Philosophy\" awaiting execution?",
         {"Boethius", "Seneca", "Augustine", "Aquinas"}},
    },
};

static const float TIME_LIMIT[LEVELS] = {20, 18, 16, 14, 12};

static struct {
    int level;             /* 0..LEVELS-1, LEVELS when done */
    const Question *q;
    int order[4];          /* displayed slot -> answer index */
    int sel;
    float left;            /* seconds left for this question */
    float feedback;        /* > 0 while showing right/wrong */
    int picked;            /* slot picked, -1 for timeout, -2 for cheat */
    bool right[LEVELS];
    float points;
    float t;
} Q;

static void next_question(void)
{
    Q.q = &POOL[Q.level][mg_randi(0, PER_LEVEL - 1)];
    for (int i = 0; i < 4; i++)
        Q.order[i] = i;
    for (int i = 3; i > 0; i--) {
        int j = mg_randi(0, i), k = Q.order[i];
        Q.order[i] = Q.order[j];
        Q.order[j] = k;
    }
    Q.sel = 0;
    Q.left = TIME_LIMIT[Q.level];
    Q.feedback = 0;
    Q.picked = -1;
}

static void start(u32 seed)
{
    (void)seed;
    memset(&Q, 0, sizeof(Q));
    next_question();
}

static void answer(int slot, bool cheat)
{
    int weight = Q.level + 1;
    bool ok = cheat || (slot >= 0 && Q.order[slot] == 0);
    Q.picked = cheat ? -2 : slot;
    Q.right[Q.level] = ok;
    if (ok) {
        float speed = cheat ? 0 : clampf(Q.left / TIME_LIMIT[Q.level], 0, 1);
        Q.points += weight * (0.6f + 0.4f * speed);
    }
    Q.feedback = 1.6f;
    mg_sfx(cheat ? "quiz_cheat_answer" : ok ? "quiz_right" : slot < 0 ? "quiz_timeout" : "quiz_wrong");
}

static bool update(const Input *in, float dt, bool cheat)
{
    Q.t += dt;
    if (Q.feedback > 0) {
        Q.feedback -= dt;
        if (Q.feedback <= 0) {
            if (++Q.level >= LEVELS)
                return false;
            next_question();
            mg_sfx("quiz_next");
        }
        return true;
    }
    if (cheat) {
        answer(-1, true);
        return true;
    }
    Q.left -= dt;
    if (Q.left <= 0) {
        Q.left = 0;
        answer(-1, false);
        return true;
    }
    /* a soft tick through the last three seconds */
    if ((int)(Q.left + dt) != (int)Q.left && Q.left < 3.0f)
        mg_sfx("quiz_tick");
    if (in->down & (KEY_UP_ | KEY_DOWN_)) {
        Q.sel = (Q.sel + ((in->down & KEY_UP_) ? 3 : 1)) % 4;
        mg_sfx("quiz_move");
    }
    if (in->down & KEY_A_) {
        answer(Q.sel, false);
        return true;
    }
    if (in->down & KEY_TOUCH_)
        for (int i = 0; i < 4; i++)
            if (in->ty >= 24 + i * 44 && in->ty < 24 + i * 44 + 40 && in->tx >= 12 && in->tx < 308) {
                Q.sel = i;
                answer(i, false);
                break;
            }
    return true;
}

/* ---- drawing ------------------------------------------------------------- */

static void draw_top(int eye)
{
    mg_sky(eye, RGBA(14, 12, 40, 255), RGBA(58, 30, 74, 255));
    /* a slowly turning constellation far behind */
    float a0 = Q.t * 0.12f;
    float px = 0, py = 0;
    for (int i = 0; i < 14; i++) {
        float a = a0 + i * 0.9f, r = 60 + (i * 37 % 90);
        float x = 200 + cosf(a) * r * 1.6f, y = 120 + sinf(a) * r * 0.7f;
        if (i)
            mg_line(eye, px, py, x, y, 1, 0.9f, RGBA(160, 170, 255, 50));
        mg_circle(eye, x, y, 1.6f + (i % 3), 0.9f, RGBA(220, 220, 255, 160));
        px = x;
        py = y;
    }
    /* the "question" sigil: a ring and a turning triangle, mid-depth */
    float ra = Q.t * 0.6f;
    mg_circle(eye, 200, 128, 46, 0.35f, RGBA(255, 210, 110, 40));
    mg_circle(eye, 200, 128, 40, 0.35f, RGBA(14, 12, 40, 200));
    mg_tri(eye, 200 + cosf(ra) * 34, 128 + sinf(ra) * 34, 200 + cosf(ra + 2.094f) * 34,
           128 + sinf(ra + 2.094f) * 34, 200 + cosf(ra + 4.189f) * 34, 128 + sinf(ra + 4.189f) * 34,
           0.3f, RGBA(255, 210, 110, 70));

    /* level pips */
    for (int i = 0; i < LEVELS; i++) {
        u32 c = i < Q.level ? (Q.right[i] ? RGBA(120, 230, 150, 255) : RGBA(230, 110, 110, 255))
              : i == Q.level ? MG_GOLD : RGBA(255, 255, 255, 60);
        mg_circle(eye, 160 + i * 20, 16, 5, -0.15f, c);
    }
    if (Q.level >= LEVELS || !Q.q)
        return;

    /* the question on a floating card */
    char wrapped[400];
    ui_wrap(Q.q->q, 340, 0.6f, wrapped, sizeof(wrapped));
    mg_rect(eye, 20, 36, 360, 76, -0.08f, RGBA(10, 8, 24, 190));
    mg_text_centered(eye, wrapped, 200, 44, 0.6f, -0.1f, MG_WHITE);

    /* answers, also on the top screen so you can keep your eyes up */
    for (int i = 0; i < 4; i++) {
        int ai = Q.order[i];
        bool show = Q.feedback > 0;
        u32 c = MG_WHITE;
        if (show && ai == 0)
            c = RGBA(120, 230, 150, 255);
        else if (show && i == Q.picked)
            c = RGBA(230, 110, 110, 255);
        else if (!show && i == Q.sel)
            c = MG_GOLD;
        mg_text_centered(eye, Q.q->a[ai], 200, 124 + i * 22, 0.52f, -0.05f - (i == Q.sel) * 0.12f, c);
    }

    /* timer bar */
    float f = Q.left / TIME_LIMIT[Q.level];
    mg_rect(eye, 40, 222, 320, 6, -0.2f, RGBA(255, 255, 255, 40));
    mg_rect(eye, 40, 222, 320 * f, 6, -0.2f, f > 0.3f ? MG_GOLD : RGBA(240, 120, 100, 255));
    if (Q.feedback > 0 && Q.picked == -2)
        mg_text_centered(eye, "Miso knew it.", 200, 196, 0.5f, -0.3f, RGBA(255, 200, 150, 255));
}

static void draw_bottom(void)
{
    char buf[64];
    snprintf(buf, sizeof(buf), "Question %d of %d  (worth %d)", Q.level < LEVELS ? Q.level + 1 : LEVELS,
             LEVELS, Q.level < LEVELS ? Q.level + 1 : LEVELS);
    gfx_text(buf, 12, 4, 0.45f, MG_GOLD);
    if (!Q.q || Q.level >= LEVELS)
        return;
    for (int i = 0; i < 4; i++) {
        int ai = Q.order[i];
        u32 bg = i == Q.sel ? RGBA(255, 255, 255, 230) : RGBA(255, 255, 255, 40);
        u32 fg = i == Q.sel ? MG_INK : MG_WHITE;
        if (Q.feedback > 0) {
            if (ai == 0)
                bg = RGBA(110, 210, 140, 255), fg = MG_INK;
            else if (i == Q.picked)
                bg = RGBA(220, 100, 100, 255), fg = MG_WHITE;
        }
        float y = 24 + i * 44;
        gfx_rect(12, y, 296, 40, bg);
        float sc = 0.5f;
        while (sc > 0.36f && gfx_text_width(Q.q->a[ai], sc) > 280)
            sc -= 0.02f;
        gfx_text(Q.q->a[ai], 160 - gfx_text_width(Q.q->a[ai], sc) / 2, y + (40 - gfx_line_height(sc)) / 2,
                 sc, fg);
    }
}

static int score(void)
{
    return (int)(Q.points / 15.0f * 100.0f + 0.5f);
}

static const char *verdict(void)
{
    static char buf[96];
    int n = 0;
    for (int i = 0; i < LEVELS; i++)
        n += Q.right[i];
    snprintf(buf, sizeof(buf), "%d of %d answered. %s", n, LEVELS,
             n == 5 ? "Socrates would have questions." : n >= 3 ? "Wisdom begins in wonder." :
             "Knowing you don't know is a start.");
    return buf;
}

static void bot(Input *in, float t)
{
    /* answer each question after two seconds, guessing the second slot */
    static float last;
    if (t < last)
        last = 0;
    if (Q.feedback <= 0 && t - last > 2.0f) {
        in->down |= KEY_DOWN_;
        last = t;
    } else if (Q.feedback <= 0 && t - last > 1.0f && Q.sel == 1) {
        in->down |= KEY_A_;
    }
}

/* the cheat can't help once the run is wrapping up */
static bool can_cheat(void) { return Q.level < LEVELS && Q.feedback <= 0; }

const MiniGame MG_QUIZ = {
    .id = "quiz",
    .title = "The Big Questions",
    .rules = "Five questions about philosophy and the\n"
             "world's religions. Each one is harder,\n"
             "has less time, and is worth more.\n"
             "Answer fast for a bonus.",
    .controls = "Touch an answer, or\nD-pad: choose    A: answer\nSTART: pause",
    .cheat = "Miso answers one question for you",
    .music = "quiz",
    .start = start,
    .update = update,
    .draw_top = draw_top,
    .draw_bottom = draw_bottom,
    .score = score,
    .verdict = verdict,
    .can_cheat = can_cheat,
    .bot = bot,
};
