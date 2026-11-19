//! MECP (Mesh Emergency Communication Protocol) 1.4.0 encoder/decoder.
//!
//! Implements MECP-polyglot `spec/conformance.md`. The regexes come from the
//! upstream pack via the generated `patterns` module.
//!
//! ```
//! let d = mecp::decode("MECP/0/M01 M07 2pax 48.6520,20.1305");
//! assert!(d.valid);
//! assert_eq!(d.codes, ["M01", "M07"]);
//! assert_eq!(d.extracted.pax, Some(2));
//! ```

#![forbid(unsafe_code)]

mod patterns;

pub use patterns::MECP_VERSION;
use regex_lite::{Captures, Regex};
use std::sync::OnceLock;

pub const MAX_MESSAGE_BYTES: usize = 200;
pub const PREFIX: &str = "MECP/";
const INT_MAX: u32 = i32::MAX as u32;

/// Error identifiers (spec: "Error ids").
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ErrorId {
    MissingPrefix,
    InvalidSeverity,
    MissingDelimiter,
    NoCodes,
    InvalidCode,
    InvalidFreetext,
    ForbiddenCharacter,
    OverLimit,
}

impl ErrorId {
    pub fn id(self) -> &'static str {
        match self {
            ErrorId::MissingPrefix => "missing_prefix",
            ErrorId::InvalidSeverity => "invalid_severity",
            ErrorId::MissingDelimiter => "missing_delimiter",
            ErrorId::NoCodes => "no_codes",
            ErrorId::InvalidCode => "invalid_code",
            ErrorId::InvalidFreetext => "invalid_freetext",
            ErrorId::ForbiddenCharacter => "forbidden_character",
            ErrorId::OverLimit => "over_limit",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Gps {
    pub lat: f64,
    pub lon: f64,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Extracted {
    pub pax: Option<u32>,
    pub gps: Option<Gps>,
    /// `HH:MM`.
    pub timestamp: Option<String>,
    pub language: Option<String>,
    pub callsign: Option<String>,
    pub reference: Option<String>,
    /// Minutes.
    pub duration: Option<u32>,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Decoded {
    pub valid: bool,
    pub severity: Option<u8>,
    pub codes: Vec<String>,
    pub is_drill: bool,
    pub freetext: Option<String>,
    pub extracted: Extracted,
}

/// `message` is `None` when the encoder refused (there are errors).
#[derive(Debug, Clone, PartialEq)]
pub struct Encoded {
    pub message: Option<String>,
    pub byte_length: usize,
    pub errors: Vec<ErrorId>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Validation {
    pub valid: bool,
    pub errors: Vec<ErrorId>,
}

/// ECMAScript whitespace: what `encode` trims from freetext.
fn is_ws(c: char) -> bool {
    matches!(c, '\u{9}'..='\u{d}' | ' ' | '\u{a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}'
        | '\u{2028}' | '\u{2029}' | '\u{202f}' | '\u{205f}' | '\u{3000}' | '\u{feff}')
}

/// Never on the wire: line breaks (§6.1 Wire), BOM and Unicode whitespace (rule 8).
fn is_forbidden(c: char) -> bool {
    matches!(c, '\n' | '\u{c}' | '\r' | '\u{85}' | '\u{2028}' | '\u{2029}' | '\u{feff}'
        | '\u{a0}' | '\u{1680}' | '\u{2000}'..='\u{200a}' | '\u{202f}' | '\u{205f}' | '\u{3000}')
}

/// Rule 4: `(?:^|B)(?:pattern)(B|$)`. The right boundary is the last group so
/// a failed match can resume where its token ends (rule 6).
fn wrap(p: &str) -> Regex {
    let b = patterns::BOUNDARY;
    Regex::new(&format!("(?:^|{b})(?:{p})({b}|$)")).unwrap()
}

struct Res {
    message: Regex,
    pax: Regex,
    gps: Regex,
    timestamp: Regex,
    language: Regex,
    callsign: Regex,
    reference: Regex,
    duration: Vec<Regex>,
}

fn res() -> &'static Res {
    static R: OnceLock<Res> = OnceLock::new();
    R.get_or_init(|| Res {
        message: Regex::new(patterns::MESSAGE).unwrap(),
        pax: wrap(patterns::PAX),
        gps: wrap(patterns::GPS),
        timestamp: wrap(patterns::TIMESTAMP),
        language: wrap(patterns::LANGUAGE),
        callsign: wrap(patterns::CALLSIGN),
        reference: wrap(patterns::REFERENCE),
        duration: patterns::DURATION.iter().map(|p| wrap(p)).collect(),
    })
}

/// Rules 5 and 6: the first match by position that passes `ok`.
fn first_valid<'h>(re: &Regex, text: &'h str, ok: impl Fn(&Captures) -> bool) -> Option<Captures<'h>> {
    let mut pos = 0;
    while pos <= text.len() {
        let c = re.captures_at(text, pos)?;
        if ok(&c) {
            return Some(c);
        }
        pos = c.get(c.len() - 1).unwrap().start(); // start of the right boundary
    }
    None
}

/// Parse an ASCII digit run, clamping huge values to the int32 maximum.
fn clamp_int(digits: &str) -> u32 {
    let mut v: u64 = 0;
    for b in digits.bytes() {
        v = v * 10 + u64::from(b - b'0');
        if v > u64::from(INT_MAX) {
            return INT_MAX;
        }
    }
    v as u32
}

fn clamp_mul(a: u32, b: u32) -> u32 {
    a.checked_mul(b).map_or(INT_MAX, |v| v.min(INT_MAX))
}

fn group<'h>(c: &Captures<'h>, i: usize) -> &'h str {
    c.get(i).map_or("", |m| m.as_str())
}

