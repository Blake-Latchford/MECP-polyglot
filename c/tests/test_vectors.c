/* Runs the shared conformance vectors, and the upstream mecp-org/MECP
 * freetext cases, against the C implementation.
 * Compiles as C99 and as C++ (to check header compatibility). */
#include "mecp.h"

#include <stdio.h>
#include <string.h>

typedef struct {
    const char *name;
    const char *input;
    size_t input_len;
    bool envelope; /* false: upstream case, compare valid and fields only */
    bool valid;
    int severity;
    const char *codes; /* space-joined */
    bool is_drill;
    const char *freetext; /* NULL when absent */
    bool has_pax;
    long pax;
    bool has_gps;
    double lat, lon;
    const char *timestamp, *language, *callsign, *reference;
    bool has_duration;
    long duration;
} decode_vec_t;

#define ENCODE_CODES_CAP 8

typedef struct {
    const char *name;
    int severity;
    const char *codes[ENCODE_CODES_CAP];
    size_t code_count;
    const char *freetext;
    const char *message; /* "" when refused */
    size_t byte_length;
    const char *errors; /* comma-joined ids */
} encode_vec_t;

typedef struct {
    const char *name;
    const char *input;
    size_t input_len;
    bool valid;
    const char *errors;
} validate_vec_t;

#include "vectors.h"

typedef char encode_codes_fit[ENCODE_MAX_CODES <= ENCODE_CODES_CAP ? 1 : -1];

static int failures = 0;

#define CHECK(cond, name, what)                                         \
    do {                                                                \
        if (!(cond)) {                                                  \
            printf("FAIL %s: %s\n", (name), (what));                    \
            failures++;                                                 \
        }                                                               \
    } while (0)

static void flags_to_ids(uint32_t flags, size_t invalid_codes, char *out, size_t size)
{
    static const struct { uint32_t flag; const char *id; } ORDER[] = {
        {MECP_MISSING_PREFIX, "missing_prefix"},
        {MECP_INVALID_SEVERITY, "invalid_severity"},
        {MECP_MISSING_DELIMITER, "missing_delimiter"},
        {MECP_NO_CODES, "no_codes"},
        {MECP_INVALID_CODE, "invalid_code"},
        {MECP_INVALID_FREETEXT, "invalid_freetext"},
        {MECP_FORBIDDEN_CHARACTER, "forbidden_character"},
        {MECP_OVER_LIMIT, "over_limit"},
        {MECP_INPUT_TOO_LONG, "input_too_long"},
    };
    out[0] = '\0';
    for (size_t i = 0; i < sizeof ORDER / sizeof ORDER[0]; i++) {
        size_t reps = ORDER[i].flag == MECP_INVALID_CODE ? invalid_codes : 1;
        if (!(flags & ORDER[i].flag)) continue;
        for (size_t r = 0; r < reps; r++) {
            if (out[0]) strncat(out, ",", size - strlen(out) - 1);
            strncat(out, ORDER[i].id, size - strlen(out) - 1);
        }
    }
}

static void run_decode(const decode_vec_t *v)
{
    static mecp_decoded_t d;
    static char buf[MECP_MAX_INPUT_BYTES + 1];

    mecp_decode(v->input, v->input_len, &d);
    CHECK(d.valid == v->valid, v->name, "valid");
    if (v->envelope) {
        CHECK(d.severity == v->severity, v->name, "severity");
        buf[0] = '\0';
        for (size_t i = 0; i < d.code_count; i++) {
            if (i) strcat(buf, " ");
            strcat(buf, d.codes[i]);
        }
        CHECK(strcmp(buf, v->codes) == 0, v->name, "codes");
        CHECK(d.is_drill == v->is_drill, v->name, "is_drill");
        CHECK(d.has_freetext == (v->freetext != NULL), v->name, "has_freetext");
        if (v->freetext) CHECK(strcmp(d.freetext, v->freetext) == 0, v->name, "freetext");
    }
    if (!v->valid) return;
    CHECK(d.has_pax == v->has_pax, v->name, "has_pax");
    if (v->has_pax) CHECK(d.pax == v->pax, v->name, "pax");
    CHECK(d.has_gps == v->has_gps, v->name, "has_gps");
    if (v->has_gps) {
        CHECK(d.gps.lat == v->lat, v->name, "gps.lat");
        CHECK(d.gps.lon == v->lon, v->name, "gps.lon");
    }
    CHECK(strcmp(d.timestamp, v->timestamp) == 0, v->name, "timestamp");
    CHECK(strcmp(d.language, v->language) == 0, v->name, "language");
    CHECK(strcmp(d.callsign, v->callsign) == 0, v->name, "callsign");
    CHECK(strcmp(d.reference, v->reference) == 0, v->name, "reference");
    CHECK(d.has_duration == v->has_duration, v->name, "has_duration");
    if (v->has_duration) CHECK(d.duration == v->duration, v->name, "duration");
}

