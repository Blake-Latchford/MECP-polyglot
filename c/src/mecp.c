/* MECP encoder/decoder. See include/mecp.h and spec/conformance.md.
 *
 * C has no regex engine, so each upstream decode pattern is matched by hand.
 * Each matcher returns what the regex would return (leftmost-first,
 * backtracking included); the comment above it names the pattern and says
 * where backtracking can change the result.
 */
#include "mecp.h"
#include "mecp_boundary.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INT_MAX32 2147483647L

/* ---------- UTF-8 and character classes ---------- */

/* Decode one code point at p (p < end). Returns its byte length (>= 1).
 * Malformed bytes decode as a single code point U+FFFD of length 1. */
static size_t utf8_next(const char *p, const char *end, uint32_t *cp)
{
    const unsigned char *u = (const unsigned char *)p;
    size_t avail = (size_t)(end - p);
    size_t n;
    uint32_t c;

    if (u[0] < 0x80) { *cp = u[0]; return 1; }
    if ((u[0] & 0xE0) == 0xC0) { n = 2; c = u[0] & 0x1F; }
    else if ((u[0] & 0xF0) == 0xE0) { n = 3; c = u[0] & 0x0F; }
    else if ((u[0] & 0xF8) == 0xF0) { n = 4; c = u[0] & 0x07; }
    else { *cp = 0xFFFD; return 1; }

    if (n > avail) { *cp = 0xFFFD; return 1; }
    for (size_t i = 1; i < n; i++) {
        if ((u[i] & 0xC0) != 0x80) { *cp = 0xFFFD; return 1; }
        c = (c << 6) | (u[i] & 0x3F);
    }
    *cp = c;
    return n;
}

/* ECMAScript whitespace: what encode trims from freetext. */
static bool is_ws(uint32_t c)
{
    return (c >= 0x09 && c <= 0x0D) || c == 0x20 || c == 0xA0 || c == 0x1680 ||
           (c >= 0x2000 && c <= 0x200A) || c == 0x2028 || c == 0x2029 ||
           c == 0x202F || c == 0x205F || c == 0x3000 || c == 0xFEFF;
}

/* Line breaks (the message pattern excludes them from freetext). */
static bool is_line_break(uint32_t c)
{
    return c == '\n' || c == '\f' || c == '\r' || c == 0x85 || c == 0x2028 || c == 0x2029;
}

/* Never on the wire: line breaks, BOM and Unicode whitespace (rule 8). */
static bool is_forbidden(uint32_t c)
{
    return is_line_break(c) || c == 0xFEFF || c == 0xA0 || c == 0x1680 ||
           (c >= 0x2000 && c <= 0x200A) || c == 0x202F || c == 0x205F || c == 0x3000;
}

static bool in_boundary(uint32_t c)
{
    for (size_t i = 0; i < sizeof mecp_boundary / sizeof mecp_boundary[0]; i++)
        if (c >= mecp_boundary[i].lo && c <= mecp_boundary[i].hi) return true;
    return false;
}

/* Byte length of the B code point at p, or 0 if there is none. */
static size_t b_len(const char *p, const char *end)
{
    uint32_t c;
    size_t n;
    if (p >= end) return 0;
    n = utf8_next(p, end, &c);
    return in_boundary(c) ? n : 0;
}

/* The right boundary (B|$) can follow p. */
static bool right_ok(const char *p, const char *end)
{
    return p == end || b_len(p, end) > 0;
}

static bool is_digit(char c) { return c >= '0' && c <= '9'; }
static bool is_alpha(char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); }
static bool is_alnum(char c) { return is_digit(c) || is_alpha(c); }
static char to_lower(char c) { return c >= 'A' && c <= 'Z' ? (char)(c + 32) : c; }
static char to_upper(char c) { return c >= 'a' && c <= 'z' ? (char)(c - 32) : c; }

/* End of the run of ASCII digits starting at p. */
static const char *digits(const char *p, const char *end)
{
    while (p < end && is_digit(*p)) p++;
    return p;
}

/* ASCII case-insensitive match of lowercase `word` at p; returns the end or NULL. */
static const char *word_ci(const char *p, const char *end, const char *word)
{
    for (; *word; word++, p++)
        if (p >= end || to_lower(*p) != *word) return NULL;
    return p;
}