// Duration kinds, in the order of patterns::DURATION.
const HM: usize = 0;
const H: usize = 1;
const D: usize = 3;
const BARE: usize = 4;

fn minutes(kind: usize, c: &Captures) -> u32 {
    let a = clamp_int(group(c, 1));
    match kind {
        HM => clamp_mul(a, 60).saturating_add(clamp_int(group(c, 2))).min(INT_MAX),
        H => clamp_mul(a, 60),
        D => clamp_mul(a, 1440),
        _ => a, // min, bare
    }
}

fn duration(text: &str) -> Option<u32> {
    let mut best: Option<(usize, u32)> = None; // (match start, minutes)
    for (kind, re) in res().duration.iter().enumerate() {
        if kind == BARE && best.is_some() {
            break; // the bare number is only a fallback
        }
        let found = first_valid(re, text, |c| {
            minutes(kind, c) > 0 && (kind != BARE || c.get(2).is_none())
        });
        if let Some(c) = found {
            let start = c.get(0).unwrap().start();
            // First by position; on a tie the earlier pattern (already in best) wins.
            if best.map_or(true, |(s, _)| start < s) {
                best = Some((start, minutes(kind, &c)));
            }
        }
    }
    best.map(|(_, m)| m)
}

fn gps_ok(c: &Captures) -> bool {
    match (group(c, 1).parse::<f64>(), group(c, 2).parse::<f64>()) {
        (Ok(lat), Ok(lon)) => (-90.0..=90.0).contains(&lat) && (-180.0..=180.0).contains(&lon),
        _ => false,
    }
}

fn extract(text: &str, codes: &[String]) -> Extracted {
    let r = res();
    let mut x = Extracted::default();
    if let Some(c) = first_valid(&r.pax, text, |_| true) {
        x.pax = Some(clamp_int(group(&c, 1)));
    }
    if let Some(c) = first_valid(&r.gps, text, gps_ok) {
        x.gps = Some(Gps {
            lat: group(&c, 1).parse().unwrap(),
            lon: group(&c, 2).parse().unwrap(),
        });
    }
    if let Some(c) = first_valid(&r.timestamp, text, |_| true) {
        x.timestamp = Some(format!("{:02}:{}", clamp_int(group(&c, 1)), group(&c, 2)));
    }
    if let Some(c) = first_valid(&r.language, text, |_| true) {
        // ASCII-only case folding (rule 5).
        x.language = Some(group(&c, 1).to_ascii_lowercase().replace('_', "-"));
    }
    if let Some(c) = first_valid(&r.callsign, text, |c| group(c, 1).len() <= 12) {
        x.callsign = Some(group(&c, 1).to_ascii_uppercase());
    }
    if let Some(c) = first_valid(&r.reference, text, |_| true) {
        x.reference = Some(group(&c, 1).to_string());
    }
    if codes.iter().any(|c| c == patterns::DURATION_SCOPE) {
        x.duration = duration(text);
    }
    x
}

pub fn is_mecp(s: &str) -> bool {
    s.starts_with(PREFIX)
}

