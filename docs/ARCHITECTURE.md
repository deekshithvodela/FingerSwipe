# FingerSwipe Architecture — Frozen for 1.0

Status: approved and frozen on 2026-07-01.

FingerSwipe is a Linux-only per-user service. It converts three-finger vertical
libinput swipe updates into changes to the default PipeWire audio sink volume.

## Boundaries

- `libfingerswipe.so` is a C23 shared library. It owns libudev, libinput, and
  PipeWire resources and exposes a versioned C ABI containing opaque handles,
  value event structures, bounded polling, normalized volume operations, and
  stable error codes.
- The Python 3.13 package owns configuration, gesture filtering and curves,
  controller policy, process lifecycle, signal handling, and logging. Python
  accesses the native library only through `ctypes` adapters.
- The event-processing path is synchronous and single-threaded. PipeWire's
  required loop is private to the native audio handle. No Python object is
  accessed from a native thread.

## Ownership and lifecycle

Native constructors return exclusively owned opaque handles. Destructors accept
null, stop internal loops, disconnect external resources, and free the handle.
Python adapters are context managers and make closure idempotent. Application
startup is configuration, logging, native input, native audio, then processing;
shutdown occurs in reverse order on normal completion, signal, or failure.

## Stable behavior

- Only exactly three-finger swipe gestures are accepted.
- Vertical motion changes the current default sink volume and horizontal motion
  is ignored by the volume controller.
- Volume is normalized and clamped to the configured inclusive range.
- Configuration uses `$XDG_CONFIG_HOME/fingerswipe/config.yaml`, falling back to
  `~/.config/fingerswipe/config.yaml`; an explicit CLI path takes precedence.
- Missing configuration uses documented defaults. Present malformed or unknown
  configuration is fatal.
- Human and JSON logs are written to stderr and therefore captured by journald.
- Device access is granted by udev session ACLs; the application never runs as
  root and is installed as a systemd user service.

## Compatibility and verification

The exported C ABI carries a numeric ABI version and hides all implementation
structures. Python public interfaces are typed. Pure policy is unit-tested with
fakes; native integration tests may skip when hardware or a user PipeWire
session is absent. CMake builds and installs the native library and public
headers; the Python wheel contains no private native implementation.

These decisions are immutable under `ENGINEERING_PROTOCOL.md` Rule 2.
