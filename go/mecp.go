// Package mecp encodes and decodes MECP (Mesh Emergency Communication
// Protocol) 1.4.0 messages, as specified by MECP-polyglot spec/conformance.md.
// The regexes come from the upstream pack via the generated patterns.go.
package mecp

import (
	"fmt"
	"math"
	"regexp"
	"strconv"
	"strings"
)

const (
	MaxMessageBytes = 200
	Prefix          = "MECP/"
	intMax          = math.MaxInt32
)

// Error identifiers.
const (
	MissingPrefix      = "missing_prefix"
	InvalidSeverity    = "invalid_severity"
	MissingDelimiter   = "missing_delimiter"
	NoCodes            = "no_codes"
	InvalidCode        = "invalid_code"
	InvalidFreetext    = "invalid_freetext"
	ForbiddenCharacter = "forbidden_character"
	OverLimit          = "over_limit"
)

type Gps struct {
	Lat float64 `json:"lat"`
	Lon float64 `json:"lon"`
}

type Extracted struct {
	Pax       *int    `json:"pax"`
	Gps       *Gps    `json:"gps"`
	Timestamp *string `json:"timestamp"`
	Language  *string `json:"language"`
	Callsign  *string `json:"callsign"`
	Reference *string `json:"reference"`
	Duration  *int    `json:"duration"`
}

type Decoded struct {
	Valid     bool      `json:"valid"`
	Severity  *int      `json:"severity"`
	Codes     []string  `json:"codes"`
	IsDrill   bool      `json:"is_drill"`
	Freetext  *string   `json:"freetext"`
	Extracted Extracted `json:"extracted"`
}

// Encoded holds the built message, or a nil Message if the encoder refused.
type Encoded struct {
	Message    *string  `json:"message"`
	ByteLength int      `json:"byte_length"`
	Errors     []string `json:"errors"`
}

type Validation struct {
	Valid  bool     `json:"valid"`
	Errors []string `json:"errors"`
}

// isWS reports whether r is ECMAScript whitespace (what Encode trims).
func isWS(r rune) bool {
	switch {
	case r >= 0x09 && r <= 0x0D, r == ' ', r == 0xA0, r == 0x1680,
		r >= 0x2000 && r <= 0x200A, r == 0x2028, r == 0x2029, r == 0x202F,
		r == 0x205F, r == 0x3000, r == 0xFEFF:
		return true
	}
	return false
}

// isForbidden: never on the wire. Line breaks (§6.1 Wire), BOM and Unicode
// whitespace (rule 8).
func isForbidden(r rune) bool {
	switch {
	case r == '\n', r == '\f', r == '\r', r == 0x85, r == 0x2028, r == 0x2029,
		r == 0xFEFF, r == 0xA0, r == 0x1680, r >= 0x2000 && r <= 0x200A,
		r == 0x202F, r == 0x205F, r == 0x3000:
		return true
	}
	return false
}

// wrap applies rule 4: (?:^|B)(?:pattern)(B|$). The right boundary is the
// last group so a failed match can resume where its token ends (rule 6).
func wrap(p string) *regexp.Regexp {
	return regexp.MustCompile("(?:^|" + patBoundary + ")(?:" + p + ")(" + patBoundary + "|$)")
}

var (
	reMessage   = regexp.MustCompile(patMessage)
	rePax       = wrap(patPax)
	reGps       = wrap(patGps)
	reTimestamp = wrap(patTimestamp)
	reLanguage  = wrap(patLanguage)
	reCallsign  = wrap(patCallsign)
	reReference = wrap(patReference)
	reDuration  [len(patDuration)]*regexp.Regexp
)

func init() {
	for i, p := range patDuration {
		reDuration[i] = wrap(p)
	}
}

// match is a submatch found by firstValid, with indices into the freetext.
type match struct {
	start  int
	groups []string // groups[0] is the whole match; "" when a group did not take part
	has    []bool
}

