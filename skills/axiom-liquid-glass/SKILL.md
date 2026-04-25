---
name: axiom-liquid-glass
description: Apple Liquid Glass design system — comprehensive design philosophy, implementation guide, and technical API reference from WWDC 2025. Covers design principles (iOS-native glass hierarchy, restraint over spectacle), implementation patterns (Regular vs Clear variants, SwiftUI glassEffect API, scroll edge effects, tinting), platform adaptation (iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+), accessibility, performance, testing, design review frameworks, and iOS-native UI redesign guidance.
user-invocable: true
skill_type: discipline
version: 1.2.0
apple_platforms: iOS 26+, iPadOS 26+, macOS Tahoe+, visionOS 3+
---

# Liquid Glass — Apple's Design System

## When to Use This Skill

- Implementing Liquid Glass effects in your app
- Reviewing existing UI for Liquid Glass adoption opportunities
- Debugging visual artifacts with Liquid Glass materials
- Optimizing Liquid Glass performance
- Requesting expert review of Liquid Glass implementation
- Redesigning a mobile app UI to feel iOS-native with glass materials
- Understanding Regular vs Clear variants, tinting, legibility
- Conducting design reviews with professional push-back frameworks

---

## Part 1: Design Philosophy

### Core Principles

- **Native over custom** — Use system components and patterns first
- **Restraint over spectacle** — Glass is a tool for hierarchy, not decoration
- **Material is functional, not decorative** — Improves clarity and depth
- **"Feels obvious" rather than "looks fancy"** — Calm, confident, inevitable
- **Glass complements content** — Lets content shine through

Avoid trendy glassmorphism gimmicks. Glass effects should appear only where they improve clarity and depth. Every screen should feel like it belongs in a first-party Apple app.

### What is Liquid Glass?

Liquid Glass is Apple's next-generation material design system introduced at WWDC 2025. It represents a significant evolution from previous materials (Aqua, iOS 7 blurs, Dynamic Island) by creating a new digital meta-material that:

- **Dynamically bends and shapes light** (lensing) rather than scattering it
- **Moves organically** like a lightweight liquid, responding to touch and app dynamism
- **Adapts automatically** to size, environment, content, and light/dark modes
- **Unifies design language** across all Apple platforms

### iOS Material Hierarchy

Use glass materials to express depth and context:

| Material | Use For | Visual Weight |
|----------|---------|---------------|
| Ultra-thin | Subtle overlays, toolbars, floating controls | Lightest |
| Regular | Cards needing gentle separation | Medium |
| Thick | Bottom sheets, modals, areas requiring strong readability | Heaviest |

**Rules:**
- Background must remain legible through blur (never "muddy")
- Material opacity and blur should scale with background complexity
- Prefer fewer, larger glass surfaces over many small glass chips

---

## Part 2: Visual Properties

### 1. Lensing (Primary Characteristic)

Liquid Glass defines itself through **lensing** — the warping and bending of light that communicates presence, motion, and form. Unlike previous materials that scattered light, Liquid Glass uses instinctive visual cues from the natural world.

- Dynamically concentrates and shapes light in real-time
- Provides definition against background while feeling visually grounded
- Controls feel ultra-lightweight and transparent while visually distinguishable
- Elements materialize in/out by modulating light bending (not fading)

### 2. Motion & Fluidity

- **Instant flex and energize** — Responds to interaction by flexing with light
- **Gel-like flexibility** — Communicates transient, malleable nature
- **Temporary lift** — Elements can lift into Liquid Glass on interaction
- **Dynamic morphing** — Continuously shape-shifts between app states
- **Lightweight transitions** — Menus pop open in-line, maintaining relationship to source
- Smooth, natural easing (no playful bounce unless system-like)
- Motion explains hierarchy, not decoration

### 3. Adaptive Behavior

Liquid Glass **continuously adapts** without fixed light/dark appearance:

- Shadows become more prominent when text scrolls underneath
- Tint and dynamic range shift to ensure legibility
- Independently switches light/dark to feel at home in any context
- Larger elements (menus, sidebars) simulate thicker material
- Ambient environment subtly spills onto surface

---

## Part 3: Implementation Guide

### Basic API Usage — SwiftUI `glassEffect` Modifier

```swift
// Basic usage - applies glass within capsule shape
Text("Hello")
    .glassEffect()

// Custom shape
Text("Hello")
    .glassEffect(in: RoundedRectangle(cornerRadius: 12))

// Interactive elements (iOS)
Button("Tap Me") { }
    .glassEffect()
    .interactive()
```

**Automatic Adoption**: Simply recompiling with Xcode 26 brings Liquid Glass to standard controls automatically.

