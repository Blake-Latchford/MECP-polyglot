// Conformance adapter for MeshCore One (MC1): MECPDecode.decode().
//
// Compiled into one module together with MC1's own MECP sources from the
// client checkout (see build.sh), so no MC1 code is copied here. Reads
// `id<TAB>hex(utf-8)` lines, writes one JSON record per line. Representation
// only: timestampHHMM "1430" becomes "14:30".
//
// `mc1-adapter --codes <MECP/Languages dir>` instead prints a JSON array of the
// codes in MC1's English pack, loaded by MECPCatalog itself.

import Foundation

// SwiftPM generates Bundle.module for MC1's resources; swiftc does not. Only
// MECPCatalog's default arguments use it; --codes passes the pack directory.
extension Bundle {
    static let module = Bundle.main
}

let args = CommandLine.arguments
if args.count == 3, args[1] == "--codes" {
    guard let dir = Bundle(path: args[2]),
          let pack = MECPCatalog.languagePack(stem: MECPCatalog.englishStem, resourceBundle: dir) else {
        FileHandle.standardError.write("no English pack in \(args[2])\n".data(using: .utf8)!)
        exit(1)
    }
    let data = try! JSONEncoder().encode(pack.codes.keys.sorted())
    print(String(decoding: data, as: UTF8.self))
    exit(0)
}

struct Record: Encodable {
    var valid: Bool
    var severity: Int?
    var codes: [String]?
    var freetext: String?
    var pax: Int?
    var timestamp: String?
    var duration: Int?
}

struct Line: Encodable {
    var id: String
    var result: Record
}

func bytes(fromHex hex: Substring) -> [UInt8] {
    var out: [UInt8] = []
    var i = hex.startIndex
    while i < hex.endIndex {
        let j = hex.index(i, offsetBy: 2)
        out.append(UInt8(hex[i..<j], radix: 16)!)
        i = j
    }
    return out
}

let encoder = JSONEncoder()
while let line = readLine(strippingNewline: true) {
    guard let tab = line.firstIndex(of: "\t") else { continue }
    let id = String(line[..<tab])
    let input = String(decoding: bytes(fromHex: line[line.index(after: tab)...]), as: UTF8.self)
    var rec = Record(valid: false)
    if let m = MECPDecode.decode(input) {
        rec.valid = true
        rec.severity = m.severity.rawValue
        rec.codes = m.codes
        rec.freetext = m.freetext
        rec.pax = m.personCount
        if let t = m.timestampHHMM {
            rec.timestamp = "\(t.prefix(2)):\(t.suffix(2))"
        }
        rec.duration = m.eta
    }
    let data = try! encoder.encode(Line(id: id, result: rec))
    print(String(decoding: data, as: UTF8.self))
}
