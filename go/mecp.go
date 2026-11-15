// Package mecp encodes and decodes MECP (Mesh Emergency Communication
// Protocol) messages, as specified by MECP-polyglot spec/conformance.md.
package mecp

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"unicode/utf8"
)

const (
	MaxMessageBytes = 200
	Prefix          = "MECP/"
)

// Warning and error identifiers.
const (
	MissingPrefix    = "missing_prefix"
	InvalidSeverity  = "invalid_severity"
	MissingDelimiter = "missing_delimiter"
	NoCodes          = "no_codes"
	InvalidCode      = "invalid_code"
	OverLimit        = "over_limit"
)

type Gps struct {
	Lat float64 `json:"lat"`
	Lon float64 `json:"lon"`
}

type Extracted struct {
	Count     *int    `json:"count"`
	Gps       *Gps    `json:"gps"`
	Eta       *int    `json:"eta"`
	Reference *string `json:"reference"`
	Language  *string `json:"language"`
	Timestamp *string `json:"timestamp"`
	Callsign  *string `json:"callsign"`
}

type Decoded struct {
	Valid     bool      `json:"valid"`
	Severity  *int      `json:"severity"`
	Codes     []string  `json:"codes"`
	IsDrill   bool      `json:"is_drill"`
	Freetext  *string   `json:"freetext"`
	Extracted Extracted `json:"extracted"`
	Warnings  []string  `json:"warnings"`
}

type Encoded struct {
	Message    string   `json:"message"`
	ByteLength int      `json:"byte_length"`
	OverLimit  bool     `json:"over_limit"`
	Warnings   []string `json:"warnings"`
}

type Validation struct {
	Valid    bool     `json:"valid"`
	Errors   []string `json:"errors"`
	Warnings []string `json:"warnings"`
}

// isWS reports whether r is ECMAScript whitespace.
func isWS(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0D, r == ' ', r == 0xA0, r == 0x1680,
		r >= 0x2000 && r <= 0x200A, r == 0x2028, r == 0x2029, r == 0x202F,
		r == 0x205F, r == 0x3000, r == 0xFEFF:
		return true
	}
	return false
}

// Polyglot patterns: the same text in every implementation (spec "Patterns").
// ws holds literal characters, written with host-language string escapes.
const (
	ws  = "[\t-\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]"
	end = "(?:" + ws + "|$)"
)

var (
	countRe     = regexp.MustCompile(`([0-9]+)pax`)
	gpsRe       = regexp.MustCompile(`(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)`)
	etaRe       = regexp.MustCompile(`^([0-9]+)` + end)
	referenceRe = regexp.MustCompile(`#([A-Za-z0-9]{1,4})`)
	languageRe  = regexp.MustCompile(`@([a-z]{2})` + end)
	timestampRe = regexp.MustCompile(`@([0-9]{4})` + end)
	callsignRe  = regexp.MustCompile(`~([A-Za-z0-9]{1,9})` + end)
)

// find returns capture group 1 of the leftmost match of re in s, if any.
func find(re *regexp.Regexp, s string) (string, bool) {
	m := re.FindStringSubmatch(s)
	if m == nil {
		return "", false
	}
	return m[1], true
}

func trim(s string) string { return strings.TrimFunc(s, isWS) }

func isDigit(b byte) bool { return b >= '0' && b <= '9' }

// toInt parses a digit run; nil if it exceeds the int32 range.
func toInt(digits string) *int {
	v, err := strconv.ParseInt(digits, 10, 32)
	if err != nil {
		return nil
	}
	r := int(v)
	return &r
}

// IsMECP reports whether s starts with "MECP/".
func IsMECP(s string) bool { return strings.HasPrefix(s, Prefix) }

// IsCode reports whether token is a well-formed code such as "M01".
func IsCode(t string) bool {
	return len(t) == 3 && t[0] >= 'A' && t[0] <= 'Z' && isDigit(t[1]) && isDigit(t[2])
}

func contains(codes []string, code string) bool {
	for _, c := range codes {
		if c == code {
			return true
		}
	}
	return false
}

func IsBeacon(codes []string) bool       { return contains(codes, "B01") }
func IsBeaconAck(codes []string) bool    { return contains(codes, "B02") }
func IsBeaconCancel(codes []string) bool { return contains(codes, "B03") }

type header struct {
	severity     *int
	hasDelimiter bool
	body         string
}

