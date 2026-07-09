# Ephemera

> **The Operating System for Offensive Security Workflows.**

Imagine a penetration test where every security tool shares the same brain.

Nmap discovers open services.

ffuf finds hidden endpoints.

Gobuster maps directories.

Nikto fingerprints technologies.

Burp captures authentication.

Your Python scripts generate custom findings.

Future AI agents reason over everything.

Instead of every tool working in isolation, **all discoveries become part of one continuously growing security knowledge graph.**

No copy-paste.

No forgotten tokens.

No repeated enumeration.

No rebuilding context.

One memory.

One workflow.

One source of truth.

---

# The Vision

Ephemera is building a **Security Context Engine**.

Rather than creating another scanner, proxy, or exploitation framework, Ephemera acts as the intelligence layer between existing security tools.

Its long-term goal is to become the missing infrastructure that allows the entire offensive security ecosystem to collaborate automatically.

Future versions aim to support:

- Shared memory between dozens of security tools
- Automatic context synchronization
- Token and session lifecycle management
- Endpoint intelligence
- Technology fingerprint sharing
- Attack timeline reconstruction
- Plugin ecosystem
- AI-assisted offensive workflows
- Team collaboration
- Distributed context sharing
- Intelligent automation powered by accumulated knowledge

The objective is simple:

> **Run your tools. Ephemera remembers everything.**

---

# Foundation (v0.1.0)

Every large system starts with a small, reliable core.

Version **0.1.0** is the first working foundation that proves the architecture.

Current capabilities include:

- HTTP(S) interception using mitmproxy
- Persistent SQLite memory
- Automatic endpoint discovery
- Security timeline engine
- JSON token extraction
- Target-scoped storage
- JSON & Markdown export
- Automated testing with high core coverage

While intentionally small, this version validates the central idea:

**Security tools no longer need to work alone.**

---

# Why This Matters

Today's penetration testing workflow is fragmented.

Every tool discovers valuable information but keeps that information to itself.

Security professionals constantly switch between terminals, Burp projects, screenshots, notes, browser tabs, and scripts while manually moving context from one place to another.

Ephemera removes that friction by becoming the shared memory layer for the entire assessment.

---

# Roadmap

## v0.2
- Native support for common security tools
- Context synchronization
- Variable injection
- Cookie extraction
- JWT claim extraction
- Better reporting
- Improved CLI

## v0.5
- Plugin SDK
- Advanced extraction engine
- Cross-tool workflows
- Rich reporting
- Workflow automation

## v1.0
- Complete Security Context Engine
- Broad offensive security ecosystem support
- AI-assisted workflows
- Team collaboration
- Enterprise-ready architecture

---

# Contributing

Ephemera is an open-source project built in public.

Whether you're a:

- Penetration Tester
- Security Researcher
- Blue Team Engineer
- Python Developer
- Rust Developer
- Student
- Open Source Contributor

your ideas, discussions, bug reports, documentation improvements, and pull requests are all welcome.

We're not just building another security tool.

We're building the missing layer that connects them all.

---

# Responsible Use

Ephemera is intended exclusively for authorized security testing and research.

It does not automate exploitation and should only be used on systems you are authorized to assess.

---

# License

Licensed under the Apache License 2.0.
