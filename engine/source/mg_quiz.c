/* The Big Questions: Adjutant Vael, Seraphiel's adjutant, reads you five
 * questions about philosophy and religion, each harder and worth more than
 * the last. She announces each one, reads it aloud (A skips), turns her
 * hourglass and waits for your answer on the touch screen (or D-pad + A).
 * She glows when you're right, looks sorry when you're wrong, taps her
 * quill as time runs out, and is scandalised when Miso (the cheat) pops up
 * and answers for you.
 *
 * Score: level k is worth k points (15 in all); a right answer earns 60% of
 * them plus up to 40% for speed. The clock only runs once she has finished
 * reading. */

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

/* Her reactions; %s is the right answer. */
static const char *const SAY_RIGHT[LEVELS] = {
    "Yes! %s. Splendid.", "Exactly right: %s.", "Correct! %s. Lovely.",
    "Yes! %s. Heaven is pleased.", "%s! Perfect. Well read.",
};
static const char *const SAY_WRONG[3] = {
    "Oh, dear. The answer: %s.", "Not quite. The answer: %s.", "Ah... the answer: %s.",
};

/* ---- layout ------------------------------------------------------------------ */

/* Vael is drawn from Seraphiel's sprite (make_demo_assets.py seraph(), 640x700),
 * scaled by VS with its centre line at VX. */
#define VX 104.0f
#define VTOP 16.0f
#define VS 0.34f
#define PX(x) (VX + ((x) - 320.0f) * VS)
#define PY(y) (oy + (y) * VS)

/* the speech bubble */
#define BX 196.0f
#define BY 28.0f
#define BW 196.0f
#define BH 170.0f
#define TX (BX + 10)
#define TY (BY + 10)
#define TW (BW - 20)
#define ANS_Y (BY + 98)
#define ANS_H 17.0f

/* her hourglass, on a cloud at the lower left */
#define HGX 30.0f
#define HGY 196.0f

/* depths: heaven far behind, Vael a little in front of it, the bubble at the
 * screen, Miso popping out */
#define D_LIGHT 1.0f
#define D_RAYS 0.95f
#define D_CLOUD_FAR 0.8f
#define D_CLOUD_NEAR 0.5f
#define D_WING 0.26f
#define D_GLOW 0.24f
#define D_HAIR 0.22f
#define D_BODY 0.18f
#define D_FACE 0.16f
#define D_HANDS 0.12f
#define D_HOURGLASS 0.1f
#define D_BUBBLE -0.04f
#define D_TEXT -0.07f
#define D_SEL -0.14f
#define D_PIPS -0.15f
#define D_MISO -0.22f

#define CPS 40.0f          /* letters she reads per second */
#define SYLLABLE_GAP 0.085f
#define VOICE_PITCH 1.32f  /* quiz_angel_voice played a little high: angelic */
#define TAP_EVERY 0.55f    /* quill taps while she's impatient */
#define FLIP_TIME 0.45f    /* the hourglass turning over */

enum { PH_ANNOUNCE, PH_READ, PH_ASK, PH_FEEDBACK };
enum { M_SMILE, M_READ, M_IMPATIENT, M_HAPPY, M_SAD, M_SHOCKED };

static struct {
    int level;             /* 0..LEVELS-1, LEVELS when done */
    const Question *q;
    int order[4];          /* displayed slot -> answer index */
    int sel;
    float left;            /* seconds left for this question */
    int picked;            /* slot picked, -1 for timeout, -2 for cheat */
    bool right[LEVELS];
    float points;
    float t;
    int phase;
    float pt;              /* seconds in this phase */
    float frozen;          /* hourglass sand when the answer came in */
    int cue;               /* reaction sounds already played */
    /* the line she is saying, typing out */
    char line[320];        /* already wrapped to the bubble */
    int len;
    float scale;
    float shown;           /* letters out so far */
    float hold;            /* a breath at punctuation */
    float line_at;         /* pt when the line starts */
    float idle;            /* seconds since the line finished */
    float cool;            /* until the next syllable may sound */
    float mouth;           /* > 0 while her mouth is open */
    int syl;
    /* impatience */
    float tap_clock;
    float tap;             /* seconds since the quill last hit the scroll */
} Q;

/* ---- her voice ------------------------------------------------------------------ */

static void say(const char *s, float scale, float delay)
{
    ui_wrap(s, TW, scale, Q.line, sizeof(Q.line));
    Q.len = (int)strlen(Q.line);
    Q.scale = scale;
    Q.shown = 0;
    Q.hold = 0;
    Q.line_at = delay;
    Q.idle = 0;
    Q.mouth = 0;
    Q.syl = 0;
}

static bool typing(void) { return Q.shown < Q.len; }

static bool vowel(char c)
{
    c = (char)(c | 0x20);
    return c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'y';
}

/* One syllable: a bell-like blip, a little melody, rising before '?'. */
static void syllable(int i)
{
    static const float MELODY[5] = {1.0f, 1.05f, 0.98f, 1.07f, 1.02f};
    float contour = 1.0f;
    for (int j = i; j < Q.len && j < i + 8; j++) {
        char c = Q.line[j];
        if (c == '?' || c == '.' || c == '!') {
            float near = 1.0f - (float)(j - i) / 8.0f;
            contour = c == '?' ? 1.0f + 0.14f * near : c == '!' ? 1.0f + 0.07f * near : 1.0f - 0.1f * near;
            break;
        }
    }
    u32 h = (u32)(i + 1) * 2654435761u ^ (u32)(unsigned char)Q.line[i];
    float jitter = 1.0f + ((float)((h >> 8) % 61) - 30.0f) / 1000.0f;
    mg_sfx_pitch("quiz_angel_voice", VOICE_PITCH * MELODY[Q.syl % 5] * contour * jitter);
    Q.syl++;
    Q.mouth = 0.1f;
    Q.cool = SYLLABLE_GAP;
}

static void type_step(float dt)
{
    if (Q.mouth > 0)
        Q.mouth -= dt;
    Q.cool -= dt;
    if (Q.pt < Q.line_at)
        return;
    if (!typing()) {
        Q.idle += dt;
        return;
    }
    if (Q.hold > 0) {
        Q.hold -= dt;
        return;
    }
    int prev = (int)Q.shown;
    Q.shown += dt * CPS;
    int now = (int)Q.shown < Q.len ? (int)Q.shown : Q.len;
    for (int i = prev; i < now; i++) {
        char c = Q.line[i], p = i ? Q.line[i - 1] : ' ';
        if (vowel(c) && !vowel(p) && Q.cool <= 0)
            syllable(i);
        char nx = i + 1 < Q.len ? Q.line[i + 1] : ' ';
        bool end = nx == ' ' || nx == '\n';
        if ((c == ',' || c == ':') && end) {
            Q.hold = 0.12f;
        } else if ((c == '.' || c == '?' || c == '!') && end) {
            Q.hold = 0.28f;
        } else {
            continue;
        }
        Q.shown = (float)(i + 1);
        break;
    }
    if (Q.shown >= Q.len) {
        Q.shown = (float)Q.len;
        Q.mouth = 0;
    }
}