// parseHeader requires s to start with Prefix. Indexing is by code point.
func parseHeader(s string) header {
	rest := s[len(Prefix):]
	var h header
	if rest != "" {
		r, n := utf8.DecodeRuneInString(rest)
		rest = rest[n:]
		if r >= '0' && r <= '3' {
			v := int(r - '0')
			h.severity = &v
		}
	}
	if rest != "" {
		r, n := utf8.DecodeRuneInString(rest)
		rest = rest[n:]
		h.hasDelimiter = r == '/'
	}
	h.body = rest
	return h
}

func extract(text string, codes []string) Extracted {
	var x Extracted
	if m, ok := find(countRe, text); ok {
		x.Count = toInt(m)
	}
	if m := gpsRe.FindStringSubmatch(text); m != nil {
		lat, err1 := strconv.ParseFloat(m[1], 64)
		lon, err2 := strconv.ParseFloat(m[2], 64)
		if err1 == nil && err2 == nil && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 {
			x.Gps = &Gps{Lat: lat, Lon: lon}
		}
	}
	if contains(codes, "R03") {
		if m, ok := find(etaRe, text); ok {
			x.Eta = toInt(m)
		}
	}
	if m, ok := find(referenceRe, text); ok {
		x.Reference = &m
	}
	if m, ok := find(languageRe, text); ok {
		x.Language = &m
	}
	if m, ok := find(timestampRe, text); ok {
		hh, _ := strconv.Atoi(m[:2])
		mm, _ := strconv.Atoi(m[2:])
		if hh <= 23 && mm <= 59 {
			x.Timestamp = &m
		}
	}
	if m, ok := find(callsignRe, text); ok {
		x.Callsign = &m
	}
	return x
}

// Decode parses s. It never fails; check Decoded.Valid and Decoded.Warnings.
func Decode(s string) Decoded {
	d := Decoded{Codes: []string{}, Warnings: []string{}}
	if !IsMECP(s) {
		return d
	}

	h := parseHeader(s)
	d.Severity = h.severity
	if h.severity == nil {
		d.Warnings = append(d.Warnings, InvalidSeverity)
	}
	if !h.hasDelimiter {
		d.Warnings = append(d.Warnings, MissingDelimiter)
	}

	if trim(h.body) == "" {
		d.Valid = h.severity != nil
		if d.Valid {
			d.Warnings = append(d.Warnings, NoCodes)
		}
		return d
	}

	var tokens []string
	for _, t := range strings.Split(h.body, " ") {
		if t != "" {
			tokens = append(tokens, t)
		}
	}
	i := 0
	for i < len(tokens) && IsCode(tokens[i]) {
		d.Codes = append(d.Codes, tokens[i])
		i++
	}
	if i < len(tokens) {
		text := strings.Join(tokens[i:], " ")
		d.Freetext = &text
		d.Extracted = extract(text, d.Codes)
	}

	d.IsDrill = contains(d.Codes, "D01") || contains(d.Codes, "D02")
	d.Valid = h.severity != nil
	return d
}

// Encode builds a message. freetext may be nil.
func Encode(severity int, codes []string, freetext *string) Encoded {
	warnings := []string{}
	if severity < 0 || severity > 3 {
		warnings = append(warnings, InvalidSeverity)
	}
	for _, c := range codes {
		if !IsCode(c) {
			warnings = append(warnings, InvalidCode)
		}
	}

	msg := fmt.Sprintf("%s%d/%s", Prefix, severity, strings.Join(codes, " "))
	if freetext != nil {
		if ft := trim(*freetext); ft != "" {
			msg += " " + ft
		}
	}
	msg = strings.TrimRightFunc(msg, isWS)

	over := len(msg) > MaxMessageBytes
	if over {
		warnings = append(warnings, OverLimit)
	}
	return Encoded{Message: msg, ByteLength: len(msg), OverLimit: over, Warnings: warnings}
}

// Validate checks s against the wire format.
func Validate(s string) Validation {
	if !IsMECP(s) {
		return Validation{Valid: false, Errors: []string{MissingPrefix}, Warnings: []string{}}
	}
	h := parseHeader(s)
	v := Validation{Errors: []string{}, Warnings: []string{}}
	if h.severity == nil {
		v.Errors = append(v.Errors, InvalidSeverity)
	}
	if !h.hasDelimiter {
		v.Errors = append(v.Errors, MissingDelimiter)
	}
	if trim(h.body) == "" {
		v.Warnings = append(v.Warnings, NoCodes)
	}
	if len(s) > MaxMessageBytes {
		v.Warnings = append(v.Warnings, OverLimit)
	}
	v.Valid = len(v.Errors) == 0
	return v
}
