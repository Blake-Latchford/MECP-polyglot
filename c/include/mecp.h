/*
 * MECP (Mesh Emergency Communication Protocol) 1.4.0 encoder/decoder.
 *
 * C99, no heap allocation, no global state, usable from C++.
 * Implements MECP-polyglot spec/conformance.md. The regexes there are matched
 * by hand; the boundary class B is generated from the upstream brief.
 *
 * Strings are UTF-8 and passed as (pointer, length); they need not be
 * NUL-terminated. Output strings are NUL-terminated. Invalid UTF-8 is read
 * as U+FFFD.
 *
 * GPS parsing uses strtod(); call it with LC_NUMERIC set to "C" (the default).
 */
#ifndef MECP_H
#define MECP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MECP_MAX_MESSAGE_BYTES 200

/* Longest input mecp_decode() accepts. Decoders must accept messages over
 * 200 bytes; override at compile time to trade RAM for headroom.
 * mecp_decoded_t is roughly 4 * MECP_MAX_INPUT_BYTES bytes. */
#ifndef MECP_MAX_INPUT_BYTES
#define MECP_MAX_INPUT_BYTES 256
#endif

/* Every code token takes at least 4 bytes ("M01 "). */
#define MECP_MAX_CODES ((MECP_MAX_INPUT_BYTES + 1) / 4)

/* Error flags. When listed, they appear in this bit order. */
#define MECP_MISSING_PREFIX       (1u << 0)
#define MECP_INVALID_SEVERITY     (1u << 1)
#define MECP_MISSING_DELIMITER    (1u << 2)
#define MECP_NO_CODES             (1u << 3)
#define MECP_INVALID_CODE         (1u << 4) /* see mecp_encoded_t.invalid_code_count */
#define MECP_INVALID_FREETEXT     (1u << 5)
#define MECP_FORBIDDEN_CHARACTER  (1u << 6)
#define MECP_OVER_LIMIT           (1u << 7)
#define MECP_INPUT_TOO_LONG       (1u << 8) /* C only: input > MECP_MAX_INPUT_BYTES */

typedef struct {
    double lat;
    double lon;
} mecp_gps_t;

typedef struct {
    bool valid;
    int severity; /* 0-3, or -1 if not valid */
    size_t code_count;
    char codes[MECP_MAX_CODES][4];
    bool is_drill;
    bool has_freetext;
    char freetext[MECP_MAX_INPUT_BYTES + 1];

    bool has_pax;
    int32_t pax;
    bool has_gps;
    mecp_gps_t gps;
    char timestamp[6];                           /* "HH:MM", "" when absent */
    char language[MECP_MAX_INPUT_BYTES + 1];     /* "" when absent */
    char callsign[13];                           /* "" when absent */
    char reference[MECP_MAX_INPUT_BYTES + 1];    /* "" when absent */
    bool has_duration;
    int32_t duration;                            /* minutes */

    uint32_t errors; /* only MECP_INPUT_TOO_LONG */
} mecp_decoded_t;

typedef struct {
    bool ok;            /* no errors; the message was written to buf */
    size_t byte_length; /* of the message as built, even when refused */
    uint32_t errors;    /* MECP_* flags */
    size_t invalid_code_count;
} mecp_encoded_t;

typedef struct {
    bool valid;
    uint32_t errors;
} mecp_validation_t;

/* Decode `s`. Always fills `out`. Returns false only if the input is longer
 * than MECP_MAX_INPUT_BYTES (then out->errors is MECP_INPUT_TOO_LONG and
 * nothing is decoded). */
bool mecp_decode(const char *s, size_t len, mecp_decoded_t *out);

/* Encode into `buf` (NUL-terminated). `codes` holds `code_count` NUL-terminated
 * strings; `freetext` may be NULL. With any error the encoder refuses: buf is
 * set to "" and out->ok is false. Returns false if `buf` is too small. */
bool mecp_encode(int severity, const char *const *codes, size_t code_count,
                 const char *freetext, char *buf, size_t buf_size,
                 mecp_encoded_t *out);

/* Whether `s` may be transmitted as an MECP message. */
void mecp_validate(const char *s, size_t len, mecp_validation_t *out);

bool mecp_is_mecp(const char *s, size_t len);
bool mecp_is_code(const char *token, size_t len);
bool mecp_has_code(const mecp_decoded_t *d, const char *code);

static inline bool mecp_is_beacon(const mecp_decoded_t *d) { return mecp_has_code(d, "B01"); }
static inline bool mecp_is_beacon_ack(const mecp_decoded_t *d) { return mecp_has_code(d, "B02"); }
static inline bool mecp_is_beacon_cancel(const mecp_decoded_t *d) { return mecp_has_code(d, "B03"); }

#ifdef __cplusplus
}
#endif

#endif /* MECP_H */
