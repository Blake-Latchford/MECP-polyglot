//! MECP (Mesh Emergency Communication Protocol) encoder/decoder.
//!
//! Implements MECP-polyglot `spec/conformance.md`.
//!
//! ```
//! let d = mecp::decode("MECP/0/M01 M07 2pax 48.6520,20.1305");
//! assert!(d.valid);
//! assert_eq!(d.codes, ["M01", "M07"]);
//! assert_eq!(d.extracted.count, Some(2));
//! ```

#![forbid(unsafe_code)]

use regex_lite::Regex;
use std::sync::OnceLock;

pub const MAX_MESSAGE_BYTES: usize = 200;
pub const PREFIX: &str = "MECP/";
const INT_FIELD_MAX: u32 = i32::MAX as u32;

/// Warning and error identifiers (spec: "Warning and error ids").
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Warning {
    MissingPrefix,
    InvalidSeverity,
    MissingDelimiter,
    NoCodes,
    InvalidCode,
    OverLimit,
}

impl Warning {
    pub fn id(self) -> &'static str {
        match self {
            Warning::MissingPrefix => "missing_prefix",
            Warning::InvalidSeverity => "invalid_severity",
            Warning::MissingDelimiter => "missing_delimiter",
            Warning::NoCodes => "no_codes",
            Warning::InvalidCode => "invalid_code",
            Warning::OverLimit => "over_limit",
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
    pub count: Option<u32>,
    pub gps: Option<Gps>,
    pub eta: Option<u32>,
    pub reference: Option<String>,
    pub language: Option<String>,
    pub timestamp: Option<String>,
    pub callsign: Option<String>,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Decoded {
    pub valid: bool,
    pub severity: Option<u8>,
    pub codes: Vec<String>,
    pub is_drill: bool,
    pub freetext: Option<String>,
    pub extracted: Extracted,
    pub warnings: Vec<Warning>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Encoded {
    pub message: String,
    pub byte_length: usize,
    pub over_limit: bool,
    pub warnings: Vec<Warning>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Validation {
    pub valid: bool,
    pub errors: Vec<Warning>,
    pub warnings: Vec<Warning>,
}

/// ECMAScript whitespace.
fn is_ws(c: char) -> bool {
    matches!(c,
        '\u{09}'..='\u{0D}' | ' ' | '\u{A0}' | '\u{1680}' | '\u{2000}'..='\u{200A}'
        | '\u{2028}' | '\u{2029}' | '\u{202F}' | '\u{205F}' | '\u{3000}' | '\u{FEFF}')
}

fn trim(s: &str) -> &str {
    s.trim_matches(is_ws)
}

// Polyglot patterns: the same text in every implementation (spec "Patterns").
// WS holds literal characters, written with host-language string escapes.
const WS: &str =
    "[\t-\r \u{a0}\u{1680}\u{2000}-\u{200a}\u{2028}\u{2029}\u{202f}\u{205f}\u{3000}\u{feff}]";

struct Patterns {
    count: Regex,
    gps: Regex,
    eta: Regex,
    reference: Regex,
    language: Regex,
    timestamp: Regex,
    callsign: Regex,
}

fn patterns() -> &'static Patterns {
    static P: OnceLock<Patterns> = OnceLock::new();
    P.get_or_init(|| {
        let end = format!("(?:{WS}|$)");
        let re = |p: &str| Regex::new(p).expect("valid pattern");
        let bounded = |p: &str| re(&format!("{p}{end}"));
        Patterns {
            count: re(r"([0-9]+)pax"),
            gps: re(r"(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)"),
            eta: bounded(r"^([0-9]+)"),
            reference: re(r"#([A-Za-z0-9]{1,4})"),
            language: bounded(r"@([a-z]{2})"),
            timestamp: bounded(r"@([0-9]{4})"),
            callsign: bounded(r"~([A-Za-z0-9]{1,9})"),
        }
    })
}

/// Capture group 1 of the leftmost match of `re` in `s`.
fn find<'a>(re: &Regex, s: &'a str) -> Option<&'a str> {
    re.captures(s).map(|c| c.get(1).expect("group 1").as_str())
}

fn to_int(digits: &str) -> Option<u32> {
    digits.parse().ok().filter(|&v| v <= INT_FIELD_MAX)
}

pub fn is_mecp(s: &str) -> bool {
    s.starts_with(PREFIX)
}

pub fn is_code(token: &str) -> bool {
    let b = token.as_bytes();
    b.len() == 3 && b[0].is_ascii_uppercase() && b[1].is_ascii_digit() && b[2].is_ascii_digit()
}

pub fn is_beacon<S: AsRef<str>>(codes: &[S]) -> bool {
    codes.iter().any(|c| c.as_ref() == "B01")
}

pub fn is_beacon_ack<S: AsRef<str>>(codes: &[S]) -> bool {
    codes.iter().any(|c| c.as_ref() == "B02")
}

pub fn is_beacon_cancel<S: AsRef<str>>(codes: &[S]) -> bool {
    codes.iter().any(|c| c.as_ref() == "B03")
}

struct Header<'a> {
    severity: Option<u8>,
    has_delimiter: bool,
    body: &'a str,
}

