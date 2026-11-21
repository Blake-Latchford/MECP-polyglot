// stdin:  <id>\t<hex utf-8 input>     stdout: one JSON record per line.
// With --codes: stdout is a JSON array of the codes in MecpCodes.CODES.
// Representation-only mapping; no protocol logic lives here.
import org.coloradomesh.meshcore.protocol.Mecp
import org.coloradomesh.meshcore.protocol.MecpCodes

fun unhex(s: String): String =
    String(ByteArray(s.length / 2) { s.substring(it * 2, it * 2 + 2).toInt(16).toByte() }, Charsets.UTF_8)

fun q(s: String?): String {
    if (s == null) return "null"
    val b = StringBuilder("\"")
    for (c in s) when {
        c == '"' -> b.append("\\\"")
        c == '\\' -> b.append("\\\\")
        c.code < 0x20 || c in '\u007f'..'\u009f' || c == '\u2028' || c == '\u2029' ->
            b.append(String.format("\\u%04x", c.code))
        else -> b.append(c)
    }
    return b.append('"').toString()
}

fun record(input: String): String {
    val m = Mecp.parse(input) ?: return """{"valid":false}"""
    val gps = if (m.latitude != null && m.longitude != null)
        """{"lat":${m.latitude},"lon":${m.longitude}}""" else "null"
    // The field is `time` since meshcore-kotlin#15 (MECP 1.4.0) and `timeUtc` before it.
    val getter = m.javaClass.methods.first { it.name == "getTime" || it.name == "getTimeUtc" }
    val ts = (getter.invoke(m) as String?)?.let { if (':' in it) it else "${it.substring(0, 2)}:${it.substring(2)}" }
    return buildString {
        append("""{"valid":true,"severity":${m.severity},""")
        append(""""codes":[${m.codes.joinToString(",") { q(it) }}],""")
        append(""""freetext":${q(m.freeText)},"pax":${m.people},"gps":$gps,""")
        append(""""timestamp":${q(ts)},"language":${q(m.language)},"callsign":${q(m.callsign)},""")
        append(""""reference":${q(m.reference)},"duration":${m.etaMinutes}}""")
    }
}

fun main(args: Array<String>) {
    if ("--codes" in args) {
        println(MecpCodes.CODES.keys.joinToString(",", "[", "]") { q(it) })
        return
    }
    val out = System.out.bufferedWriter()
    generateSequence(::readLine).filter { it.isNotEmpty() }.forEach { line ->
        val (id, hex) = line.split('\t', limit = 2)
        val body = try {
            "\"result\":" + record(unhex(hex))
        } catch (e: Throwable) {
            "\"error\":" + q("${e::class.simpleName}: ${e.message}")
        }
        out.write("{\"id\":${q(id)},$body}\n")
    }
    out.flush()
}