### Variants: Regular vs Clear

**CRITICAL DECISION**: Never mix Regular and Clear in the same interface.

#### Regular Variant (Default — Use 95% of the Time)

- Most versatile, full visual and adaptive effects
- Provides legibility regardless of context
- Works in any size, over any content

**When to use**: Navigation bars, tab bars, toolbars, buttons, menus, sidebars

```swift
NavigationView {
    // Content
}
.glassEffect() // Uses Regular variant by default
```

#### Clear Variant (Special Cases Only)

- Permanently more transparent, no adaptive behaviors
- **Requires dimming layer** for legibility

**Use ONLY when ALL three conditions are met**:
1. Element is over **media-rich content**
2. Content layer won't be negatively affected by **dimming layer**
3. Content above glass is **bold and bright**

```swift
ZStack {
    MediaRichBackground()
        .overlay(.black.opacity(0.3)) // Dimming layer
    BoldBrightControl()
        .glassEffect(.clear)
}
```

**WARNING**: Using Clear without meeting all three conditions results in poor legibility.

### Design Principles & Best Practices

#### Reserve Glass for Navigation Layer

```
[Content Layer — No Glass]
    |
[Navigation Layer — Liquid Glass]
    - Tab bars, Navigation bars, Toolbars, Floating controls
```

#### DO NOT Use on Content Layer

```swift
// WRONG
List(items) { item in
    Text(item.name)
}
.glassEffect() // Competes with navigation, muddy hierarchy
```

#### DO NOT Stack Glass on Glass

```swift
// WRONG
ZStack {
    NavigationBar().glassEffect()
    FloatingButton().glassEffect() // Glass on glass
}

// CORRECT
ZStack {
    NavigationBar().glassEffect()
    FloatingButton()
        .foregroundStyle(.primary) // Use fills, transparency, vibrancy
}
```

#### Avoid Content Intersections in Steady State

Reposition or scale content to maintain separation. Intersections are acceptable during scrolling/transitions.

---

## Part 4: Tinting & Color

### Adaptive Tinting System

1. Selecting color generates range of tones
2. Tones mapped to content brightness underneath
3. Changes hue, brightness, saturation based on background
4. Doesn't deviate too much from intended color

```swift
Button("Primary Action") { }
    .tint(.red)
    .glassEffect()
```

### Tinting Rules

- **DO**: Use tinting for primary actions only
- **DON'T**: Tint everything (when everything is tinted, nothing stands out)
- **DON'T**: Use solid fills on glass elements (breaks visual character)
- Use color in content layer instead, reserve tinting for primary UI actions

```swift
// WRONG - Solid fill breaks glass character
Button("Action") {}
    .background(.red) // Opaque

// CORRECT - Transparent, grounded
Button("Action") {}
    .tint(.red)
    .glassEffect()
```

---

## Part 5: Scroll Edge Effects

Work in concert with Liquid Glass to maintain separation with scrolling content.

- Content scrolling -> effect gently dissolves content into background
- Lifts glass visually above moving content
- Darker content triggers dark style for contrast

### Hard Style Effect

Use when pinned accessory views exist:

```swift
ScrollView { }
    .scrollEdgeEffect(.hard)
```

---

## Part 6: Layout & Component Patterns

### Typography
- System-first typography (SF Pro style)
- Clear hierarchy using size & weight, not color
- Prefer semantic text styles (Title / Headline / Body / Caption)

### Color
- Neutral palette by default (white, off-white, system grays)
- Accent colors used sparingly (1 primary accent max)
- Avoid neon, high saturation blocks, heavy gradients

### Buttons
- Prefer system button semantics
- Glass button usage: only for floating contexts (toolbar, overlay)
- Press state: slight opacity down + subtle scale, never flashy

### Lists
- iOS list rhythm (consistent row height, predictable spacing)
- Glass behind lists: only if list is within a sheet/overlay
- Ensure text contrast and scannability remain high

### Navigation
- Standard navigation bars with large titles when appropriate
- Translucent nav bar when content scrolls under it
- Preserve clear title hierarchy and scroll behavior

### Modals & Sheets
- Bottom sheets preferred, respect drag-to-dismiss
- Regular/Thick material based on background complexity
- Avoid full-screen modal unless task truly demands it

### Layout Principles
- iOS-native layout patterns, safe-area aware
- Comfortable touch targets (44pt+)
- Use whitespace and grouping as main separators
- Cards should feel light and system-like

---

## Part 7: Layered System Architecture

### 1. Highlights Layer
- Light sources produce highlights responding to geometry
- Lights move during interactions, defining silhouette
- Some respond to device motion