static void skip_line(void)
{
    Q.shown = (float)Q.len;
    Q.hold = 0;
    Q.mouth = 0;
    if (Q.pt < Q.line_at)
        Q.pt = Q.line_at;
}

/* ---- the run --------------------------------------------------------------------- */

static void begin_question(void)
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
    Q.picked = -1;
    Q.frozen = 0;
    Q.phase = PH_ANNOUNCE;
    Q.pt = 0;
    char buf[96];
    int n = Q.level + 1;
    if (Q.level == 0)
        snprintf(buf, sizeof(buf), "Five questions, A-30.\nQuestion 1 of %d.\nWorth 1.", LEVELS);
    else if (Q.level == LEVELS - 1)
        snprintf(buf, sizeof(buf), "The last one!\nQuestion %d of %d.\nWorth %d.", n, LEVELS, n);
    else
        snprintf(buf, sizeof(buf), "Question %d of %d.\nWorth %d.", n, LEVELS, n);
    say(buf, 0.62f, 0.2f);
    mg_sfx("quiz_next");
}

static void begin_read(void)
{
    Q.phase = PH_READ;
    Q.pt = 0;
    say(Q.q->q, 0.52f, 0.15f);
}

static void begin_ask(void)
{
    Q.phase = PH_ASK;
    Q.pt = 0;
    Q.left = TIME_LIMIT[Q.level];
    Q.tap_clock = 0;
    Q.tap = 1;
    mg_sfx("quiz_hourglass_flip");
}

static void start(u32 seed)
{
    (void)seed;
    memset(&Q, 0, sizeof(Q));
    begin_question();
}

static void answer(int slot, bool cheat)
{
    int weight = Q.level + 1;
    bool ok = cheat || (slot >= 0 && Q.order[slot] == 0);
    if (Q.phase == PH_READ)
        skip_line();
    Q.frozen = Q.phase == PH_ASK ? clampf(Q.left / TIME_LIMIT[Q.level], 0, 1) : 0;
    Q.picked = cheat ? -2 : slot;
    Q.right[Q.level] = ok;
    if (ok) {
        float speed = cheat ? 0 : clampf(Q.left / TIME_LIMIT[Q.level], 0, 1);
        Q.points += weight * (0.6f + 0.4f * speed);
    }
    Q.phase = PH_FEEDBACK;
    Q.pt = 0;
    Q.cue = 0;
    char buf[160];
    const char *a = Q.q->a[0];
    if (cheat)
        snprintf(buf, sizeof(buf), "Miso?! No cats in the exam hall! ...Correct, though.");
    else if (ok)
        snprintf(buf, sizeof(buf), SAY_RIGHT[Q.level], a);
    else if (slot < 0)
        snprintf(buf, sizeof(buf), "Time's up, I'm afraid. The answer: %s.", a);
    else
        snprintf(buf, sizeof(buf), SAY_WRONG[mg_randi(0, 2)], a);
    say(buf, 0.52f, cheat ? 0.95f : 0.5f);
    mg_sfx(cheat ? "quiz_miso_popin" : ok ? "quiz_right" : slot < 0 ? "quiz_timeout" : "quiz_wrong");
}

/* Reaction sounds a moment after the answer, in order. */
static void feedback_cues(void)
{
    if (Q.picked == -2) {
        if (Q.cue == 0 && Q.pt >= 0.3f) {
            Q.cue++;
            mg_sfx("quiz_cheat_answer");   /* Miso's answer lights up */
        }
        if (Q.cue == 1 && Q.pt >= 0.6f) {
            Q.cue++;
            mg_sfx("quiz_angel_gasp");
        }
        if (Q.cue == 2 && Q.idle >= 0.7f) {
            Q.cue++;
            mg_sfx("quiz_miso_popout");
        }
    } else if (Q.cue == 0 && Q.pt >= 0.32f) {
        Q.cue++;
        mg_sfx(Q.right[Q.level] ? "quiz_angel_pleased" : "quiz_angel_sigh");
    }
}

static bool impatient(void)
{
    return Q.phase == PH_ASK && Q.left < TIME_LIMIT[Q.level] * 0.45f;
}

static int touched_slot(const Input *in)
{
    if (!(in->down & KEY_TOUCH_))
        return -1;
    for (int i = 0; i < 4; i++)
        if (in->ty >= 24 + i * 44 && in->ty < 24 + i * 44 + 40 && in->tx >= 12 && in->tx < 308)
            return i;
    return -1;
}

static bool update(const Input *in, float dt, bool cheat)
{
    Q.t += dt;
    Q.pt += dt;
    Q.tap += dt;
    type_step(dt);

    switch (Q.phase) {
    case PH_ANNOUNCE:
        if (in->down & KEY_A_) {
            mg_sfx("quiz_read_skip");
            begin_read();
        } else if (!typing() && Q.idle >= 0.5f) {
            begin_read();
        }
        break;
    case PH_READ:
        if (cheat) {
            answer(-1, true);
        } else if ((in->down & KEY_A_) || touched_slot(in) >= 0) {
            mg_sfx("quiz_read_skip");
            skip_line();
            begin_ask();
        } else if (!typing() && Q.idle >= 0.35f) {
            begin_ask();
        }
        break;
    case PH_ASK:
        if (cheat) {
            answer(-1, true);
            break;
        }
        Q.left -= dt;
        if (Q.left <= 0) {
            Q.left = 0;
            answer(-1, false);
            break;
        }
        /* a soft tick through the last three seconds */
        if ((int)(Q.left + dt) != (int)Q.left && Q.left < 3.0f)
            mg_sfx("quiz_tick");
        if (impatient()) {
            Q.tap_clock += dt;
            if (Q.tap_clock >= TAP_EVERY) {
                Q.tap_clock -= TAP_EVERY;
                Q.tap = 0;
                mg_sfx("quiz_quill_tap");
            }
        }
        if (in->down & (KEY_UP_ | KEY_DOWN_)) {
            Q.sel = (Q.sel + ((in->down & KEY_UP_) ? 3 : 1)) % 4;
            mg_sfx("quiz_move");
        }
        if (in->down & KEY_A_) {
            answer(Q.sel, false);
            break;
        }
        {
            int s = touched_slot(in);
            if (s >= 0) {
                Q.sel = s;
                answer(s, false);
            }
        }
        break;
    case PH_FEEDBACK:
        feedback_cues();
        if ((in->down & KEY_A_) && Q.pt > 0.6f) {
            if (typing())
                skip_line();
            else
                Q.idle = 99;
        }
        if (!typing() && Q.pt >= Q.line_at && Q.idle >= 1.1f) {
            if (++Q.level >= LEVELS)
                return false;
            begin_question();
        }
        break;
    }
    return true;
}

