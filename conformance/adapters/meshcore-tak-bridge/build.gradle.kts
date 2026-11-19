// Conformance adapter for meshcore-tak-bridge's Kotlin MECP decoder.
// Compiles the client's own sources in place (nothing is copied into this repo).
// Point at a checkout with -PclientDir=/path/to/meshcore-tak-bridge.
plugins {
    kotlin("jvm") version "2.0.21"
    application
}

repositories { mavenCentral() }

val clientDir = (findProperty("clientDir") as String?)
    ?: "${rootDir}/../../../../meshcore-tak-bridge"
val protocolSrc = "$clientDir/meshcore-kotlin/protocol/src/main/kotlin"


sourceSets.main {
    kotlin.srcDir("src/main/kotlin")
    kotlin.srcDir(protocolSrc)
    // Only the files the decoder needs; the rest pull in BLE/companion code.
    kotlin.filter.include("Adapter.kt", "**/Mecp.kt", "**/MecpCodes.kt", "**/ChannelReplies.kt")
}

kotlin { jvmToolchain(17) }

application { mainClass.set("AdapterKt") }