/* Optional single space ( ?). */
static const char *opt_space(const char *p, const char *end)
{
    return p < end && *p == ' ' ? p + 1 : p;
}

/* Parse an ASCII digit run, clamping huge values to the int32 maximum. */
static int32_t clamp_int(const char *p, const char *e)
{
    long long v = 0;
    for (; p < e; p++) {
        v = v * 10 + (*p - '0');
        if (v > INT_MAX32) return (int32_t)INT_MAX32;
    }
    return (int32_t)v;
}

static int32_t clamp_ll(long long v) { return v > INT_MAX32 ? (int32_t)INT_MAX32 : (int32_t)v; }

/* ---------- Decode patterns ---------- */

typedef struct {
    const char *b, *e; /* NULL b: the group did not take part */
} span_t;

typedef struct {
    const char *start; /* start of the whole match, left boundary included */
    const char *end;   /* end of the token, i.e. start of the right boundary */
    span_t g[2];       /* capture groups 1 and 2 */
} match_t;

/* Try the pattern at `at` (text is the freetext start, for ^). On success
 * set m->end and m->g, having checked that (B|$) follows. */
typedef bool (*pattern_fn)(const char *text, const char *at, const char *end, match_t *m);

static bool set1(match_t *m, const char *b, const char *e, const char *tok_end, const char *end)
{
    if (!right_ok(tok_end, end)) return false;
    m->g[0].b = b; m->g[0].e = e;
    m->g[1].b = NULL; m->g[1].e = NULL;
    m->end = tok_end;
    return true;
}

/* 0*([1-9][0-9]*) ?[Pp][Aa][Xx]
 * 0* must take every zero, since [1-9] cannot match one. */
static bool pat_pax(const char *text, const char *p, const char *end, match_t *m)
{
    const char *g;
    (void)text;
    while (p < end && *p == '0') p++;
    if (p >= end || *p < '1' || *p > '9') return false;
    g = p;
    p = digits(p, end);
    {
        const char *q = word_ci(opt_space(p, end), end, "pax");
        return q && set1(m, g, p, q, end);
    }
}

/* [+-]?[0-9]+\.[0-9]+ ; returns the end or NULL. Greedy runs are final:
 * what follows is never a digit. */
static const char *decimal(const char *p, const char *end)
{
    const char *q;
    if (p < end && (*p == '+' || *p == '-')) p++;
    q = digits(p, end);
    if (q == p || q >= end || *q != '.') return NULL;
    p = digits(q + 1, end);
    return p == q + 1 ? NULL : p;
}

/* ([+-]?[0-9]+\.[0-9]+), ?([+-]?[0-9]+\.[0-9]+) */
static bool pat_gps(const char *text, const char *p, const char *end, match_t *m)
{
    const char *a = p, *ae = decimal(p, end), *b, *be;
    (void)text;
    if (!ae || ae >= end || *ae != ',') return false;
    b = opt_space(ae + 1, end);
    be = decimal(b, end);
    if (!be || !right_ok(be, end)) return false;
    m->g[0].b = a; m->g[0].e = ae;
    m->g[1].b = b; m->g[1].e = be;
    m->end = be;
    return true;
}

/* @([01]?[0-9]|2[0-3]):?([0-5][0-9])
 * Backtracking matters: try the hour forms in regex order ([01] then [0-9],
 * [0-9] alone, 2[0-3]) and, for each, the colon taken then skipped. */
static bool pat_timestamp(const char *text, const char *p, const char *end, match_t *m)
{
    const char *hours[3];
    int n = 0;
    (void)text;
    if (p >= end || *p != '@') return false;
    p++;
    if (p + 1 < end && (*p == '0' || *p == '1') && is_digit(p[1])) hours[n++] = p + 2;
    if (p < end && is_digit(*p)) hours[n++] = p + 1;
    if (p + 1 < end && *p == '2' && p[1] >= '0' && p[1] <= '3') hours[n++] = p + 2;
    for (int i = 0; i < n; i++) {
        const char *after = hours[i];
        const char *colon[2];
        int nc = 0;
        if (after < end && *after == ':') colon[nc++] = after + 1;
        colon[nc++] = after;
        for (int j = 0; j < nc; j++) {
            const char *q = colon[j];
            if (q + 1 < end && q[0] >= '0' && q[0] <= '5' && is_digit(q[1]) && right_ok(q + 2, end)) {
                m->g[0].b = p; m->g[0].e = after;
                m->g[1].b = q; m->g[1].e = q + 2;
                m->end = q + 2;
                return true;
            }
        }
    }
    return false;
}

