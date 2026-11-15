/* MECP encoder/decoder. See include/mecp.h and spec/conformance.md. */
#include "mecp.h"

#include <stdlib.h>
#include <string.h>

#define INT_FIELD_MAX 2147483647L

/* ---------- UTF-8 / whitespace helpers ---------- */

/* Decode one code point at p (p < end). Returns its byte length (>= 1).
 * Malformed bytes decode as a single code point 0xFFFD of length 1. */
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

/* ECMAScript whitespace. */
static bool is_ws_cp(uint32_t c)
{
    return (c >= 0x09 && c <= 0x0D) || c == 0x20 || c == 0xA0 || c == 0x1680 ||
           (c >= 0x2000 && c <= 0x200A) || c == 0x2028 || c == 0x2029 ||
           c == 0x202F || c == 0x205F || c == 0x3000 || c == 0xFEFF;
}

/* Byte length of the whitespace code point at p, or 0 if none. */
static size_t ws_len(const char *p, const char *end)
{
    uint32_t c;
    size_t n;
    if (p >= end) return 0;
    n = utf8_next(p, end, &c);
    return is_ws_cp(c) ? n : 0;
}

/* Position is at end of text or followed by whitespace. */
static bool at_boundary(const char *p, const char *end)
{
    return p == end || ws_len(p, end) > 0;
}

/* Trim whitespace from both ends of [*b, *e). */
static void trim(const char **b, const char **e)
{
    const char *p = *b, *last = *b;
    size_t n;
    while ((n = ws_len(p, *e)) > 0) p += n;
    *b = p;
    last = p;
    while (p < *e) {
        uint32_t c;
        n = utf8_next(p, *e, &c);
        p += n;
        if (!is_ws_cp(c)) last = p;
    }
    *e = last;
}

static bool is_digit(char c) { return c >= '0' && c <= '9'; }
static bool is_lower(char c) { return c >= 'a' && c <= 'z'; }
static bool is_alnum(char c)
{
    return is_digit(c) || (c >= 'A' && c <= 'Z') || is_lower(c);
}

/* Parse a run of ASCII digits [p, e) as an int; false if > INT_FIELD_MAX. */
static bool to_int(const char *p, const char *e, int32_t *out)
{
    long v = 0;
    for (; p < e; p++) {
        v = v * 10 + (*p - '0');
        if (v > INT_FIELD_MAX) return false;
    }
    *out = (int32_t)v;
    return true;
}

static void copy_str(char *dst, const char *src, size_t n)
{
    memcpy(dst, src, n);
    dst[n] = '\0';
}

/* ---------- Header parsing shared by decode and validate ---------- */

typedef struct {
    int severity;         /* -1 if invalid */
    bool has_delimiter;
    const char *body;     /* body start (may equal end) */
} header_t;

static void parse_header(const char *s, const char *end, header_t *h)
{
    const char *p = s + 5;
    uint32_t c5 = 0, c6 = 0;
    bool have5 = false, have6 = false;

    if (p < end) { p += utf8_next(p, end, &c5); have5 = true; }
    if (p < end) { p += utf8_next(p, end, &c6); have6 = true; }

    h->severity = (have5 && c5 >= '0' && c5 <= '3') ? (int)(c5 - '0') : -1;
    h->has_delimiter = have6 && c6 == '/';
    h->body = p;
}

/* ---------- Public helpers ---------- */

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

/* ---------- Freetext extraction ---------- */

/* `-?[0-9]+\.[0-9]+` at p; returns end or NULL. */
static const char *match_decimal(const char *p, const char *end)
{
    const char *q;
    if (p < end && *p == '-') p++;
    q = p;
    while (p < end && is_digit(*p)) p++;
    if (p == q || p >= end || *p != '.') return NULL;
    q = ++p;
    while (p < end && is_digit(*p)) p++;
    return p == q ? NULL : p;
}

/* strtod over [p, e) inside a mutable buffer, without reading past e. */
static double parse_double(char *p, char *e)
{
    char saved = *e;
    double v;
    *e = '\0';
    v = strtod(p, NULL);
    *e = saved;
    return v;
}