/* ---- drawing helpers ---------------------------------------------------------- */

static const float PI_F = 3.14159265f;

/* A filled ellipse (rotated by `rot`), or the slice of it from a0 to a1. */
static void ell_part(int eye, float cx, float cy, float rx, float ry, float rot, float a0, float a1, int seg,
                     float d, u32 c)
{
    float ca = cosf(rot), sa = sinf(rot), px = 0, py = 0;
    for (int i = 0; i <= seg; i++) {
        float a = a0 + (a1 - a0) * (float)i / (float)seg;
        float ex = rx * cosf(a), ey = ry * sinf(a);
        float x = cx + ex * ca - ey * sa, y = cy + ex * sa + ey * ca;
        if (i)
            mg_tri(eye, cx, cy, px, py, x, y, d, c);
        px = x;
        py = y;
    }
}

static void ell(int eye, float cx, float cy, float rx, float ry, int seg, float d, u32 c)
{
    ell_part(eye, cx, cy, rx, ry, 0, 0, 2 * PI_F, seg, d, c);
}

/* An arc of an ellipse as a thick line. */
static void arc(int eye, float cx, float cy, float rx, float ry, float a0, float a1, int seg, float thick,
                float d, u32 c)
{
    float px = 0, py = 0;
    for (int i = 0; i <= seg; i++) {
        float a = a0 + (a1 - a0) * (float)i / (float)seg;
        float x = cx + rx * cosf(a), y = cy + ry * sinf(a);
        if (i)
            mg_line(eye, px, py, x, y, thick, d, c);
        px = x;
        py = y;
    }
}

static void quad(int eye, float x0, float y0, float x1, float y1, float x2, float y2, float x3, float y3,
                 float d, u32 c)
{
    mg_tri(eye, x0, y0, x1, y1, x2, y2, d, c);
    mg_tri(eye, x0, y0, x2, y2, x3, y3, d, c);
}

static void rrect(int eye, float x, float y, float w, float h, float r, float d, u32 c)
{
    ui_rrect(x + mg_shift(eye, d), y, w, h, r, c);
}

static float deg(float a) { return a * PI_F / 180.0f; }

/* ---- the background: heaven -------------------------------------------------- */

static void cloud(int eye, float x, float y, float s, float d, u32 c)
{
    mg_circle(eye, x - 22 * s, y + 4 * s, 13 * s, d, c);
    mg_circle(eye, x - 6 * s, y - 6 * s, 17 * s, d, c);
    mg_circle(eye, x + 14 * s, y - 2 * s, 14 * s, d, c);
    mg_circle(eye, x + 28 * s, y + 6 * s, 10 * s, d, c);
    mg_rect(eye, x - 22 * s, y + 4 * s, 50 * s, 11 * s, d, c);
}

static void draw_heaven(int eye)
{
    mg_sky(eye, RGBA(126, 164, 226, 255), RGBA(214, 222, 246, 255));
    /* the light behind her */
    float lx = VX + 6, ly = 34;
    float ra = Q.t * 0.05f;
    for (int i = 0; i < 8; i++) {
        float a = ra + i * (2 * PI_F / 8), w = 0.1f;
        mg_tri(eye, lx, ly, lx + cosf(a - w) * 330, ly + sinf(a - w) * 330, lx + cosf(a + w) * 330,
               ly + sinf(a + w) * 330, D_RAYS, RGBA(255, 250, 225, 26));
    }
    static const float GLOW_R[4] = {120, 84, 56, 34};
    for (int i = 0; i < 4; i++)
        mg_circle(eye, lx, ly, GLOW_R[i], D_LIGHT, RGBA(255, 248, 220, 34 + i * 14));
    /* far clouds drifting one way, near ones the other */
    for (int i = 0; i < 4; i++) {
        float x = fmodf(i * 130.0f + Q.t * 4.0f, 520.0f) - 60;
        cloud(eye, x, 214 - (i % 2) * 18, 1.3f, D_CLOUD_FAR, RGBA(246, 248, 255, 200));
    }
    for (int i = 0; i < 3; i++) {
        float x = 520.0f - fmodf(i * 180.0f + 60 + Q.t * 7.0f, 560.0f) - 40;
        cloud(eye, x, 70 + i * 52, 0.8f, D_CLOUD_NEAR, RGBA(255, 255, 255, 150));
    }
}

/* ---- Vael ------------------------------------------------------------------------ */

static const u32 SKIN = RGBA(240, 225, 215, 255);
static const u32 SKIN_EDGE = RGBA(205, 185, 175, 255);
static const u32 HAIR = RGBA(252, 228, 160, 255);    /* her name colour, #ffe9a8 */
static const u32 HAIR_EDGE = RGBA(214, 184, 116, 255);
static const u32 ROBE = RGBA(245, 240, 225, 255);
static const u32 ROBE_EDGE = RGBA(196, 188, 170, 255);
static const u32 TRIM = RGBA(220, 180, 80, 255);
static const u32 IRIS = RGBA(80, 130, 195, 255);
static const u32 LID = RGBA(70, 80, 110, 255);
static const u32 BROW = RGBA(196, 160, 92, 255);
static const u32 LIPS = RGBA(150, 55, 65, 255);
static const u32 INNER = RGBA(110, 35, 50, 255);
static const u32 TONGUE = RGBA(225, 115, 125, 255);

typedef struct {
    int eyes, brows, mouth, blush;   /* as in make_demo_assets.py's EXPRESSIONS */
    float gx, gy;                    /* where she looks, -1..1 */
} Face;

enum { E_OPEN, E_READ, E_SQUINT, E_DROOP, E_FLAT, E_WIDE, E_SHUT };
enum { B_RELAXED, B_LIFTED, B_HIGH, B_SAD, B_QUIZZICAL };
enum { MO_SMILE, MO_SOFT, MO_HAPPY, MO_SAD, MO_SIDE, MO_O };

/* Lower an upper eyelid: cover the eye above a line, then draw the line. */
static void lid(int eye, float oy, float x, float y, int s, float inner_y, float outer_y)
{
    float k = VS, rx = 12 * k, ry = 15 * k;
    float xo = x + s * (rx + 5 * k), xi = x - s * (rx + 5 * k), top = y - ry - 10 * k;
    (void)oy;
    quad(eye, xo, outer_y, xi, inner_y, xi, top, xo, top, D_FACE, SKIN);
    mg_line(eye, xo, outer_y, xi, inner_y, 6 * k, D_FACE, LID);
}

static void shine(int eye, float x, float y, float r)
{
    mg_circle(eye, x + 12 * VS * 0.35f, y - 15 * VS * 0.4f, r, D_FACE, MG_WHITE);
}

