/*
 * MECP (Mesh Emergency Communication Protocol) encoder/decoder.
 *
 * C99, no heap allocation, no global state, usable from C++.
 * Implements MECP-polyglot spec/conformance.md.
 *
 * Strings are UTF-8 and passed as (pointer, length); they need not be
 * NUL-terminated. Output strings are NUL-terminated.
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

/* Longest input mecp_decode() accepts. Override at compile time to trade RAM
 * for headroom; mecp_decoded_t is roughly 1.5 * MECP_MAX_INPUT_BYTES bytes. */
#ifndef MECP_MAX_INPUT_BYTES
#define MECP_MAX_INPUT_BYTES 256
#endif

/* Every code token takes at least 4 bytes ("M01 "). */
#define MECP_MAX_CODES ((MECP_MAX_INPUT_BYTES + 1) / 4)

/* Warning / error flags. When listed, they appear in this bit order. */
#define MECP_MISSING_PREFIX    (1u << 0)
#define MECP_INVALID_SEVERITY  (1u << 1)
#define MECP_MISSING_DELIMITER (1u << 2)
#define MECP_NO_CODES          (1u << 3)
#define MECP_INVALID_CODE      (1u << 4) /* see mecp_encoded_t.invalid_code_count */
#define MECP_OVER_LIMIT        (1u << 5)
#define MECP_INPUT_TOO_LONG    (1u << 6) /* C only: input > MECP_MAX_INPUT_BYTES */

typedef struct {
    double lat;
    double lon;
} mecp_gps_t;

typedef struct {
    bool valid;
    int severity; /* 0-3, or -1 if absent/invalid */
    size_t code_count;
    char codes[MECP_MAX_CODES][4];
    bool is_drill;
    bool has_freetext;
    char freetext[MECP_MAX_INPUT_BYTES + 1];

    bool has_count;
    int32_t count;
    bool has_gps;
    mecp_gps_t gps;
    bool has_eta;
    int32_t eta;
    char reference[5]; /* "" when absent */
    char language[3];  /* "" when absent */
    char timestamp[5]; /* "" when absent */
    char callsign[10]; /* "" when absent */

    uint32_t warnings; /* MECP_* flags */
} mecp_decoded_t;

typedef struct {
    size_t byte_length;
    bool over_limit;
    uint32_t warnings;
    size_t invalid_code_count;
} mecp_encoded_t;

typedef struct {
    bool valid;
    uint32_t errors;
    uint32_t warnings;
} mecp_validation_t;

/* Decode `s`. Always fills `out`. Returns false only if the input is longer
 * than MECP_MAX_INPUT_BYTES (then out->warnings has MECP_INPUT_TOO_LONG and
 * nothing else is decoded). */
bool mecp_decode(const char *s, size_t len, mecp_decoded_t *out);

/* Encode into `buf` (NUL-terminated). `codes` holds `code_count` NUL-terminated
 * strings; `freetext` may be NULL. Returns false if `buf` is too small. */
bool mecp_encode(int severity, const char *const *codes, size_t code_count,
                 const char *freetext, char *buf, size_t buf_size,
                 mecp_encoded_t *out);

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