/// `s` must start with PREFIX.
fn parse_header(s: &str) -> Header<'_> {
    let mut it = s[PREFIX.len()..].chars();
    let c5 = it.next();
    let c6 = it.next();
    Header {
        severity: match c5 {
            Some(c @ '0'..='3') => Some(c as u8 - b'0'),
            _ => None,
        },
        has_delimiter: c6 == Some('/'),
        body: it.as_str(),
    }
}

fn extract(text: &str, codes: &[String]) -> Extracted {
    let p = patterns();
    let mut x = Extracted::default();

    x.count = find(&p.count, text).and_then(to_int);
    if let Some(c) = p.gps.captures(text) {
        let lat: f64 = c[1].parse().unwrap_or(f64::NAN);
        let lon: f64 = c[2].parse().unwrap_or(f64::NAN);
        if (-90.0..=90.0).contains(&lat) && (-180.0..=180.0).contains(&lon) {
            x.gps = Some(Gps { lat, lon });
        }
    }
    if codes.iter().any(|c| c == "R03") {
        x.eta = find(&p.eta, text).and_then(to_int);
    }
    x.reference = find(&p.reference, text).map(String::from);
    x.language = find(&p.language, text).map(String::from);
    x.timestamp = find(&p.timestamp, text)
        .filter(|t| to_int(&t[..2]) <= Some(23) && to_int(&t[2..]) <= Some(59))
        .map(String::from);
    x.callsign = find(&p.callsign, text).map(String::from);
    x
}

pub fn decode(s: &str) -> Decoded {
    let mut d = Decoded::default();
    if !is_mecp(s) {
        return d;
    }

    let h = parse_header(s);
    d.severity = h.severity;
    if h.severity.is_none() {
        d.warnings.push(Warning::InvalidSeverity);
    }
    if !h.has_delimiter {
        d.warnings.push(Warning::MissingDelimiter);
    }

    if trim(h.body).is_empty() {
        d.valid = h.severity.is_some();
        if d.valid {
            d.warnings.push(Warning::NoCodes);
        }
        return d;
    }

    let tokens: Vec<&str> = h.body.split(' ').filter(|t| !t.is_empty()).collect();
    let n_codes = tokens.iter().take_while(|t| is_code(t)).count();
    d.codes = tokens[..n_codes].iter().map(|t| t.to_string()).collect();
    if n_codes < tokens.len() {
        let ft = tokens[n_codes..].join(" ");
        d.extracted = extract(&ft, &d.codes);
        d.freetext = Some(ft);
    }

    d.is_drill = d.codes.iter().any(|c| c == "D01" || c == "D02");
    d.valid = h.severity.is_some();
    d
}

pub fn encode<S: AsRef<str>>(severity: i32, codes: &[S], freetext: Option<&str>) -> Encoded {
    let mut warnings = Vec::new();
    if !(0..=3).contains(&severity) {
        warnings.push(Warning::InvalidSeverity);
    }
    for c in codes {
        if !is_code(c.as_ref()) {
            warnings.push(Warning::InvalidCode);
        }
    }

    let joined: Vec<&str> = codes.iter().map(AsRef::as_ref).collect();
    let mut message = format!("{PREFIX}{severity}/{}", joined.join(" "));
    if let Some(ft) = freetext.map(trim).filter(|ft| !ft.is_empty()) {
        message.push(' ');
        message.push_str(ft);
    }
    let message = message.trim_end_matches(is_ws).to_string();

    let byte_length = message.len();
    let over_limit = byte_length > MAX_MESSAGE_BYTES;
    if over_limit {
        warnings.push(Warning::OverLimit);
    }
    Encoded { message, byte_length, over_limit, warnings }
}

pub fn validate(s: &str) -> Validation {
    if !is_mecp(s) {
        return Validation { valid: false, errors: vec![Warning::MissingPrefix], warnings: vec![] };
    }
    let h = parse_header(s);
    let mut errors = Vec::new();
    let mut warnings = Vec::new();
    if h.severity.is_none() {
        errors.push(Warning::InvalidSeverity);
    }
    if !h.has_delimiter {
        errors.push(Warning::MissingDelimiter);
    }
    if trim(h.body).is_empty() {
        warnings.push(Warning::NoCodes);
    }
    if s.len() > MAX_MESSAGE_BYTES {
        warnings.push(Warning::OverLimit);
    }
    Validation { valid: errors.is_empty(), errors, warnings }
}
