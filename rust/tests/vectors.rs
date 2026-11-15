use serde_json::{json, Value};

fn vectors() -> Value {
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../vectors/mecp-vectors.json");
    serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

fn ids(ws: &[mecp::Warning]) -> Value {
    ws.iter().map(|w| w.id()).collect::<Vec<_>>().into()
}

fn decoded_json(d: &mecp::Decoded) -> Value {
    let x = &d.extracted;
    json!({
        "valid": d.valid,
        "severity": d.severity,
        "codes": d.codes,
        "is_drill": d.is_drill,
        "freetext": d.freetext,
        "extracted": {
            "count": x.count,
            "gps": x.gps.map(|g| json!({"lat": g.lat, "lon": g.lon})),
            "eta": x.eta,
            "reference": x.reference,
            "language": x.language,
            "timestamp": x.timestamp,
            "callsign": x.callsign,
        },
        "warnings": ids(&d.warnings),
    })
}

#[test]
fn decode_vectors() {
    for case in vectors()["decode"].as_array().unwrap() {
        let got = mecp::decode(case["input"].as_str().unwrap());
        assert_eq!(decoded_json(&got), case["expect"], "{}", case["name"]);
    }
}

#[test]
fn encode_vectors() {
    for case in vectors()["encode"].as_array().unwrap() {
        let codes: Vec<&str> =
            case["codes"].as_array().unwrap().iter().map(|c| c.as_str().unwrap()).collect();
        let got = mecp::encode(
            case["severity"].as_i64().unwrap() as i32,
            &codes,
            case["freetext"].as_str(),
        );
        let got = json!({
            "message": got.message,
            "byte_length": got.byte_length,
            "over_limit": got.over_limit,
            "warnings": ids(&got.warnings),
        });
        assert_eq!(got, case["expect"], "{}", case["name"]);
    }
}

#[test]
fn validate_vectors() {
    for case in vectors()["validate"].as_array().unwrap() {
        let got = mecp::validate(case["input"].as_str().unwrap());
        let got = json!({
            "valid": got.valid,
            "errors": ids(&got.errors),
            "warnings": ids(&got.warnings),
        });
        assert_eq!(got, case["expect"], "{}", case["name"]);
    }
}

#[test]
fn beacon_helpers() {
    let d = mecp::decode("MECP/0/B01 B02 B03");
    assert!(mecp::is_beacon(&d.codes));
    assert!(mecp::is_beacon_ack(&d.codes));
    assert!(mecp::is_beacon_cancel(&d.codes));
    assert!(!mecp::is_beacon(&["M01"]));
}