static void extract(mecp_decoded_t *d)
{
    char *t = d->freetext;
    char *end = t + (d->has_freetext ? strlen(t) : 0);
    char *p;

    /* count: ([0-9]+)pax */
    for (p = t; p < end; p++) {
        char *q = p;
        while (q < end && is_digit(*q)) q++;
        if (q > p && end - q >= 3 && memcmp(q, "pax", 3) == 0) {
            d->has_count = to_int(p, q, &d->count);
            break;
        }
    }

    /* gps: first match only, then range check */
    for (p = t; p < end; p++) {
        char *lat_end = (char *)match_decimal(p, end);
        char *lon_end;
        if (!lat_end || lat_end >= end || *lat_end != ',') continue;
        lon_end = (char *)match_decimal(lat_end + 1, end);
        if (!lon_end) continue;
        {
            double lat = parse_double(p, lat_end);
            double lon = parse_double(lat_end + 1, lon_end);
            if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
                d->has_gps = true;
                d->gps.lat = lat;
                d->gps.lon = lon;
            }
        }
        break;
    }

    /* eta: ^([0-9]+)Boundary, only after R03 */
    if (d->has_freetext && mecp_has_code(d, "R03")) {
        p = t;
        while (p < end && is_digit(*p)) p++;
        if (p > t && at_boundary(p, end))
            d->has_eta = to_int(t, p, &d->eta);
    }

    /* reference: #([A-Za-z0-9]{1,4}) */
    for (p = t; p < end; p++) {
        size_t n = 0;
        if (*p != '#') continue;
        while (n < 4 && p + 1 + n < end && is_alnum(p[1 + n])) n++;
        if (n > 0) { copy_str(d->reference, p + 1, n); break; }
    }

    /* language: @([a-z]{2})Boundary */
    for (p = t; p + 3 <= end; p++) {
        if (p[0] == '@' && is_lower(p[1]) && is_lower(p[2]) && at_boundary(p + 3, end)) {
            copy_str(d->language, p + 1, 2);
            break;
        }
    }

    /* timestamp: @([0-9]{4})Boundary, first match only, then range check */
    for (p = t; p + 5 <= end; p++) {
        if (p[0] == '@' && is_digit(p[1]) && is_digit(p[2]) && is_digit(p[3]) &&
            is_digit(p[4]) && at_boundary(p + 5, end)) {
            int hh = (p[1] - '0') * 10 + (p[2] - '0');
            int mm = (p[3] - '0') * 10 + (p[4] - '0');
            if (hh <= 23 && mm <= 59) copy_str(d->timestamp, p + 1, 4);
            break;
        }
    }

    /* callsign: ~([A-Za-z0-9]{1,9})Boundary */
    for (p = t; p < end; p++) {
        char *q;
        if (*p != '~') continue;
        q = p + 1;
        while (q < end && is_alnum(*q)) q++;
        if (q - p - 1 >= 1 && q - p - 1 <= 9 && at_boundary(q, end)) {
            copy_str(d->callsign, p + 1, (size_t)(q - p - 1));
            break;
        }
    }
}

/* ---------- Decode ---------- */

bool mecp_decode(const char *s, size_t len, mecp_decoded_t *d)
{
    const char *end = s + len;
    const char *p, *b, *e;
    header_t h;
    size_t ft_len = 0;
    bool in_freetext = false;

    memset(d, 0, sizeof *d);
    d->severity = -1;

    if (len > MECP_MAX_INPUT_BYTES) {
        d->warnings = MECP_INPUT_TOO_LONG;
        return false;
    }
    if (!mecp_is_mecp(s, len)) return true;

    parse_header(s, end, &h);
    d->severity = h.severity;
    if (h.severity < 0) d->warnings |= MECP_INVALID_SEVERITY;
    if (!h.has_delimiter) d->warnings |= MECP_MISSING_DELIMITER;

    b = h.body;
    e = end;
    trim(&b, &e);
    if (b == e) {
        d->valid = h.severity >= 0;
        if (d->valid) d->warnings |= MECP_NO_CODES;
        return true;
    }

    /* Tokenise on U+0020 only. 0x20 never occurs inside a UTF-8 sequence. */
    for (p = h.body; p < end;) {
        const char *tok, *tok_end;
        while (p < end && *p == ' ') p++;
        if (p == end) break;
        tok = p;
        while (p < end && *p != ' ') p++;
        tok_end = p;

        if (!in_freetext && mecp_is_code(tok, (size_t)(tok_end - tok)) &&
            d->code_count < MECP_MAX_CODES) {
            copy_str(d->codes[d->code_count++], tok, 3);
            continue;
        }
        in_freetext = true;
        if (ft_len > 0) d->freetext[ft_len++] = ' ';
        memcpy(d->freetext + ft_len, tok, (size_t)(tok_end - tok));
        ft_len += (size_t)(tok_end - tok);
    }
    d->freetext[ft_len] = '\0';
    d->has_freetext = in_freetext;

    extract(d);
    d->is_drill = mecp_has_code(d, "D01") || mecp_has_code(d, "D02");
    d->valid = h.severity >= 0;
    return true;
}