static void run_encode(const encode_vec_t *v)
{
    char msg[512];
    char ids[256];
    mecp_encoded_t e;
    bool ok = mecp_encode(v->severity, v->codes, v->code_count, v->freetext,
                          msg, sizeof msg, &e);

    CHECK(ok, v->name, "encode returned false");
    CHECK(strcmp(msg, v->message) == 0, v->name, "message");
    CHECK(e.ok == (v->message[0] != '\0'), v->name, "ok");
    CHECK(e.byte_length == v->byte_length, v->name, "byte_length");
    flags_to_ids(e.errors, e.invalid_code_count, ids, sizeof ids);
    CHECK(strcmp(ids, v->errors) == 0, v->name, "errors");
}

static void run_validate(const validate_vec_t *v)
{
    char ids[256];
    mecp_validation_t r;

    mecp_validate(v->input, v->input_len, &r);
    CHECK(r.valid == v->valid, v->name, "valid");
    flags_to_ids(r.errors, 0, ids, sizeof ids);
    CHECK(strcmp(ids, v->errors) == 0, v->name, "errors");
}

static void run_c_specific(void)
{
    static mecp_decoded_t d;
    static char big[MECP_MAX_INPUT_BYTES + 2];
    char small[8];
    mecp_encoded_t e;
    const char *codes[] = {"M01", "M07"};
    const char bad_utf8[] = "MECP/3/L01 \xff #tag";

    memcpy(big, "MECP/0/M01 ", 11);
    memset(big + 11, 'A', sizeof big - 12);
    CHECK(!mecp_decode(big, sizeof big - 1, &d), "input too long", "returned true");
    CHECK(d.errors == MECP_INPUT_TOO_LONG && !d.valid, "input too long", "flags");

    CHECK(!mecp_encode(0, codes, 2, NULL, small, sizeof small, &e), "small buffer",
          "returned true");
    CHECK(e.byte_length == 14, "small buffer", "byte_length");

    mecp_decode(bad_utf8, sizeof bad_utf8 - 1, &d);
    CHECK(d.valid && strcmp(d.reference, "tag") == 0, "invalid UTF-8", "not decoded");

    mecp_decode("MECP/0/B01 B02 B03", 18, &d);
    CHECK(mecp_is_beacon(&d) && mecp_is_beacon_ack(&d) && mecp_is_beacon_cancel(&d),
          "beacon helpers", "not detected");
}

int main(void)
{
    size_t nd = sizeof DECODE_VECTORS / sizeof DECODE_VECTORS[0];
    size_t ne = sizeof ENCODE_VECTORS / sizeof ENCODE_VECTORS[0];
    size_t nv = sizeof VALIDATE_VECTORS / sizeof VALIDATE_VECTORS[0];

    for (size_t i = 0; i < nd; i++) run_decode(&DECODE_VECTORS[i]);
    for (size_t i = 0; i < ne; i++) run_encode(&ENCODE_VECTORS[i]);
    for (size_t i = 0; i < nv; i++) run_validate(&VALIDATE_VECTORS[i]);
    run_c_specific();

    printf("%zu decode (incl. upstream), %zu encode, %zu validate vectors: %s (%d failures)\n",
           nd, ne, nv, failures ? "FAIL" : "ok", failures);
    return failures ? 1 : 0;
}