/* @([A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*)
 * Backtracking cannot help: giving back a letter, an alnum or a whole subtag
 * leaves a character that is neither B nor [-_]. */
static bool pat_language(const char *text, const char *p, const char *end, match_t *m)
{
    const char *g, *q;
    (void)text;
    if (p >= end || *p != '@') return false;
    g = ++p;
    while (p < end && is_alpha(*p)) p++;
    if (p - g < 2 || p - g > 3) return false;
    while (p < end && (*p == '-' || *p == '_')) {
        q = p + 1;
        while (q < end && is_alnum(*q)) q++;
        if (q - (p + 1) < 2 || q - (p + 1) > 8) break;
        p = q;
    }
    return set1(m, g, p, p, end);
}

/* ~([A-Za-z0-9/]+) */
static bool pat_callsign(const char *text, const char *p, const char *end, match_t *m)
{
    const char *g;
    (void)text;
    if (p >= end || *p != '~') return false;
    g = ++p;
    while (p < end && (is_alnum(*p) || *p == '/')) p++;
    return p > g && set1(m, g, p, p, end);
}

/* #([A-Za-z0-9_-]+) */
static bool pat_reference(const char *text, const char *p, const char *end, match_t *m)
{
    const char *g;
    (void)text;
    if (p >= end || *p != '#') return false;
    g = ++p;
    while (p < end && (is_alnum(*p) || *p == '_' || *p == '-')) p++;
    return p > g && set1(m, g, p, p, end);
}

/* (?:[Ee][Tt][Aa] ?)? ; skipping ETA cannot help, a digit must follow. */
static const char *opt_eta(const char *p, const char *end)
{
    const char *q = word_ci(p, end, "eta");
    return q ? opt_space(q, end) : p;
}

/* (?:[Ee][Tt][Aa] ?)?([0-9]+) ?<unit> where unit is "h", "min" or "d". */
static bool unit_value(const char *p, const char *end, const char *unit, span_t *g, const char **after)
{
    const char *d = opt_eta(p, end), *de = digits(d, end), *q;
    if (de == d) return false;
    q = word_ci(opt_space(de, end), end, unit);
    if (!q) return false;
    g->b = d; g->e = de;
    *after = q;
    return true;
}

/* (?:[Ee][Tt][Aa] ?)?([0-9]+) ?[Hh] ?([0-9]+) ?[Mm][Ii][Nn] */
static bool pat_dur_hm(const char *text, const char *p, const char *end, match_t *m)
{
    const char *q;
    (void)text;
    if (!unit_value(p, end, "h", &m->g[0], &q)) return false;
    q = opt_space(q, end);
    {
        const char *de = digits(q, end), *r;
        if (de == q) return false;
        r = word_ci(opt_space(de, end), end, "min");
        if (!r || !right_ok(r, end)) return false;
        m->g[1].b = q; m->g[1].e = de;
        m->end = r;
        return true;
    }
}

static bool pat_dur_unit(const char *p, const char *end, const char *unit, match_t *m)
{
    const char *q;
    if (!unit_value(p, end, unit, &m->g[0], &q) || !right_ok(q, end)) return false;
    m->g[1].b = NULL; m->g[1].e = NULL;
    m->end = q;
    return true;
}

static bool pat_dur_h(const char *text, const char *p, const char *end, match_t *m)
{
    (void)text;
    return pat_dur_unit(p, end, "h", m);
}

static bool pat_dur_min(const char *text, const char *p, const char *end, match_t *m)
{
    (void)text;
    return pat_dur_unit(p, end, "min", m);
}

static bool pat_dur_d(const char *text, const char *p, const char *end, match_t *m)
{
    (void)text;
    return pat_dur_unit(p, end, "d", m);
}

/* ^(?:[Ee][Tt][Aa] ?)?([0-9]+)([.,][0-9]+)?
 * Backtracking matters: if B does not follow the decimal part, the regex
 * drops group 2, and the `.` or `,` (both in B) becomes the right boundary. */