static void draw_eye(int eye, float oy, float x, float y, int s, const Face *f)
{
    float k = VS, rx = 12 * k, ry = 15 * k, sh = 4 * k;
    float ix = x + f->gx * rx * 0.5f, iy = y + f->gy * ry * 0.35f;
    switch (f->eyes) {
    case E_SHUT:
        arc(eye, x, y - ry * 0.2f, rx + 3 * k, ry * 0.7f, deg(20), deg(160), 4, 6 * k, D_FACE, LID);
        return;
    case E_WIDE: {
        float g = 5 * k;
        ell(eye, x, y, rx + g + 1, ry + g, 10, D_FACE, LID);
        ell(eye, x, y, rx + g, ry + g - 1, 10, D_FACE, MG_WHITE);
        ell(eye, x, y + k, rx * 0.55f, ry * 0.55f, 8, D_FACE, IRIS);
        mg_circle(eye, x + rx * 0.2f, y - ry * 0.25f + k, 1.0f, D_FACE, MG_WHITE);
        return;
    }
    default:
        break;
    }
    ell(eye, ix, iy, rx, ry, 10, D_FACE, IRIS);
    switch (f->eyes) {
    case E_SQUINT:   /* cheeks push the lower lids up: a smiling eye */
        ell_part(eye, x, y + ry * 1.575f, rx + 8 * k, ry * 1.425f, 0, PI_F, 2 * PI_F, 8, D_FACE, SKIN);
        shine(eye, ix, iy - ry * 0.05f, sh * 0.9f);
        break;
    case E_DROOP:    /* sad: the outer corners fall */
        shine(eye, ix, iy, sh);
        lid(eye, oy, x, y, s, y - ry * 0.95f, y - ry * 0.15f);
        break;
    case E_FLAT:     /* impatient: a flat half-lid */
        shine(eye, ix, iy + ry * 0.3f, sh * 0.7f);
        lid(eye, oy, x, y, s, y - ry * 0.2f, y - ry * 0.2f);
        break;
    case E_READ:     /* eyes down on the scroll */
        shine(eye, ix, iy + ry * 0.2f, sh * 0.8f);
        lid(eye, oy, x, y, s, y - ry * 0.3f, y - ry * 0.3f);
        break;
    default:
        shine(eye, ix, iy, sh);
        break;
    }
}

static void draw_brow(int eye, float x, float y, int s, int kind)
{
    float k = VS, bl = 17 * k, by = y - 32 * k, bw = 7 * k;
    float dy = 0, depth = 12;
    switch (kind) {
    case B_SAD: {   /* inner ends up: sympathy */
        float xo = x + s * bl, xi = x - s * bl;
        mg_line(eye, xo, by + 6 * k, xi, by - 9 * k, bw, D_FACE, BROW);
        return;
    }
    case B_LIFTED: dy = -4; break;
    case B_HIGH: dy = -9, depth = 14; break;
    case B_QUIZZICAL:   /* one brow up, one down */
        if (s > 0)
            dy = -12, depth = 14;
        else
            dy = 3, depth = 7;
        break;
    default: break;
    }
    arc(eye, x, by + (dy + depth / 4) * k, bl, depth * 0.75f * k, deg(200), deg(340), 4, bw, D_FACE, BROW);
}

static void draw_mouth(int eye, float oy, int kind, bool talk)
{
    float k = VS, mx = PX(320), my = PY(248), lw = 7 * k;
#define DSHAPE(top, w, h)                                                                          \
    do {                                                                                           \
        ell_part(eye, mx, (top), (w) * k, (h) * k, 0, 0, PI_F, 8, D_FACE, INNER);                  \
        if ((h) > 12)                                                                              \
            ell_part(eye, mx, (top) + (h) * k * 0.75f, (w) * k * 0.55f, (h) * k * 0.4f, 0, PI_F,  \
                     2 * PI_F, 6, D_FACE, TONGUE);                                                 \
    } while (0)
#define USHAPE(bottom, w, h) ell_part(eye, mx, (bottom), (w) * k, (h) * k, 0, PI_F, 2 * PI_F, 8, D_FACE, INNER)
#define OVAL(rx, ry, ox, oy2) ell(eye, mx + (ox) * k, my + (oy2) * k, (rx) * k, (ry) * k, 10, D_FACE, INNER)
#define ARC_UP(w, dp) arc(eye, mx, my - (dp) * k * 0.5f, (w) * k, (dp) * k, deg(15), deg(165), 6, lw, D_FACE, LIPS)
#define ARC_DOWN(w, dp) arc(eye, mx, my + (dp) * k * 0.8f, (w) * k, (dp) * k, deg(200), deg(340), 6, lw, D_FACE, LIPS)
    switch (kind) {
    case MO_SOFT:
        if (talk) DSHAPE(my - 5 * k, 14, 14); else ARC_UP(17, 7);
        break;
    case MO_SMILE:
        if (talk) DSHAPE(my - 8 * k, 24, 20); else ARC_UP(30, 13);
        break;
    case MO_HAPPY:
        if (talk) DSHAPE(my - 10 * k, 32, 30); else DSHAPE(my - 8 * k, 28, 22);
        break;
    case MO_SAD:
        if (talk) USHAPE(my + 12 * k, 15, 14); else ARC_DOWN(18, 9);
        break;
    case MO_SIDE:   /* pursed off to one side */
        if (talk) {
            OVAL(8, 9, 10, 1);
        } else {
            mg_line(eye, mx - 2 * k, my + 4 * k, mx + 12 * k, my + 2 * k, lw, D_FACE, LIPS);
            mg_line(eye, mx + 12 * k, my + 2 * k, mx + 24 * k, my - 2 * k, lw, D_FACE, LIPS);
        }
        break;
    case MO_O:
        if (talk) OVAL(13, 17, 0, 4); else OVAL(9, 11, 0, 2);
        break;
    }
#undef DSHAPE
#undef USHAPE
#undef OVAL
#undef ARC_UP
#undef ARC_DOWN
}

static void draw_face(int eye, float oy, const Face *f, bool talk)
{
    float k = VS, ey = PY(185);
    if (f->blush) {
        static const float T[3] = {0, 0.3f, 0.55f};
        float t = T[f->blush < 3 ? f->blush : 2];
        u32 c = RGBA((int)lerpf(240, 250, t), (int)lerpf(225, 150, t), (int)lerpf(215, 150, t), 255);
        for (int s = -1; s <= 1; s += 2)
            ell(eye, PX(320) + s * 66 * k, ey + 40 * k, 18 * k, 10 * k, 10, D_FACE, c);
    }
    for (int s = -1; s <= 1; s += 2) {
        float x = PX(320) + s * 45 * k;
        draw_eye(eye, oy, x, ey, s, f);
        draw_brow(eye, x, ey, s, f->brows);
    }
    draw_mouth(eye, oy, f->mouth, talk);
}