### 2. Shadows Layer
- Aware of background content
- Increases shadow opacity over text for separation
- Lowers shadow opacity over solid light backgrounds

### 3. Internal Glow (Interaction Feedback)
- Illuminates from within on interaction
- Glow starts under fingertips, spreads throughout
- Spreads to nearby Liquid Glass elements

### 4. Adaptive Tinting Layer
- Multiple layers adapt together
- Windows losing focus visually recede (Mac/iPad)

---

## Part 8: Accessibility

Liquid Glass offers accessibility features that modify material **without sacrificing its magic**:

| Feature | Effect | Developer Action |
|---------|--------|-----------------|
| Reduced Transparency | Makes glass frostier, obscures more | Automatic |
| Increased Contrast | Elements predominantly black/white with contrasting border | Automatic |
| Reduced Motion | Decreases intensity, disables elastic properties | Automatic |

**No developer action required** — all features apply automatically when using Liquid Glass.

---

## Part 9: Performance Considerations

### View Hierarchy
- Regular variant optimized for performance
- Avoid excessive nesting of glass elements
- Flatten hierarchy when possible

```swift
// WRONG - Deep nesting
ZStack {
    GlassContainer1().glassEffect()
    ZStack {
        GlassContainer2().glassEffect()
    }
}

// CORRECT - Flat hierarchy
VStack {
    GlassContainer1().glassEffect()
    GlassContainer2().glassEffect()
}
```

### Rendering Costs
- Don't animate Liquid Glass elements unnecessarily
- Use Clear variant sparingly (requires dimming layer computation)
- Profile with Instruments if experiencing performance issues

---

## Part 10: Testing

### Visual Regression Testing

```swift
func testLiquidGlassAppearance() {
    let app = XCUIApplication()
    app.launch()

    // Test light mode
    XCTContext.runActivity(named: "Light Mode Glass") { _ in
        let screenshot = app.screenshot()
    }

    // Test dark mode
    app.launchArguments = ["-UIUserInterfaceStyle", "dark"]
    app.launch()
    XCTContext.runActivity(named: "Dark Mode Glass") { _ in
        let screenshot = app.screenshot()
    }
}
```

### Critical Test Cases
- Light mode vs dark mode
- Reduced Transparency / Increased Contrast / Reduced Motion enabled
- Dynamic Type (larger text sizes)
- Content scrolling (verify scroll edge effects)
- Right-to-left languages

### Accessibility Testing

```swift
func testLiquidGlassAccessibility() {
    app.launchArguments += [
        "-UIAccessibilityIsReduceTransparencyEnabled", "1",
        "-UIAccessibilityButtonShapesEnabled", "1",
        "-UIAccessibilityIsReduceMotionEnabled", "1"
    ]
    XCTAssertTrue(glassElement.exists)
    XCTAssertTrue(glassElement.isHittable)
}
```

---

## Part 11: Design Review & Push-Back Framework

### Red Flags — Requests That Violate Guidelines

If you hear ANY of these, **STOP and reference the skill**:

- "Use Clear everywhere" — Clear requires three specific conditions
- "Glass looks better than fills" — Correct layer trumps aesthetics
- "Stack glass on glass for consistency" — Explicitly prohibited
- "Apply glass to Lists for sophistication" — Lists are content layer

### How to Push Back Professionally

**Step 1: Show the Framework**
```
"Let me show you Apple's guidance on Clear variant.
It requires THREE conditions:
1. Media-rich content background
2. Dimming layer for legibility
3. Bold, bright controls on top
Let me show which screens meet all three..."
```

**Step 2: Demonstrate the Risk**
Open the app on a device. Show Clear variant in low-contrast scenario (unreadable) vs Regular (legible).

**Step 3: Offer Compromise**
```
"Clear works beautifully in these hero sections where all three conditions apply.
Regular handles everything else with automatic legibility. Best of both worlds."
```

**Step 4: Document the Decision**
If overruled, send written documentation of the decision and monitoring plan.

---

## Part 12: Expert Review Checklist

### 1. Material Appropriateness
- [ ] Glass used only on navigation layer (not content)?
- [ ] Standard controls get glass automatically via Xcode 26 recompile?
- [ ] No glass-on-glass situations?

### 2. Variant Selection
- [ ] Regular variant used for most cases?
- [ ] Clear variant meets all three conditions where used?
- [ ] Regular and Clear never mixed in same interface?

### 3. Legibility & Contrast
- [ ] Primary actions selectively tinted (not everything)?
- [ ] Solid fills avoided on glass elements?
- [ ] Elements maintain legibility on various backgrounds?

### 4. Layering & Hierarchy
- [ ] Content intersections avoided in steady states?
- [ ] Elements on top of glass use fills/transparency (not glass)?
- [ ] Visual hierarchy clear (navigation vs content layer)?