static bool pat_dur_bare(const char *text, const char *p, const char *end, match_t *m)
{
    const char *d, *de;
    if (p != text) return false;
    d = opt_eta(p, end);
    de = digits(d, end);
    if (de == d) return false;
    m->g[0].b = d; m->g[0].e = de;
    if (de < end && (*de == '.' || *de == ',')) {
        const char *fe = digits(de + 1, end);
        if (fe > de + 1 && right_ok(fe, end)) {
            m->g[1].b = de; m->g[1].e = fe;
            m->end = fe;
            return true;
        }
    }
    if (!right_ok(de, end)) return false;
    m->g[1].b = NULL; m->g[1].e = NULL;
    m->end = de;
    return true;
}

/* ---------- Search (rules 4-6) ---------- */

typedef bool (*valid_fn)(const match_t *m, int kind);

/* Leftmost match of (?:^|B)(?:pattern)(?:B|$) starting at or after pos. */
static bool search(pattern_fn f, const char *text, const char *end, const char *pos, match_t *m)
{
    for (const char *s = pos;;) {
        size_t n;
        if (s == text && f(text, s, end, m)) { m->start = s; return true; }
        n = b_len(s, end);
        if (n && f(text, s + n, end, m)) { m->start = s; return true; }
        if (s >= end) return false;
        {
            uint32_t c;
            s += utf8_next(s, end, &c);
        }
    }
}

/* Rules 5 and 6: the first match that passes validation. On failure the
 * search resumes where the failed token ends. */
static bool first_valid(pattern_fn f, const char *text, const char *end,
                        valid_fn ok, int kind, match_t *m)
{
    const char *pos = text;
    while (search(f, text, end, pos, m)) {
        if (!ok || ok(m, kind)) return true;
        pos = m->end;
    }
    return false;
}

/* strtod() on a copy: the span is not NUL-terminated. A group is never
 * longer than the input, so the copy is exact. */
static double parse_decimal(span_t s)
{
    char buf[MECP_MAX_INPUT_BYTES + 1];
    size_t n = (size_t)(s.e - s.b);
    memcpy(buf, s.b, n);
    buf[n] = '\0';
    return strtod(buf, NULL);
}

static bool gps_ok(const match_t *m, int kind)
{
    double lat = parse_decimal(m->g[0]), lon = parse_decimal(m->g[1]);
    (void)kind;
    return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}

static bool callsign_ok(const match_t *m, int kind)
{
    (void)kind;
    return m->g[0].e - m->g[0].b <= 12;
}

enum { DUR_HM, DUR_H, DUR_MIN, DUR_D, DUR_BARE, DUR_KINDS };

static const pattern_fn duration_patterns[DUR_KINDS] = {
    pat_dur_hm, pat_dur_h, pat_dur_min, pat_dur_d, pat_dur_bare,
};

static int32_t minutes(const match_t *m, int kind)
{
    long long a = clamp_int(m->g[0].b, m->g[0].e);
    switch (kind) {
    case DUR_HM: return clamp_ll(a * 60 + clamp_int(m->g[1].b, m->g[1].e));
    case DUR_H: return clamp_ll(a * 60);
    case DUR_D: return clamp_ll(a * 1440);
    default: return (int32_t)a; /* min, bare */
    }
}

static bool duration_ok(const match_t *m, int kind)
{
    return minutes(m, kind) > 0 && (kind != DUR_BARE || m->g[1].b == NULL);
}

/* Patterns 1-4: first by position, ties to list order. Pattern 5 (bare
 * number) only when none of them matches. */
static bool duration(const char *text, const char *end, int32_t *out)
{
    bool found = false;
    const char *best_start = NULL;
    for (int kind = 0; kind < DUR_KINDS; kind++) {
        match_t m;
        if (kind == DUR_BARE && found) break;
        if (first_valid(duration_patterns[kind], text, end, duration_ok, kind, &m) &&
            (!found || m.start < best_start)) {
            found = true;
            best_start = m.start;
            *out = minutes(&m, kind);
        }
    }
    return found;
}

static void copy_span(char *dst, span_t s, char (*fold)(char))
{
    size_t n = (size_t)(s.e - s.b);
    for (size_t i = 0; i < n; i++) dst[i] = fold ? fold(s.b[i]) : s.b[i];
    dst[n] = '\0';
}

static char lang_fold(char c) { return c == '_' ? '-' : to_lower(c); }