/* How she looks right now. */
static Face face_now(int *mood_out)
{
    Face f = {E_OPEN, B_LIFTED, MO_SMILE, 0, 0, 0};
    int mood = M_SMILE;
    if (Q.phase == PH_READ && typing())
        mood = M_READ;
    else if (Q.phase == PH_ASK && impatient())
        mood = M_IMPATIENT;
    else if (Q.phase == PH_FEEDBACK)
        mood = Q.picked == -2 ? M_SHOCKED : Q.right[Q.level] ? M_HAPPY : M_SAD;
    switch (mood) {
    case M_READ:
        f = (Face){E_READ, B_RELAXED, MO_SOFT, 0, 0.3f, 1.0f};
        break;
    case M_IMPATIENT: {
        /* glance at the hourglass, then back at you */
        bool glance = fmodf(Q.pt, 1.8f) < 0.75f;
        f = (Face){E_FLAT, B_QUIZZICAL, MO_SIDE, 0, glance ? -1.0f : 0, glance ? 0.9f : 0};
        break;
    }
    case M_HAPPY:
        f = (Face){E_SQUINT, B_LIFTED, MO_HAPPY, 1, 0, 0};
        break;
    case M_SAD:
        f = (Face){E_DROOP, B_SAD, MO_SAD, 0, 0, 0.3f};
        break;
    case M_SHOCKED:
        f = (Face){E_WIDE, B_HIGH, MO_O, 2, 0, 0};
        if (Q.pt < 0.6f)   /* she hasn't noticed the cat yet */
            f = (Face){E_OPEN, B_LIFTED, MO_SMILE, 0, 0, 0};
        break;
    default:
        break;
    }
    /* blink now and then, but not while shocked */
    if (mood != M_SHOCKED && mood != M_HAPPY && fmodf(Q.t + 0.7f, 3.7f) < 0.12f)
        f.eyes = E_SHUT;
    *mood_out = mood;
    return f;
}

/* A wing: Seraphiel's four overlapping feathers per side, turned about the
 * shoulder by `lift` (radians, up). */
static void draw_wing(int eye, float oy, int side, float lift)
{
    float pvx = PX(320 + side * 100), pvy = PY(330);
    float a = -side * lift, ca = cosf(a), sa = sinf(a);
    for (int pass = 0; pass < 2; pass++)
        for (int kk = 0; kk < 4; kk++) {
            float cx = PX(320 + side * (120 + kk * 40 + 95)), cy = PY(235 + kk * 60);
            float dx = cx - pvx, dy = cy - pvy;
            float x = pvx + dx * ca - dy * sa, y = pvy + dx * sa + dy * ca;
            float r = 95 * VS;
            if (pass == 0)
                mg_circle(eye, x, y, r + 1.2f, D_WING, RGBA(150, 160, 200, 255));
            else
                mg_circle(eye, x, y, r, D_WING, RGBA(255, 255, 255, 255 - kk * 14));
        }
}

/* The quill in her right hand: `lift` raises the nib off the scroll. */
static void draw_quill(int eye, float oy, float lift)
{
    float hx = PX(320 + 72), hy = PY(472);
    float th = deg(-62) - lift, dx = cosf(th), dy = sinf(th);
    float tipx = hx - dx * 40 * VS, tipy = hy - dy * 40 * VS;
    float endx = hx + dx * 165 * VS, endy = hy + dy * 165 * VS;
    float fx = hx + dx * 100 * VS, fy = hy + dy * 100 * VS;
    ell_part(eye, fx, fy, 64 * VS + 1, 15 * VS + 1, th, 0, 2 * PI_F, 8, D_HANDS, RGBA(170, 176, 204, 255));
    ell_part(eye, fx, fy, 64 * VS, 15 * VS, th, 0, 2 * PI_F, 8, D_HANDS, RGBA(255, 255, 255, 255));
    mg_line(eye, tipx, tipy, endx, endy, 1.2f, D_HANDS, RGBA(150, 120, 80, 255));
    mg_line(eye, tipx, tipy, tipx + dx * 10 * VS, tipy + dy * 10 * VS, 1.8f, D_HANDS, RGBA(60, 50, 60, 255));
    mg_circle(eye, hx, hy, 16 * VS, D_HANDS, SKIN);
}