// firstValid applies rules 5 and 6: the first match by position that passes ok.
func firstValid(re *regexp.Regexp, text string, ok func(match) bool) (match, bool) {
	pos := 0
	for pos <= len(text) {
		// Searching a suffix lets ^ match at pos, which is harmless: pos is
		// always at a boundary character, and no pattern starts with one.
		ix := re.FindStringSubmatchIndex(text[pos:])
		if ix == nil {
			break
		}
		n := len(ix) / 2
		m := match{start: pos + ix[0], groups: make([]string, n), has: make([]bool, n)}
		for g := 0; g < n; g++ {
			if ix[2*g] >= 0 {
				m.groups[g] = text[pos+ix[2*g] : pos+ix[2*g+1]]
				m.has[g] = true
			}
		}
		if ok == nil || ok(m) {
			return m, true
		}
		pos += ix[2*(n-1)] // start of the right boundary
	}
	return match{}, false
}

// clampInt parses an ASCII digit run, clamping huge values to the int32 maximum.
func clampInt(digits string) int {
	var v int64
	for i := 0; i < len(digits); i++ {
		v = v*10 + int64(digits[i]-'0')
		if v > intMax {
			return intMax
		}
	}
	return int(v)
}

func clampMul(a, b int) int {
	if a > intMax/b {
		return intMax
	}
	return a * b
}

// Duration kinds, in the order of patDuration.
const (
	kindHM = iota
	kindH
	kindMin
	kindD
	kindBare
)

func minutes(kind int, m match) int {
	a := clampInt(m.groups[1])
	switch kind {
	case kindHM:
		return int(min(int64(clampMul(a, 60))+int64(clampInt(m.groups[2])), intMax))
	case kindH:
		return clampMul(a, 60)
	case kindD:
		return clampMul(a, 1440)
	}
	return a // min, bare
}

func duration(text string) *int {
	found, bestStart, best := false, 0, 0
	for kind, re := range reDuration {
		if kind == kindBare && found {
			break // the bare number is only a fallback
		}
		m, ok := firstValid(re, text, func(m match) bool {
			return minutes(kind, m) > 0 && (kind != kindBare || !m.has[2])
		})
		// First by position; on a tie the earlier pattern (already found) wins.
		if ok && (!found || m.start < bestStart) {
			found, bestStart, best = true, m.start, minutes(kind, m)
		}
	}
	if !found {
		return nil
	}
	return &best
}

func ptr[T any](v T) *T { return &v }

func extract(text string, codes []string) Extracted {
	var x Extracted
	if m, ok := firstValid(rePax, text, nil); ok {
		x.Pax = ptr(clampInt(m.groups[1]))
	}
	gpsOK := func(m match) bool {
		lat, err1 := strconv.ParseFloat(m.groups[1], 64)
		lon, err2 := strconv.ParseFloat(m.groups[2], 64)
		return err1 == nil && err2 == nil && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180
	}
	if m, ok := firstValid(reGps, text, gpsOK); ok {
		lat, _ := strconv.ParseFloat(m.groups[1], 64)
		lon, _ := strconv.ParseFloat(m.groups[2], 64)
		x.Gps = &Gps{lat, lon}
	}
	if m, ok := firstValid(reTimestamp, text, nil); ok {
		x.Timestamp = ptr(fmt.Sprintf("%02d:%s", clampInt(m.groups[1]), m.groups[2]))
	}
	if m, ok := firstValid(reLanguage, text, nil); ok {
		x.Language = ptr(strings.ReplaceAll(asciiLower(m.groups[1]), "_", "-"))
	}
	if m, ok := firstValid(reCallsign, text, func(m match) bool { return len(m.groups[1]) <= 12 }); ok {
		x.Callsign = ptr(asciiUpper(m.groups[1]))
	}
	if m, ok := firstValid(reReference, text, nil); ok {
		x.Reference = ptr(m.groups[1])
	}
	if contains(codes, durationScope) {
		x.Duration = duration(text)
	}
	return x
}

// ASCII-only case folding (rule 5): never locale-sensitive.
func asciiLower(s string) string {
	b := []byte(s)
	for i, c := range b {
		if c >= 'A' && c <= 'Z' {
			b[i] = c + 32
		}
	}
	return string(b)
}