### 5. Scroll Edge Effects
- [ ] Applied where glass meets scrolling content?
- [ ] Hard style used for pinned accessory views?

### 6. Accessibility
- [ ] Works with Reduced Transparency, Increased Contrast, Reduced Motion?
- [ ] Interactive elements hittable in all configurations?

### 7. Performance
- [ ] View hierarchy reasonably flat?
- [ ] Glass elements animated only when necessary?
- [ ] Clear variant used sparingly?

---

## Part 13: API Reference

### SwiftUI Modifiers

#### `glassEffect(in:isInteractive:)`

```swift
func glassEffect<S: Shape>(
    in shape: S = Capsule(),
    isInteractive: Bool = false
) -> some View
```

#### `glassEffect(_:in:isInteractive:)`

```swift
func glassEffect<S: Shape>(
    _ variant: GlassVariant,  // .regular or .clear
    in shape: S = Capsule(),
    isInteractive: Bool = false
) -> some View
```

#### `scrollEdgeEffect(_:)`

```swift
func scrollEdgeEffect(_ style: ScrollEdgeStyle) -> some View
// styles: .automatic, .soft, .hard
```

#### `scrollEdgeEffectStyle(_:for:)` (NEW in iOS 26)

```swift
func scrollEdgeEffectStyle(_ style: ScrollEdgeStyle, for edges: Edge.Set) -> some View
```

#### `glassBackgroundEffect()` (NEW in iOS 26)

Apply glass effect to custom views for reflecting surrounding content.

```swift
CustomPhotoGrid()
    .glassBackgroundEffect()
```

#### `GlassEffectContainer` (NEW in iOS 26)

Container for combining multiple Liquid Glass effects with optimized rendering.

```swift
GlassEffectContainer {
    HStack {
        Button("Action 1") { }.glassEffect()
        Button("Action 2") { }.glassEffect()
    }
}
```

Benefits: Optimizes rendering, fluid morphing between glass shapes, reduced compositor overhead.

### Toolbar Modifiers (NEW in iOS 26)

#### `Spacer(.fixed)` in Toolbars

Separates toolbar button groups with fixed spacing.

#### `.buttonStyle(.borderedProminent)` + `.tint()` in Toolbars

Makes toolbar items prominent with Liquid Glass tinting.

### Navigation & Search (NEW in iOS 26)

- **Bottom-aligned search** on iPhone (automatic with `.searchable()`)
- **Search tab role** with `.tabRole(.search)` — morphs into search field
- **Tab bar minimization** with `.tabBarMinimizationBehavior(.onScrollDown)`

### Types

```swift
enum GlassVariant {
    case regular  // Default - full adaptive behavior
    case clear    // More transparent, no adaptation
}

enum ScrollEdgeStyle {
    case automatic  // System determines
    case soft       // Gradual fade
    case hard       // Uniform across toolbar height
}
```

---

## Part 14: Backward Compatibility

### UIDesignRequiresCompatibility Key (NEW in iOS 26)

Add to Info.plist to maintain iOS 18 appearance while building with iOS 26 SDK:

```xml
<key>UIDesignRequiresCompatibility</key>
<true/>
```

**Migration strategy:**
1. Ship with key enabled
2. Audit interface changes in separate build
3. Update interface incrementally
4. Remove key when ready for Liquid Glass

---

## Output Requirements (For UI Redesigns)

For each redesigned screen, provide:

1. **Design intent** — What feels more iOS-native and why
2. **Layout structure** — Regions, spacing, safe-area decisions
3. **Material map** — Where glass is used, which thickness, and why
4. **Typography map** — Text styles and hierarchy rationale
5. **Interaction & motion notes** — Scroll, transitions, gestures
6. **iOS-native justification** — System defaults, familiarity, clarity

---

## Absolute Avoid List

- Over-designed custom components
- Glass everywhere (blanket translucency)
- Trendy gimmicks (neon, glow, heavy gradients, fake reflections)
- Harsh borders or outlines
- Dense, cluttered information layouts
- Non-standard navigation patterns
- Solid opaque fills on glass elements

---

## Resources

**WWDC**: 2025-219, 2025-323, 2025-256
**Docs**: /technologyoverviews/adopting-liquid-glass, /swiftui/landmarks-building-an-app-with-liquid-glass, /swiftui/applying-liquid-glass-to-custom-views
**Related Skills**: axiom-liquid-glass-ref, swiftui-liquid-glass
**Platforms:** iOS 26+, iPadOS 26+, macOS Tahoe, visionOS 3
**Xcode:** 26+