static void draw_vael(int eye)
{
    int mood;
    Face f = face_now(&mood);
    float oy = VTOP + sinf(Q.t * 1.6f) * 1.5f;
    float k = VS;

    /* wings: a gentle flap; up when pleased, flared when shocked, low when sad */
    float lift = 0.07f * sinf(Q.t * 2.2f);
    if (mood == M_HAPPY)
        lift = 0.1f + 0.1f * sinf(Q.t * 6);
    else if (mood == M_SAD)
        lift = -0.1f + 0.03f * sinf(Q.t * 1.5f);
    else if (mood == M_SHOCKED && Q.pt >= 0.6f)
        lift = 0.32f * clampf((Q.pt - 0.6f) / 0.12f, 0, 1) + 0.03f * sinf(Q.t * 14);
    draw_wing(eye, oy, -1, lift);
    draw_wing(eye, oy, 1, lift);

    /* pleased: a warm glow about her */
    float glow = mood == M_HAPPY ? clampf(Q.pt / 0.5f, 0, 1) * (0.85f + 0.15f * sinf(Q.t * 5)) : 0;
    if (glow > 0)
        for (int i = 0; i < 3; i++)
            mg_circle(eye, VX, PY(230), 100 - i * 24, D_GLOW, RGBA(255, 222, 120, (int)(glow * (70 + i * 30))));

    /* long hair behind */
    rrect(eye, PX(190), PY(70), 260 * k, 350 * k, 90 * k, D_HAIR, HAIR);

    /* robe with gold trim (sleeves drawn with the hands) */
    float bot = 250;   /* below the screen */
    float t0 = PY(330), hw0 = 100 * k, hwb = hw0 + 60 * k * (bot - t0) / (370 * k);
    quad(eye, VX - hw0 - 1, t0 - 1, VX + hw0 + 1, t0 - 1, VX + hwb + 1, bot, VX - hwb - 1, bot, D_BODY, ROBE_EDGE);
    quad(eye, VX - hw0, t0, VX + hw0, t0, VX + hwb, bot, VX - hwb, bot, D_BODY, ROBE);
    mg_line(eye, VX - hw0 + 2, t0, VX - hwb + 2, bot, 2.2f, D_BODY, TRIM);
    mg_line(eye, VX + hw0 - 2, t0, VX + hwb - 2, bot, 2.2f, D_BODY, TRIM);
    mg_rect(eye, PX(220), PY(360), 200 * k, 20 * k, D_BODY, TRIM);
    mg_rect(eye, PX(360), PY(400), 12 * k, 25 * k, D_BODY, TRIM);   /* one rank bar: an adjutant */

    /* neck, head */
    mg_rect(eye, PX(292), PY(260), 56 * k, 80 * k, D_BODY, SKIN);
    ell(eye, VX, PY(180), 110 * k + 1, 120 * k + 1, 14, D_FACE, SKIN_EDGE);
    ell(eye, VX, PY(180), 110 * k, 120 * k, 14, D_FACE, SKIN);

    /* halo (behind her fringe), brighter when pleased */
    float hy = PY(30) + sinf(Q.t * 1.6f + 0.6f) * 1.2f;
    u32 halo = mood == M_HAPPY ? RGBA(255, 236, 150, 255) : RGBA(255, 210, 90, 255);
    if (mood == M_HAPPY)
        arc(eye, VX, hy, 95 * k, 22 * k, 0, 2 * PI_F, 16, 9 * k + 3, D_HAIR, RGBA(255, 240, 180, 90));
    arc(eye, VX, hy, 95 * k, 22 * k, 0, 2 * PI_F, 16, 9 * k, D_HAIR, halo);

    /* her fringe: the top half of an ellipse */
    ell_part(eye, VX, PY(122.5f), 118 * k + 1, 77.5f * k + 1, 0, PI_F, 2 * PI_F, 10, D_FACE, HAIR_EDGE);
    ell_part(eye, VX, PY(122.5f), 118 * k, 77.5f * k, 0, PI_F, 2 * PI_F, 10, D_FACE, HAIR);

    draw_face(eye, oy, &f, Q.mouth > 0);

    /* shocked: two little lines of alarm */
    if (mood == M_SHOCKED && Q.pt >= 0.6f) {
        float jump = 2 * sinf(clampf((Q.pt - 0.6f) / 0.25f, 0, 1) * PI_F);
        mg_text(eye, "!?", PX(445), PY(40) - jump, 0.8f, D_FACE - 0.02f, RGBA(226, 84, 84, 255));
    }

    /* sleeves and the scroll she reads from */
    mg_line(eye, PX(218), PY(345), PX(222), PY(490), 48 * k + 2, D_HANDS, ROBE_EDGE);
    mg_line(eye, PX(218), PY(345), PX(222), PY(490), 48 * k, D_HANDS, ROBE);
    mg_line(eye, PX(422), PY(345), PX(392), PY(462), 44 * k + 2, D_HANDS, ROBE_EDGE);
    mg_line(eye, PX(422), PY(345), PX(392), PY(462), 44 * k, D_HANDS, ROBE);
    mg_rect(eye, PX(230), PY(448), 160 * k, 96 * k, D_HANDS, RGBA(252, 247, 230, 255));
    mg_rect(eye, PX(222), PY(436), 176 * k, 16 * k, D_HANDS, RGBA(222, 204, 160, 255));
    mg_rect(eye, PX(222), PY(540), 176 * k, 16 * k, D_HANDS, RGBA(222, 204, 160, 255));
    for (int i = 0; i < 4; i++)
        mg_line(eye, PX(248), PY(470 + i * 20), PX(248 + 110 - (i % 2) * 34), PY(470 + i * 20), 1.2f,
                D_HANDS, RGBA(176, 166, 150, 255));
    mg_circle(eye, PX(226), PY(492), 17 * k, D_HANDS, SKIN);

    /* the quill: resting, or tapping the scroll when she's impatient */
    float ql = 0.28f + 0.04f * sinf(Q.t * 1.3f);
    if (mood == M_IMPATIENT)
        ql = 0.3f * sinf(PI_F * clampf(Q.tap / TAP_EVERY, 0, 1));
    else if (mood == M_READ)
        ql = 0.18f;
    draw_quill(eye, oy, ql);
    if (mood == M_IMPATIENT && Q.tap < 0.14f) {   /* tap! */
        float nx = PX(320 + 72) - cosf(deg(-62)) * 40 * VS, ny = PY(472) - sinf(deg(-62)) * 40 * VS;
        for (int i = -1; i <= 1; i++)
            mg_line(eye, nx + i * 4, ny + 3, nx + i * 7, ny + 7 - (i == 0) * 1, 1, D_HANDS,
                    RGBA(120, 100, 80, 255));
    }

    /* and sparkles in front of her */
    for (int i = 0; glow > 0 && i < 6; i++) {
        float a = Q.t * 0.8f + i * 1.047f, r = 66 + 8 * sinf(Q.t * 3 + i);
        float tw = 0.5f + 0.5f * sinf(Q.t * 7 + i * 2);
        float sx = VX + cosf(a) * r, sy = PY(230) + sinf(a) * r * 0.8f, sz = 1.5f + 2.5f * tw;
        u32 c = rgba_alpha(RGBA(255, 200, 80, 255), glow);
        mg_tri(eye, sx - sz, sy, sx + sz, sy, sx, sy - sz * 2.2f, D_HANDS - 0.02f, c);
        mg_tri(eye, sx - sz, sy, sx + sz, sy, sx, sy + sz * 2.2f, D_HANDS - 0.02f, c);
    }
}

/* ---- the hourglass ----------------------------------------------------------- */

static void draw_hourglass(int eye)
{
    /* sand above: f; the glass turns over when the clock starts */
    float f = 0, ang = 0;
    bool flowing = false;
    if (Q.phase == PH_ASK) {
        if (Q.pt < FLIP_TIME) {
            float p = Q.pt / FLIP_TIME;
            ang = PI_F * (p * p * (3 - 2 * p));
        } else {
            f = clampf(Q.left / TIME_LIMIT[Q.level], 0, 1);
            flowing = true;
        }
    } else if (Q.phase == PH_FEEDBACK) {
        f = Q.frozen;
    }
    float d = D_HOURGLASS, ca = cosf(ang), sa = sinf(ang);
    const float W = 11, H = 19;
#define RX(lx, ly) (HGX + (lx) * ca - (ly) * sa)
#define RY(lx, ly) (HGY + (lx) * sa + (ly) * ca)
#define QUAD(x0, y0, x1, y1, c)                                                                    \
    quad(eye, RX(x0, y0), RY(x0, y0), RX(x1, y0), RY(x1, y0), RX(x1, y1), RY(x1, y1), RX(x0, y1),  \
         RY(x0, y1), d, c)
#define TRI(x0, y0, x1, y1, x2, y2, c) mg_tri(eye, RX(x0, y0), RY(x0, y0), RX(x1, y1), RY(x1, y1), RX(x2, y2), RY(x2, y2), d, c)
    /* its cloud */
    cloud(eye, HGX + 2, HGY + 30, 0.62f, d + 0.02f, RGBA(255, 255, 255, 240));
    /* glass */
    u32 glass = RGBA(255, 255, 255, 120), sand = RGBA(236, 188, 104, 255);
    TRI(-W, -H, W, -H, 0, -1, glass);
    TRI(-W, H, W, H, 0, 1, glass);
    TRI(-1.5f, -1.5f, 1.5f, -1.5f, 0, 1.5f, glass);
    if (f > 0) {   /* sand on top, sinking towards the neck */
        float h = (H - 1) * sqrtf(f) * 0.9f, w = W * h / H;
        TRI(-w, -h, w, -h, 0, -0.5f, sand);
    }
    float g = 1 - f;
    if (g > 0.02f) {   /* the heap below */
        float bw = W * clampf(0.35f + g, 0, 1) - 1, bh = (H - 2) * g * 0.8f;
        TRI(-bw, H - 0.5f, bw, H - 0.5f, 0, H - 0.5f - bh, sand);
    }
    if (flowing && f > 0)
        mg_line(eye, RX(0, 0), RY(0, 0), RX(0, H - 1), RY(0, H - 1), 1, d, sand);
    /* frame */
    u32 gold = RGBA(214, 168, 70, 255);
    QUAD(-W - 3, -H - 4, W + 3, -H, gold);
    QUAD(-W - 3, H, W + 3, H + 4, gold);
    mg_line(eye, RX(-W - 1.5f, -H), RY(-W - 1.5f, -H), RX(-W - 1.5f, H), RY(-W - 1.5f, H), 1.6f, d, gold);
    mg_line(eye, RX(W + 1.5f, -H), RY(W + 1.5f, -H), RX(W + 1.5f, H), RY(W + 1.5f, H), 1.6f, d, gold);
#undef RX
#undef RY
#undef QUAD
#undef TRI
}