static void extract(const char *text, const char *end, mecp_decoded_t *d)
{
    match_t m;
    if (first_valid(pat_pax, text, end, NULL, 0, &m)) {
        d->has_pax = true;
        d->pax = clamp_int(m.g[0].b, m.g[0].e);
    }
    if (first_valid(pat_gps, text, end, gps_ok, 0, &m)) {
        d->has_gps = true;
        d->gps.lat = parse_decimal(m.g[0]);
        d->gps.lon = parse_decimal(m.g[1]);
    }
    if (first_valid(pat_timestamp, text, end, NULL, 0, &m)) {
        int h = (int)clamp_int(m.g[0].b, m.g[0].e);
        d->timestamp[0] = (char)('0' + h / 10);
        d->timestamp[1] = (char)('0' + h % 10);
        d->timestamp[2] = ':';
        d->timestamp[3] = m.g[1].b[0];
        d->timestamp[4] = m.g[1].b[1];
        d->timestamp[5] = '\0';
    }
    if (first_valid(pat_language, text, end, NULL, 0, &m)) copy_span(d->language, m.g[0], lang_fold);
    if (first_valid(pat_callsign, text, end, callsign_ok, 0, &m)) copy_span(d->callsign, m.g[0], to_upper);
    if (first_valid(pat_reference, text, end, NULL, 0, &m)) copy_span(d->reference, m.g[0], NULL);
    if (mecp_has_code(d, "R03")) d->has_duration = duration(text, end, &d->duration);
}

/* ---------- Envelope ---------- */

/* Freetext group of the message pattern:
 * [^ \t LB](?:[^LB]*[^ \t LB])? where LB is the line breaks. */
static bool freetext_ok(const char *p, const char *end)
{
    uint32_t c = 0;
    if (p >= end || *p == ' ' || *p == '\t') return false;
    if (end[-1] == ' ' || end[-1] == '\t') return false;
    while (p < end) {
        p += utf8_next(p, end, &c);
        if (is_line_break(c)) return false;
    }
    return true;
}

/* Match the message pattern against [s, end). On success *codes_end is the
 * end of the code section and *ft is the freetext start (NULL if none).
 * The code group is greedy, so on failure the regex retries with one code
 * fewer; that can turn "T05 T05  x" into codes [T05], freetext "T05  x". */
static bool envelope(const char *s, const char *end, const char **codes_end, const char **ft)
{
    const char *ends[MECP_MAX_CODES + 1];
    size_t k = 0;
    const char *p = s + 7;

    if (end - s < 10 || memcmp(s, "MECP/", 5) != 0 || s[5] < '0' || s[5] > '3' || s[6] != '/')
        return false;
    for (;;) {
        if (end - p < 3 || !mecp_is_code(p, 3) || k == MECP_MAX_CODES) break;
        ends[k++] = p + 3;
        if (p + 3 < end && p[3] == ' ') p += 4;
        else break;
    }
    while (k > 0) {
        const char *ce = ends[--k];
        if (ce == end) { *codes_end = ce; *ft = NULL; return true; }
        if (*ce == ' ' && freetext_ok(ce + 1, end)) { *codes_end = ce; *ft = ce + 1; return true; }
    }
    return false;
}

/* ---------- Public API ---------- */

bool mecp_is_mecp(const char *s, size_t len)
{
    return len >= 5 && memcmp(s, "MECP/", 5) == 0;
}

bool mecp_is_code(const char *t, size_t len)
{
    return len == 3 && t[0] >= 'A' && t[0] <= 'Z' && is_digit(t[1]) && is_digit(t[2]);
}

bool mecp_has_code(const mecp_decoded_t *d, const char *code)
{
    for (size_t i = 0; i < d->code_count; i++)
        if (strcmp(d->codes[i], code) == 0) return true;
    return false;
}

bool mecp_decode(const char *s, size_t len, mecp_decoded_t *out)
{
    const char *end = s + len, *codes_end, *ft;

    memset(out, 0, sizeof *out);
    out->severity = -1;
    if (len > MECP_MAX_INPUT_BYTES) {
        out->errors = MECP_INPUT_TOO_LONG;
        return false;
    }
    /* Remove at most one trailing \n, \r or \r\n. */
    if (end - s >= 2 && end[-2] == '\r' && end[-1] == '\n') end -= 2;
    else if (end > s && (end[-1] == '\n' || end[-1] == '\r')) end -= 1;

    if (!envelope(s, end, &codes_end, &ft)) return true;
    out->valid = true;
    out->severity = s[5] - '0';
    for (const char *p = s + 7; p < codes_end; p += 4) {
        memcpy(out->codes[out->code_count], p, 3);
        out->codes[out->code_count++][3] = '\0';
    }
    out->is_drill = mecp_has_code(out, "D01") || mecp_has_code(out, "D02");
    if (ft) {
        out->has_freetext = true;
        memcpy(out->freetext, ft, (size_t)(end - ft));
        out->freetext[end - ft] = '\0';
        extract(ft, end, out);
    }
    return true;
}

