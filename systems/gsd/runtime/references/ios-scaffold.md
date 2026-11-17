# iOS App Scaffold Reference

Rules and patterns for scaffolding iOS applications. Apply when any plan involves creating a new iOS app target.

---

## Critical Rule: Never Use Package.swift as the Primary Build System for iOS Apps

**NEVER use `Package.swift` with `.executableTarget` (or `.target`) to scaffold an iOS app.** Swift Package Manager executable targets compile as macOS command-line tools — they do not produce `.app` bundles, cannot be signed for iOS devices, and cannot be submitted to the App Store.

**Prohibited pattern:**
```swift
// Package.swift — DO NOT USE for iOS apps
.executableTarget(name: "MyApp", dependencies: [])
// or
.target(name: "MyApp", dependencies: [])
```

Using this pattern produces a macOS CLI binary, not an iOS app. The app will not build for any iOS simulator or device.

---

## Required Pattern: XcodeGen

All iOS app scaffolding MUST use XcodeGen to generate the `.xcodeproj`.

### Step 1 — Install XcodeGen (if not present)

```bash
brew install xcodegen
```

### Step 2 — Create `project.yml`

`project.yml` is the XcodeGen spec that describes the project structure. Minimum viable spec:

```yaml
name: MyApp
options:
  bundleIdPrefix: com.example
  deploymentTarget:
    iOS: "17.0"
settings:
  SWIFT_VERSION: "5.10"
  IPHONEOS_DEPLOYMENT_TARGET: "17.0"
targets:
  MyApp:
    type: application
    platform: iOS
    sources: [Sources/MyApp]
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: com.example.MyApp
      INFOPLIST_FILE: Sources/MyApp/Info.plist
    scheme:
      testTargets:
        - MyAppTests
  MyAppTests:
    type: bundle.unit-test
    platform: iOS
    sources: [Tests/MyAppTests]
    dependencies:
      - target: MyApp
```

### Step 3 — Generate the .xcodeproj

```bash
xcodegen generate
```

This creates `MyApp.xcodeproj` in the project root. Commit `project.yml` but add `*.xcodeproj` to `.gitignore` (regenerate on checkout).

### Step 4 — Standard project layout

```
MyApp/
├── project.yml              # XcodeGen spec — commit this