/* ---------- Encode ---------- */

typedef struct {
    char *buf;
    size_t size;
    size_t len;
    bool overflow;
} writer_t;

static void put(writer_t *w, const char *s, size_t n)
{
    if (w->len + n + 1 > w->size) { w->overflow = true; return; }
    memcpy(w->buf + w->len, s, n);
    w->len += n;
    w->buf[w->len] = '\0';
}

bool mecp_encode(int severity, const char *const *codes, size_t code_count,
                 const char *freetext, char *buf, size_t buf_size,
                 mecp_encoded_t *out)
{
    writer_t w = {buf, buf_size, 0, false};
    char num[16];
    size_t num_len = 0;
    unsigned long mag;
    const char *b, *e;

    memset(out, 0, sizeof *out);
    if (buf_size == 0) return false;
    buf[0] = '\0';

    if (severity < 0 || severity > 3) out->warnings |= MECP_INVALID_SEVERITY;

    /* decimal(severity), most significant digit first */
    mag = severity < 0 ? 0UL - (unsigned long)severity : (unsigned long)severity;
    do { num[sizeof num - 1 - num_len++] = (char)('0' + mag % 10); mag /= 10; } while (mag);
    if (severity < 0) num[sizeof num - 1 - num_len++] = '-';

    put(&w, "MECP/", 5);
    put(&w, num + sizeof num - num_len, num_len);
    put(&w, "/", 1);
    for (size_t i = 0; i < code_count; i++) {
        size_t n = strlen(codes[i]);
        if (!mecp_is_code(codes[i], n)) {
            out->warnings |= MECP_INVALID_CODE;
            out->invalid_code_count++;
        }
        if (i > 0) put(&w, " ", 1);
        put(&w, codes[i], n);
    }

    if (freetext) {
        b = freetext;
        e = freetext + strlen(freetext);
        trim(&b, &e);
        if (b < e) {
            put(&w, " ", 1);
            put(&w, b, (size_t)(e - b));
        }
    }
    if (w.overflow) return false;

    /* Strip trailing whitespace from the whole message. */
    b = buf;
    e = buf + w.len;
    {
        const char *p = b, *last = b;
        while (p < e) {
            uint32_t c;
            p += utf8_next(p, e, &c);
            if (!is_ws_cp(c)) last = p;
        }
        w.len = (size_t)(last - b);
        buf[w.len] = '\0';
    }

    out->byte_length = w.len;
    out->over_limit = w.len > MECP_MAX_MESSAGE_BYTES;
    if (out->over_limit) out->warnings |= MECP_OVER_LIMIT;
    return true;
}

/* ---------- Validate ---------- */

void mecp_validate(const char *s, size_t len, mecp_validation_t *out)
{
    const char *end = s + len;
    const char *b, *e;
    header_t h;

    memset(out, 0, sizeof *out);
    if (!mecp_is_mecp(s, len)) {
        out->errors = MECP_MISSING_PREFIX;
        return;
    }
    parse_header(s, end, &h);
    if (h.severity < 0) out->errors |= MECP_INVALID_SEVERITY;
    if (!h.has_delimiter) out->errors |= MECP_MISSING_DELIMITER;

    b = h.body;
    e = end;
    trim(&b, &e);
    if (b == e) out->warnings |= MECP_NO_CODES;
    if (len > MECP_MAX_MESSAGE_BYTES) out->warnings |= MECP_OVER_LIMIT;
    out->valid = out->errors == 0;
}