void mecp_validate(const char *s, size_t len, mecp_validation_t *out)
{
    const char *end = s + len, *codes_end, *ft;
    bool severity_ok, delim_ok, forbidden = false;

    memset(out, 0, sizeof *out);
    if (!mecp_is_mecp(s, len)) {
        out->errors = MECP_MISSING_PREFIX;
        return;
    }
    severity_ok = len > 5 && s[5] >= '0' && s[5] <= '3';
    delim_ok = len > 6 && s[6] == '/';
    if (!severity_ok) out->errors |= MECP_INVALID_SEVERITY;
    if (!delim_ok) out->errors |= MECP_MISSING_DELIMITER;
    for (const char *p = s; p < end;) {
        uint32_t c;
        p += utf8_next(p, end, &c);
        if (is_forbidden(c)) forbidden = true;
    }
    if (severity_ok && delim_ok && !forbidden) {
        if (len < 10 || !mecp_is_code(s + 7, 3) || (len > 10 && s[10] != ' '))
            out->errors |= MECP_NO_CODES;
        else if (!envelope(s, end, &codes_end, &ft))
            out->errors |= MECP_INVALID_FREETEXT;
    }
    if (forbidden) out->errors |= MECP_FORBIDDEN_CHARACTER;
    if (len > MECP_MAX_MESSAGE_BYTES) out->errors |= MECP_OVER_LIMIT;
    out->valid = out->errors == 0;
}

typedef struct {
    char *buf;
    size_t cap;
    size_t len;
} writer_t;

static void put(writer_t *w, const char *s, size_t n)
{
    if (w->len + n < w->cap) memcpy(w->buf + w->len, s, n);
    w->len += n;
}

bool mecp_encode(int severity, const char *const *codes, size_t code_count,
                 const char *freetext, char *buf, size_t buf_size,
                 mecp_encoded_t *out)
{
    writer_t w = {buf, buf_size, 0};
    char num[16];
    mecp_validation_t v;

    memset(out, 0, sizeof *out);
    if (severity < 0 || severity > 3) out->errors |= MECP_INVALID_SEVERITY;
    if (code_count == 0) out->errors |= MECP_NO_CODES;

    snprintf(num, sizeof num, "%d", severity);
    put(&w, "MECP/", 5);
    put(&w, num, strlen(num));
    put(&w, "/", 1);
    for (size_t i = 0; i < code_count; i++) {
        size_t n = strlen(codes[i]);
        if (!mecp_is_code(codes[i], n)) {
            out->errors |= MECP_INVALID_CODE;
            out->invalid_code_count++;
        }
        if (i > 0) put(&w, " ", 1);
        put(&w, codes[i], n);
    }
    if (freetext) {
        /* Trim ECMAScript whitespace from both ends. */
        const char *b = freetext, *e = freetext + strlen(freetext), *p, *last;
        uint32_t c;
        size_t n;
        while (b < e && (n = utf8_next(b, e, &c), is_ws(c))) b += n;
        for (p = last = b; p < e;) {
            p += utf8_next(p, e, &c);
            if (!is_ws(c)) last = p;
        }
        if (b < last) {
            put(&w, " ", 1);
            put(&w, b, (size_t)(last - b));
        }
    }
    out->byte_length = w.len;
    if (w.len >= buf_size) {
        if (buf_size) buf[0] = '\0';
        return false;
    }
    buf[w.len] = '\0';

    /* Wire errors; the other validate errors only repeat an input error. */
    mecp_validate(buf, w.len, &v);
    out->errors |= v.errors & (MECP_FORBIDDEN_CHARACTER | MECP_OVER_LIMIT);
    out->ok = out->errors == 0;
    if (!out->ok) buf[0] = '\0';
    return true;
}