/* ---- Miso, popping up to answer ------------------------------------------------- */

static void draw_miso(int eye)
{
    if (Q.phase != PH_FEEDBACK || Q.picked != -2)
        return;
    /* up with a little overshoot, down again before the next question */
    float p = clampf(Q.pt / 0.3f, 0, 1);
    float up = p < 1 ? 1.15f * sinf(p * 1.9f) / sinf(1.9f) : 1;
    if (Q.pt >= 0.3f && Q.pt < 0.5f)
        up = 1 + 0.1f * sinf((Q.pt - 0.3f) / 0.2f * PI_F);
    if (!typing() && Q.pt >= Q.line_at)
        up *= 1 - clampf((Q.idle - 0.7f) / 0.3f, 0, 1);
    if (up <= 0.01f)
        return;
    float x = 366, y = 262 - 50 * up, d = D_MISO;
    u32 fur = RGBA(235, 150, 70, 255), dark = RGBA(200, 110, 45, 255), chest = RGBA(250, 240, 225, 255);
    u32 ink = RGBA(60, 40, 30, 255), pink = RGBA(240, 160, 160, 255);
    mg_circle(eye, x, y + 30, 22, d, fur);
    mg_circle(eye, x, y + 34, 12, d, chest);
    for (int s = -1; s <= 1; s += 2) {
        mg_tri(eye, x + s * 17, y - 4, x + s * 12, y - 25, x + s * 2, y - 14, d, fur);
        mg_tri(eye, x + s * 14, y - 7, x + s * 11, y - 20, x + s * 5, y - 13, d, pink);
    }
    mg_circle(eye, x, y, 17, d, fur);
    mg_line(eye, x - 5, y - 16, x - 3, y - 10, 2, d, dark);
    mg_line(eye, x + 5, y - 16, x + 3, y - 10, 2, d, dark);
    /* ^ ^ eyes, pleased with herself */
    for (int s = -1; s <= 1; s += 2)
        arc(eye, x + s * 7, y + 1, 4.5f, 4, deg(200), deg(340), 3, 1.6f, d, ink);
    mg_tri(eye, x - 2, y + 4, x + 2, y + 4, x, y + 6.5f, d, pink);
    arc(eye, x - 2.5f, y + 6.5f, 2.5f, 2, 0, PI_F, 3, 1.2f, d, ink);
    arc(eye, x + 2.5f, y + 6.5f, 2.5f, 2, 0, PI_F, 3, 1.2f, d, ink);
    for (int s = -1; s <= 1; s += 2) {
        mg_line(eye, x + s * 8, y + 5, x + s * 24, y + 2, 0.8f, d, RGBA(255, 255, 255, 220));
        mg_line(eye, x + s * 8, y + 7, x + s * 24, y + 9, 0.8f, d, RGBA(255, 255, 255, 220));
    }
    /* a paw up: she knew it */
    float wave = sinf(Q.t * 10) * 2;
    mg_circle(eye, x - 22, y + 10 + wave, 6, d, fur);
    mg_circle(eye, x + 12, y + 24, 6, d, fur);
    if (Q.pt >= 0.3f) {
        rrect(eye, x - 74, y - 6, 40, 16, 8, d, RGBA(255, 255, 255, 240));
        mg_text(eye, "Meow.", x - 69, y - 5, 0.42f, d, MG_INK);
    }
}

/* ---- the bubble ------------------------------------------------------------------- */

/* The first `n` bytes of her line, with whole UTF-8 characters. */
static void line_prefix(char *out, size_t cap)
{
    int n = (int)Q.shown;
    if (n > Q.len)
        n = Q.len;
    while (n > 0 && n < Q.len && ((unsigned char)Q.line[n] & 0xC0) == 0x80)
        n--;
    if ((size_t)n >= cap)
        n = (int)cap - 1;
    memcpy(out, Q.line, (size_t)n);
    out[n] = 0;
}

static bool reveal(void)
{
    return Q.phase == PH_FEEDBACK && (Q.picked != -2 || Q.pt >= 0.3f);
}

static void draw_bubble(int eye)
{
    u32 edge = RGBA(232, 196, 110, 255), paper = RGBA(255, 253, 246, 245);
    /* tail towards her mouth */
    float tx = 150, ty = VTOP + 248 * VS - 2;
    mg_tri(eye, BX + 2, BY + 54, BX + 2, BY + 80, tx - 1.5f, ty, D_BUBBLE, edge);
    rrect(eye, BX - 2, BY - 2, BW + 4, BH + 4, 14, D_BUBBLE, edge);
    rrect(eye, BX, BY, BW, BH, 12, D_BUBBLE, paper);
    mg_tri(eye, BX + 4, BY + 57, BX + 4, BY + 77, tx + 2, ty, D_BUBBLE, paper);

    char buf[320];
    line_prefix(buf, sizeof(buf));
    if (Q.phase == PH_ANNOUNCE) {
        float lines = 1;
        for (const char *p = Q.line; *p; p++)
            lines += *p == '\n';
        float y = BY + (BH - lines * gfx_line_height(Q.scale)) / 2;
        mg_text(eye, buf, TX + 6, y, Q.scale, D_TEXT, MG_INK);
        return;
    }
    mg_text(eye, buf, TX, TY, Q.scale, D_TEXT, MG_INK);

    /* the answers, once she has asked */
    if (Q.phase != PH_ASK && Q.phase != PH_FEEDBACK)
        return;
    mg_line(eye, TX, ANS_Y - 5, TX + TW, ANS_Y - 5, 1, D_BUBBLE, RGBA(232, 210, 160, 255));
    for (int i = 0; i < 4; i++) {
        int ai = Q.order[i];
        const char *a = Q.q->a[ai];
        float y = ANS_Y + i * ANS_H, dep = D_TEXT;
        u32 pill = 0, fg = MG_INK;
        if (reveal() && ai == 0)
            pill = RGBA(110, 210, 140, 255);
        else if (reveal() && i == Q.picked)
            pill = RGBA(226, 104, 104, 255), fg = MG_WHITE;
        else if (Q.phase == PH_ASK && i == Q.sel)
            pill = RGBA(255, 214, 120, 200), dep = D_SEL;
        else
            fg = RGBA(70, 66, 90, 255);
        if (pill)
            rrect(eye, TX - 4, y, TW + 8, ANS_H - 1, 7, dep + 0.02f, pill);
        float sc = 0.46f;
        while (sc > 0.34f && gfx_text_width(a, sc) > TW - 4)
            sc -= 0.02f;
        mg_text(eye, a, TX + 2, y + (ANS_H - 1 - gfx_line_height(sc)) / 2, sc, dep, fg);
    }
}

