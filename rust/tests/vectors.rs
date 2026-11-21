use serde_json::{json, Value};

const FIELDS: [&str; 7] = ["pax", "gps", "timestamp", "language", "callsign", "reference", "duration"];

fn read(rel: &str) -> Value {
    let path = format!("{}/../{rel}", env!("CARGO_MANIFEST_DIR"));
    serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

fn ids(es: &[mecp::ErrorId]) -> Value {
    es.iter().map(|e| e.id()).collect::<Vec<_>>().into()
}

fn extracted_json(x: &mecp::Extracted) -> Value {
    json!({
        "pax": x.pax,
        "gps": x.gps.map(|g| json!({"lat": g.lat, "lon": g.lon})),
        "timestamp": x.timestamp,
        "language": x.language,
        "callsign": x.callsign,
        "reference": x.reference,
        "duration": x.duration,
    })
}

fn decoded_json(d: &mecp::Decoded) -> Value {
    json!({
        "valid": d.valid,
        "severity": d.severity,
        "codes": d.codes,
        "is_drill": d.is_drill,
        "freetext": d.freetext,
        "extracted": extracted_json(&d.extracted),
    })
}

/// Collects mismatches so one run reports every failing case.
fn check(failures: Vec<String>) {
    assert!(failures.is_empty(), "{} failures:\n{}", failures.len(), failures.join("\n"));
}

#[test]
fn decode_vectors() {
    let mut bad = Vec::new();
    for case in read("vectors/mecp-vectors.json")["decode"].as_array().unwrap() {
        let got = decoded_json(&mecp::decode(case["input"].as_str().unwrap()));
        if got != case["expect"] {
            bad.push(format!("{}: got {got}, want {}", case["name"], case["expect"]));
        }
    }
    check(bad);
}

#[test]
fn encode_vectors() {
    let mut bad = Vec::new();
    for case in read("vectors/mecp-vectors.json")["encode"].as_array().unwrap() {
        let codes: Vec<&str> =
            case["codes"].as_array().unwrap().iter().map(|c| c.as_str().unwrap()).collect();
        let e = mecp::encode(case["severity"].as_i64().unwrap() as i32, &codes, case["freetext"].as_str());
        let got = json!({"message": e.message, "byte_length": e.byte_length, "errors": ids(&e.errors)});
        if got != case["expect"] {
            bad.push(format!("{}: got {got}, want {}", case["name"], case["expect"]));
        }
    }
    check(bad);
}

#[test]
fn validate_vectors() {
    let mut bad = Vec::new();
    for case in read("vectors/mecp-vectors.json")["validate"].as_array().unwrap() {
        let v = mecp::validate(case["input"].as_str().unwrap());
        let got = json!({"valid": v.valid, "errors": ids(&v.errors)});
        if got != case["expect"] {
            bad.push(format!("{}: got {got}, want {}", case["name"], case["expect"]));
        }
    }
    check(bad);
}

/// mecp-org/MECP freetext/tests.json, run unchanged.
#[test]
fn upstream_freetext() {
    assert_eq!(read("upstream/freetext/manifest.json")["schemaVersion"], 2);
    let mut bad = Vec::new();
    for t in read("upstream/freetext/tests.json").as_array().unwrap() {
        let d = mecp::decode(t["input"].as_str().unwrap());
        let ok = match &t["expect"] {
            Value::Null => !d.valid,
            exp => {
                let want: serde_json::Map<String, Value> =
                    FIELDS.iter().map(|f| (f.to_string(), exp.get(f).cloned().unwrap_or(Value::Null))).collect();
                d.valid && extracted_json(&d.extracted) == Value::Object(want)
            }
        };
        if !ok {
            bad.push(format!("{}: got {}", t["title"], decoded_json(&d)));
        }
    }
    check(bad);
}

#[test]
fn beacon_helpers() {
    let d = mecp::decode("MECP/0/B01 B02 B03");
    assert!(mecp::is_beacon(&d.codes));
    assert!(mecp::is_beacon_ack(&d.codes));
    assert!(mecp::is_beacon_cancel(&d.codes));
    assert!(!mecp::is_beacon(&["M01"]));
    assert_eq!(mecp::MECP_VERSION, "1.4.1");
}
