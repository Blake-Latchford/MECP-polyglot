pluginManagement {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}

rootProject.name = "mecp-adapter-tak-bridge"

plugins {
    // Same as the client's build: fetch the JDK when none is installed.
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
}