static void draw_top(int eye)
{
    draw_heaven(eye);
    draw_vael(eye);
    draw_hourglass(eye);
    if (Q.level >= LEVELS || !Q.q)
        return;
    draw_bubble(eye);

    /* level pips */
    for (int i = 0; i < LEVELS; i++) {
        bool done = i < Q.level || (i == Q.level && Q.phase == PH_FEEDBACK && reveal());
        u32 c = done ? (Q.right[i] ? RGBA(90, 200, 120, 255) : RGBA(220, 96, 96, 255))
              : i == Q.level ? MG_GOLD : RGBA(255, 255, 255, 140);
        mg_circle(eye, 258 + i * 18, 15, 5.5f, D_PIPS, RGBA(255, 255, 255, 200));
        mg_circle(eye, 258 + i * 18, 15, 4, D_PIPS, c);
    }

    /* the clock, once it runs */
    if (Q.phase == PH_ASK || (Q.phase == PH_FEEDBACK && Q.picked != -2)) {
        float fr = Q.phase == PH_ASK ? Q.left / TIME_LIMIT[Q.level] : Q.frozen;
        mg_rect(eye, BX + 6, BY + BH + 6, BW - 12, 5, D_PIPS, RGBA(255, 255, 255, 120));
        mg_rect(eye, BX + 6, BY + BH + 6, (BW - 12) * fr, 5, D_PIPS,
                fr > 0.3f ? RGBA(236, 188, 104, 255) : RGBA(230, 110, 96, 255));
    }
    draw_miso(eye);
}

static void draw_bottom(void)
{
    char buf[64];
    int n = Q.level < LEVELS ? Q.level + 1 : LEVELS;
    snprintf(buf, sizeof(buf), "Question %d of %d  (worth %d)", n, LEVELS, n);
    gfx_text(buf, 12, 4, 0.45f, MG_GOLD);
    if (!Q.q || Q.level >= LEVELS)
        return;
    if (Q.phase == PH_ASK) {
        snprintf(buf, sizeof(buf), "%d s", (int)ceilf(Q.left));
        gfx_text(buf, 308 - gfx_text_width(buf, 0.45f), 4, 0.45f,
                 impatient() ? RGBA(240, 130, 110, 255) : MG_WHITE);
    }
    bool hidden = Q.phase == PH_ANNOUNCE || Q.phase == PH_READ;
    for (int i = 0; i < 4; i++) {
        int ai = Q.order[i];
        float y = 24 + i * 44;
        if (hidden) {
            gfx_rect(12, y, 296, 40, RGBA(255, 255, 255, 22));
            continue;
        }
        u32 bg = i == Q.sel && Q.phase == PH_ASK ? RGBA(255, 255, 255, 230) : RGBA(255, 255, 255, 40);
        u32 fg = i == Q.sel && Q.phase == PH_ASK ? MG_INK : MG_WHITE;
        if (reveal()) {
            if (ai == 0)
                bg = RGBA(110, 210, 140, 255), fg = MG_INK;
            else if (i == Q.picked)
                bg = RGBA(220, 100, 100, 255), fg = MG_WHITE;
        }
        gfx_rect(12, y, 296, 40, bg);
        float sc = 0.5f;
        while (sc > 0.36f && gfx_text_width(Q.q->a[ai], sc) > 280)
            sc -= 0.02f;
        gfx_text(Q.q->a[ai], 160 - gfx_text_width(Q.q->a[ai], sc) / 2, y + (40 - gfx_line_height(sc)) / 2,
                 sc, fg);
    }
    if (hidden) {
        const char *s = Q.phase == PH_ANNOUNCE ? "Vael is announcing..." : "Vael is reading the question...";
        gfx_text(s, 160 - gfx_text_width(s, 0.45f) / 2, 68 + (40 - gfx_line_height(0.45f)) / 2, 0.45f,
                 RGBA(200, 200, 210, 255));
        gfx_text("A: skip", 12, 212, 0.45f, RGBA(152, 152, 159, 255));
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

/* The bot listens to question 1 and touches the right answer, skips the
 * reading of 2 and picks a wrong one, lets Miso answer 3, waits on 4 until
 * Vael taps her quill and then answers right, and lets 5 run out. */
static void bot(Input *in, float t)
{
    static float last;
    if (t < last)
        last = 0;
    if (t - last < 0.25f)
        return;
    int right = 0;
    for (int i = 0; i < 4; i++)
        if (Q.order[i] == 0)
            right = i;
    switch (Q.phase) {
    case PH_ANNOUNCE:
        if (Q.level == 1 && Q.pt > 0.7f) {
            in->down |= KEY_A_;
            last = t;
        }
        break;
    case PH_READ:
        if (Q.level == 1 && Q.pt > 0.8f) {
            in->down |= KEY_A_;
            last = t;
        }
        break;
    case PH_ASK: {
        if (Q.level == 0 && Q.pt > 2.5f) {
            in->down |= KEY_TOUCH_;
            in->tx = 160;
            in->ty = 24 + right * 44 + 20;
            last = t;
        } else if (Q.level == 1 && Q.pt > 1.5f) {
            int wrong = (right + 2) % 4;
            in->down |= Q.sel != wrong ? KEY_DOWN_ : KEY_A_;
            last = t;
        } else if (Q.level == 2 && Q.pt > 1.8f) {
            in->down |= KEY_L_;
            last = t;
        } else if (Q.level == 3 && Q.left < 3.2f) {
            in->down |= Q.sel != right ? KEY_DOWN_ : KEY_A_;
            last = t;
        }
        break;
    }
    default:
        break;
    }
}

/* the cheat helps while a question is being read or asked */
static bool can_cheat(void) { return Q.level < LEVELS && (Q.phase == PH_READ || Q.phase == PH_ASK); }

const MiniGame MG_QUIZ = {
    .id = "quiz",
    .title = "The Big Questions",
    .rules = "Adjutant Vael reads you five questions\n"
             "on philosophy and the world's religions.\n"
             "Each is harder and worth more. Her clock\n"
             "starts once she has read the question:\n"
             "answer fast for a bonus.",
    .controls = "Touch an answer, or\nD-pad: choose    A: answer\nA while she reads: skip\nSTART: pause",
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