/// `token` is exactly `[A-Z][0-9][0-9]`.
pub fn is_code(token: &str) -> bool {
    let b = token.as_bytes();
    b.len() == 3 && b[0].is_ascii_uppercase() && b[1].is_ascii_digit() && b[2].is_ascii_digit()
}

fn has<S: AsRef<str>>(codes: &[S], code: &str) -> bool {
    codes.iter().any(|c| c.as_ref() == code)
}

pub fn is_beacon<S: AsRef<str>>(codes: &[S]) -> bool {
    has(codes, "B01")
}

pub fn is_beacon_ack<S: AsRef<str>>(codes: &[S]) -> bool {
    has(codes, "B02")
}

pub fn is_beacon_cancel<S: AsRef<str>>(codes: &[S]) -> bool {
    has(codes, "B03")
}

fn strip_line_ending(s: &str) -> &str {
    s.strip_suffix("\r\n")
        .or_else(|| s.strip_suffix('\n'))
        .or_else(|| s.strip_suffix('\r'))
        .unwrap_or(s)
}

pub fn decode(s: &str) -> Decoded {
    let s = strip_line_ending(s);
    let Some(env) = res().message.captures(s) else {
        return Decoded::default();
    };
    let codes: Vec<String> = group(&env, 2).split(' ').map(String::from).collect();
    let freetext = env.get(3).map(|m| m.as_str().to_string());
    Decoded {
        valid: true,
        severity: Some(group(&env, 1).as_bytes()[0] - b'0'),
        is_drill: has(&codes, "D01") || has(&codes, "D02"),
        extracted: freetext.as_deref().map(|t| extract(t, &codes)).unwrap_or_default(),
        codes,
        freetext,
    }
}

/// Whether `s` may be transmitted as an MECP 1.4.0 message.
pub fn validate(s: &str) -> Validation {
    if !is_mecp(s) {
        return Validation { valid: false, errors: vec![ErrorId::MissingPrefix] };
    }
    let b = s.as_bytes();
    let mut errors = Vec::new();
    let severity_ok = matches!(b.get(5), Some(b'0'..=b'3'));
    let delim_ok = b.get(6) == Some(&b'/');
    if !severity_ok {
        errors.push(ErrorId::InvalidSeverity);
    }
    if !delim_ok {
        errors.push(ErrorId::MissingDelimiter);
    }
    let forbidden = s.chars().any(is_forbidden);
    if severity_ok && delim_ok && !forbidden {
        let first = b.get(7..10).and_then(|t| std::str::from_utf8(t).ok());
        if !first.is_some_and(is_code) || b.get(10).is_some_and(|&c| c != b' ') {
            errors.push(ErrorId::NoCodes);
        } else if !res().message.is_match(s) {
            errors.push(ErrorId::InvalidFreetext);
        }
    }
    if forbidden {
        errors.push(ErrorId::ForbiddenCharacter);
    }
    if s.len() > MAX_MESSAGE_BYTES {
        errors.push(ErrorId::OverLimit);
    }
    Validation { valid: errors.is_empty(), errors }
}

/// Build a message. With any error, `message` is `None`: the encoder refuses.
pub fn encode<S: AsRef<str>>(severity: i32, codes: &[S], freetext: Option<&str>) -> Encoded {
    let mut errors = Vec::new();
    if !(0..=3).contains(&severity) {
        errors.push(ErrorId::InvalidSeverity);
    }
    if codes.is_empty() {
        errors.push(ErrorId::NoCodes);
    }
    errors.extend(codes.iter().filter(|c| !is_code(c.as_ref())).map(|_| ErrorId::InvalidCode));

    let joined: Vec<&str> = codes.iter().map(|c| c.as_ref()).collect();
    let mut message = format!("{PREFIX}{severity}/{}", joined.join(" "));
    if let Some(ft) = freetext.map(|f| f.trim_matches(is_ws)).filter(|f| !f.is_empty()) {
        message.push(' ');
        message.push_str(ft);
    }
    // Wire errors; the other validate errors only repeat an input error.
    errors.extend(
        validate(&message)
            .errors
            .into_iter()
            .filter(|e| matches!(e, ErrorId::ForbiddenCharacter | ErrorId::OverLimit)),
    );
    let byte_length = message.len();
    Encoded { message: errors.is_empty().then_some(message), byte_length, errors }
}