func asciiUpper(s string) string {
	b := []byte(s)
	for i, c := range b {
		if c >= 'a' && c <= 'z' {
			b[i] = c - 32
		}
	}
	return string(b)
}

func IsMECP(s string) bool { return strings.HasPrefix(s, Prefix) }

// IsCode reports whether t is exactly [A-Z][0-9][0-9].
func IsCode(t string) bool {
	return len(t) == 3 && t[0] >= 'A' && t[0] <= 'Z' &&
		t[1] >= '0' && t[1] <= '9' && t[2] >= '0' && t[2] <= '9'
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

func stripLineEnding(s string) string {
	switch {
	case strings.HasSuffix(s, "\r\n"):
		return s[:len(s)-2]
	case strings.HasSuffix(s, "\n"), strings.HasSuffix(s, "\r"):
		return s[:len(s)-1]
	}
	return s
}

// Decode decodes s. Invalid UTF-8 is read as U+FFFD.
func Decode(s string) Decoded {
	r := Decoded{Codes: []string{}}
	s = strings.ToValidUTF8(s, "�")
	env := reMessage.FindStringSubmatchIndex(stripLineEnding(s))
	if env == nil {
		return r
	}
	s = stripLineEnding(s)
	r.Valid = true
	r.Severity = ptr(int(s[env[2]] - '0'))
	r.Codes = strings.Split(s[env[4]:env[5]], " ")
	r.IsDrill = contains(r.Codes, "D01") || contains(r.Codes, "D02")
	if env[6] >= 0 {
		r.Freetext = ptr(s[env[6]:env[7]])
		r.Extracted = extract(*r.Freetext, r.Codes)
	}
	return r
}

// Validate reports whether s may be transmitted as an MECP 1.4.0 message.
func Validate(s string) Validation {
	if !IsMECP(s) {
		return Validation{false, []string{MissingPrefix}}
	}
	errs := []string{}
	severityOK := len(s) > 5 && s[5] >= '0' && s[5] <= '3'
	delimOK := len(s) > 6 && s[6] == '/'
	if !severityOK {
		errs = append(errs, InvalidSeverity)
	}
	if !delimOK {
		errs = append(errs, MissingDelimiter)
	}
	forbidden := strings.IndexFunc(s, isForbidden) >= 0
	if severityOK && delimOK && !forbidden {
		if len(s) < 10 || !IsCode(s[7:10]) || (len(s) > 10 && s[10] != ' ') {
			errs = append(errs, NoCodes)
		} else if !reMessage.MatchString(s) {
			errs = append(errs, InvalidFreetext)
		}
	}
	if forbidden {
		errs = append(errs, ForbiddenCharacter)
	}
	if len(s) > MaxMessageBytes {
		errs = append(errs, OverLimit)
	}
	return Validation{len(errs) == 0, errs}
}

// Encode builds a message. If there is any error, Message is nil: the
// encoder refuses to produce a transmittable string. Invalid UTF-8 in
// freetext is replaced with U+FFFD.
func Encode(severity int, codes []string, freetext *string) Encoded {
	errs := []string{}
	if severity < 0 || severity > 3 {
		errs = append(errs, InvalidSeverity)
	}
	if len(codes) == 0 {
		errs = append(errs, NoCodes)
	}
	for _, c := range codes {
		if !IsCode(c) {
			errs = append(errs, InvalidCode)
		}
	}
	msg := Prefix + strconv.Itoa(severity) + "/" + strings.Join(codes, " ")
	if freetext != nil {
		ft := strings.TrimFunc(strings.ToValidUTF8(*freetext, "\uFFFD"), isWS)
		if ft != "" {
			msg += " " + ft
		}
	}
	// Wire errors; the other validate errors only repeat an input error.
	for _, e := range Validate(msg).Errors {
		if e == ForbiddenCharacter || e == OverLimit {
			errs = append(errs, e)
		}
	}
	out := Encoded{ByteLength: len(msg), Errors: errs}
	if len(errs) == 0 {
		out.Message = &msg
	}
	return out
}
