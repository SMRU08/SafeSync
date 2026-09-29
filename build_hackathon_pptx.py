"""
build_hackathon_pptx.py
Official 6-Slide BPUT Hackathon 2026 Presentation Generator for SafeSync.
Follows the exact 6-slide template structure required by the evaluation committee:
1. TITLE PAGE
2. IDEA TITLE
3. TECHNICAL APPROACH
4. FEASIBILITY AND VIABILITY
5. IMPACT AND BENEFITS
6. RESEARCH AND REFERENCES
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Design Theme: Clean Professional Engineering (Dark on Light)
    COLOR_BG_CARD = RGBColor(248, 250, 252)     # #F8FAFC
    COLOR_BORDER = RGBColor(203, 213, 225)      # #CBD5E1
    COLOR_TITLE = RGBColor(15, 23, 42)          # #0F172A Dark Navy
    COLOR_PRIMARY = RGBColor(30, 58, 138)       # #1E3A8A Deep Blue
    COLOR_ACCENT = RGBColor(2, 132, 199)        # #0284C7 Engineering Blue
    COLOR_TEXT_DARK = RGBColor(30, 41, 59)      # #1E293B
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
    COLOR_GREEN = RGBColor(16, 149, 106)        # #10956A Emerald Green
    COLOR_LINE = RGBColor(226, 232, 240)        # #E2E8F0
    COLOR_WHITE = RGBColor(255, 255, 255)

    blank_layout = prs.slide_layouts[6]

    def add_slide_header(slide, slide_num, title_text, subtitle_text):
        # Top pill badge
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.733), Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = f"BPUT HACKATHON 2026   |   PROBLEM STATEMENT PS06   |   SLIDE {slide_num} OF 6"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT

        # Slide Main Title
        tb_t = slide.shapes.add_textbox(Inches(0.8), Inches(0.65), Inches(11.733), Inches(0.5))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TITLE

        # Subtitle
        if subtitle_text:
            tb_s = slide.shapes.add_textbox(Inches(0.8), Inches(1.15), Inches(11.733), Inches(0.3))
            tf_s = tb_s.text_frame
            tf_s.word_wrap = True
            tf_s.margin_left = tf_s.margin_top = tf_s.margin_right = tf_s.margin_bottom = 0
            p_s = tf_s.paragraphs[0]
            p_s.text = subtitle_text
            p_s.font.size = Pt(11)
            p_s.font.color.rgb = COLOR_TEXT_MUTED

        # Divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.733), Inches(0.015))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_LINE
        line.line.color.rgb = COLOR_LINE

    def add_card(slide, left, top, width, height, title, bg_col=COLOR_BG_CARD, border_col=COLOR_BORDER):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_col
        shape.line.color.rgb = border_col
        shape.line.width = Pt(1)

        # Title
        tb_t = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.12), width - Inches(0.36), Inches(0.32))
        tf_t = tb_t.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p = tf_t.paragraphs[0]
        p.text = title
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY

        # Body Frame
        tb_b = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.44), width - Inches(0.36), height - Inches(0.5))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = tf_b.margin_top = tf_b.margin_right = tf_b.margin_bottom = 0
        return tf_b

    # =========================================================================
    # SLIDE 1 — TITLE PAGE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)

    # Top Hero Header Banner
    hero = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.6), Inches(11.733), Inches(1.35))
    hero.fill.solid()
    hero.fill.fore_color.rgb = COLOR_TITLE
    hero.line.fill.background()

    tb_hero = s1.shapes.add_textbox(Inches(1.1), Inches(0.72), Inches(11.133), Inches(1.1))
    tf_h = tb_hero.text_frame
    tf_h.word_wrap = True
    p_h1 = tf_h.paragraphs[0]
    p_h1.text = "BPUT HACKATHON 2026   |   TITLE PAGE"
    p_h1.font.size = Pt(22)
    p_h1.font.bold = True
    p_h1.font.color.rgb = COLOR_WHITE

    p_h2 = tf_h.add_paragraph()
    p_h2.text = "Organized by Software Technology Parks of India (STPI) & EmTek"
    p_h2.font.size = Pt(12)
    p_h2.font.color.rgb = RGBColor(186, 230, 253)

    # Project Spotlight
    tb_sp = s1.shapes.add_textbox(Inches(0.8), Inches(2.1), Inches(11.733), Inches(0.95))
    tf_sp = tb_sp.text_frame
    p_s1 = tf_sp.paragraphs[0]
    p_s1.text = "SafeSync"
    p_s1.font.size = Pt(36)
    p_s1.font.bold = True
    p_s1.font.color.rgb = COLOR_PRIMARY

    p_s2 = tf_sp.add_paragraph()
    p_s2.text = "Autonomous AI Vision Platform for Industrial Safety Gear Compliance & Hazard Governance"
    p_s2.font.size = Pt(13)
    p_s2.font.color.rgb = COLOR_TEXT_MUTED

    # Left Metadata Box
    c_s1_l = add_card(s1, Inches(0.8), Inches(3.2), Inches(5.7), Inches(3.8), "PROBLEM STATEMENT SPECIFICATION")
    fields_l = [
        ("Problem Statement ID:", "PS06"),
        ("Problem Statement Title:", "Build a prototype AI system that detects safety gear compliance"),
        ("Theme:", "Artificial Intelligence & Computer Vision / Workplace Safety"),
        ("Category:", "Software (Edge AI & Full-Stack Web Application)"),
        ("Verification Status:", "Verified Prototype (250/250 Unit Tests • 39/39 Integration Scenarios)")
    ]
    for lbl, val in fields_l:
        p = c_s1_l.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"{lbl} "
        r1.font.size = Pt(11)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_TEXT_DARK
        r2 = p.add_run()
        r2.text = val
        r2.font.size = Pt(11)
        r2.font.color.rgb = COLOR_PRIMARY if "PS06" in val or "Verified" in val else COLOR_TEXT_MUTED

    # Right Metadata Box
    c_s1_r = add_card(s1, Inches(6.8), Inches(3.2), Inches(5.7), Inches(3.8), "TEAM & INSTITUTIONAL METADATA")
    fields_r = [
        ("Team ID:", "BPUT-PS06-XERSES (To Be Assigned)"),
        ("Team Name:", "XERSES"),
        ("College / Institution:", "Biju Patnaik University of Technology (BPUT) Affiliated Institute"),
        ("Department:", "Computer Science & Engineering (To Be Updated)"),
        ("Project Lead:", "Smruti Ranjan Nayak (@SMRU08)"),
        ("GitHub Repository:", "https://github.com/SMRU08/SafeSync.git")
    ]
    for lbl, val in fields_r:
        p = c_s1_r.add_paragraph()
        p.space_after = Pt(8)
        r1 = p.add_run()
        r1.text = f"{lbl} "
        r1.font.size = Pt(11)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_TEXT_DARK
        r2 = p.add_run()
        r2.text = val
        r2.font.size = Pt(11)
        r2.font.color.rgb = COLOR_PRIMARY if "XERSES" in val else COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 2 — IDEA TITLE
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_header(s2, 2, "IDEA TITLE", "SafeSync — Autonomous Industrial Safety Gear Compliance & Hazard Governance")

    # Card 1: Proposed Solution & How It Addresses Problem
    c_s2_sol = add_card(s2, Inches(0.8), Inches(1.7), Inches(5.7), Inches(2.55), "PROPOSED SOLUTION & HOW IT ADDRESSES PS06")
    p = c_s2_sol.add_paragraph()
    p.text = "PROPOSED SOLUTION:"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    p = c_s2_sol.add_paragraph()
    p.text = "SafeSync is an edge-compatible, multi-camera AI computer vision system designed to automate workplace safety monitoring. It continuously inspects live video streams, localizes workers, tracks movement paths, and evaluates Personal Protective Equipment (PPE) compliance while monitoring early flame and smoke hazards before escalation."
    p.font.size = Pt(9.5)
    p.font.color.rgb = COLOR_TEXT_DARK
    p.space_after = Pt(5)

    p = c_s2_sol.add_paragraph()
    p.text = "HOW IT ADDRESSES THE PROBLEM (PS06):"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    p = c_s2_sol.add_paragraph()
    p.text = "• Replaces intermittent manual walkthroughs with continuous 24/7 video surveillance.\n• Eliminates human monitor vigilance decay (which drops after 20–30 mins).\n• Delivers sub-second alerts with cryptographically signed photographic snapshots."
    p.font.size = Pt(9)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Card 2: Innovation / Uniqueness
    c_s2_inn = add_card(s2, Inches(6.8), Inches(1.7), Inches(5.7), Inches(2.55), "INNOVATION / UNIQUENESS")
    inn_points = [
        ("Positive Detection + Derived Absence:", "Avoids training noisy negative classes (e.g. no_helmet). Positively detects items and verifies anatomical overlap with tracked worker bodies."),
        ("Strict Ambiguity Invariant (UNKNOWN != VIOLATION):", "Partial machine occlusions or boundary clipping yield an UNKNOWN state; UNKNOWN strictly never triggers false violation alarms."),
        ("Zero-Biometric Privacy Architecture:", "Employs anonymous ByteTrack integer track IDs (Track #101); zero facial recognition, zero facial vector storage, and zero PII collected.")
    ]
    for itit, idesc in inn_points:
        p = c_s2_inn.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = f"• {itit} "
        r1.font.size = Pt(9.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = idesc
        r2.font.size = Pt(9)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Card 3: Key Features (Verified Implemented Features)
    c_s2_feat = add_card(s2, Inches(0.8), Inches(4.45), Inches(11.733), Inches(2.6), "KEY FEATURES (VERIFIED IMPLEMENTED FEATURES)")
    kf_left = [
        "• Real-Time PPE Compliance: 4-zone anatomical association (Head, Torso, Hands, Feet)",
        "• Worker-Level PPE Association: Nearest-centroid IoU mapping eliminates double-counting",
        "• Helmet & Safety Vest Detection: High-confidence cranial and thoracic coverage validation",
        "• Protective Gloves & Footwear: Distal limb detection with far-field UNKNOWN suppression",
        "• Fire and Smoke Detection: Dual-channel 7-stage state machine (N_confirm = 5 frames)"
    ]
    kf_right = [
        "• Temporal Validation: N_confirm = 3 consecutive frames eliminates 1-frame false alarms",
        "• Location-Specific Policy: Declarative YAML zone rules (e.g. mandatory boots in Loading Dock)",
        "• Multi-Camera Monitoring: Thread-isolated RTSP, USB Webcam, HTTP MJPEG, and file inputs",
        "• Real-Time Dashboard: React 18 SOC interface with live video HUD & WebSocket streaming",
        "• Incident & Evidence Tracking: SHA-256 hashed photographic snapshots & 60s alert cooldown"
    ]
    for i in range(len(kf_left)):
        p = c_s2_feat.add_paragraph()
        p.space_after = Pt(2.5)
        p.text = f"{kf_left[i]:<60}  {kf_right[i]}"
        p.font.size = Pt(9)
        p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 3 — TECHNICAL APPROACH
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_header(s3, 3, "TECHNICAL APPROACH", "Production-Grade AI Pipeline, Decoupled Architecture & Real Prototype Evidence")

    # Column 1: Technologies Used (Inches 0.8 to 4.4)
    c_s3_tech = add_card(s3, Inches(0.8), Inches(1.7), Inches(3.6), Inches(5.35), "TECHNOLOGIES USED")
    tech_lines = [
        ("Programming Languages:", "Python 3.13, TypeScript, SQL"),
        ("Frameworks:", "FastAPI, React 18, Vite 6, Tailwind CSS, PyTorch 2.14.0+cpu, OpenCV"),
        ("AI/ML Models:", "Ultralytics YOLOv8n (384x384), ByteTrack 8-State Kalman Filter"),
        ("Database:", "SQLite (WAL Mode, PRAGMA synchronous=NORMAL, 5000ms busy timeout)"),
        ("APIs:", "Async REST APIs, WebSockets (/ws/events, /ws/alerts), Prometheus /metrics"),
        ("Hardware / Sensors:", "13th Gen Intel Core i5 CPU, USB Webcams, IP Cameras, RTSP Feeds")
    ]
    for lbl, val in tech_lines:
        p = c_s3_tech.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = f"{lbl}\n"
        r1.font.size = Pt(9.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = val
        r2.font.size = Pt(8.8)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Column 2: Methodology & System Architecture / Flow (Inches 4.6 to 8.6)
    c_s3_flow = add_card(s3, Inches(4.6), Inches(1.7), Inches(4.0), Inches(5.35), "METHODOLOGY & SYSTEM ARCHITECTURE")
    p = c_s3_flow.add_paragraph()
    p.text = "Step-by-Step Methodology:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    steps = [
        "1. Ingestion: Thread-isolated worker buffers frame (Queue depth = 1).",
        "2. AI Detection: Single-pass YOLOv8n outputs 7 canonical classes.",
        "3. Tracking: ByteTrack links worker Kalman trajectories anonymously.",
        "4. Spatial Zoning: Maps PPE to Head (25%), Torso (20-70%), Hands, Feet.",
        "5. Debouncing: Requires N_confirm = 3 frames (PPE) or N=5 (Hazard).",
        "6. Risk & Push: Calculates 0-100 risk score; dispatches via WebSockets."
    ]
    for st in steps:
        p = c_s3_flow.add_paragraph()
        p.space_after = Pt(1.5)
        p.text = st
        p.font.size = Pt(8.2)
        p.font.color.rgb = COLOR_TEXT_DARK

    p = c_s3_flow.add_paragraph()
    p.space_before = Pt(4)
    p.text = "System Architecture / Flow:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    pipe_diagram = """Camera / CCTV / Video Feed
         ↓
Frame Capture (Queue Depth = 1)
         ↓
AI Detection (Ultralytics YOLOv8n)
         ↓
Person + PPE + Hazard Detection
         ↓
Worker Tracking (ByteTrack)
         ↓
PPE Association (4-Zone Geometry)
         ↓
Temporal Validation (N_confirm = 3)
         ↓
Safety / Risk Engine (0-100 Score)
         ↓
Incident & Alert Engine (60s Cooldown)
         ↓
Database (WAL) + WebSocket Gateway
         ↓
SafeSync React 18 Dashboard"""
    p = c_s3_flow.add_paragraph()
    p.text = pipe_diagram
    p.font.size = Pt(7.6)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Column 3: Working Prototype / Demo (Inches 8.8 to 12.5)
    c_s3_demo = add_card(s3, Inches(8.8), Inches(1.7), Inches(3.733), Inches(5.35), "WORKING PROTOTYPE / DEMO")
    p = c_s3_demo.add_paragraph()
    p.text = "Live Implementation Evidence:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    stats = [
        ("Unit Test Suite:", "250 / 250 Passing (100% Pass Rate)"),
        ("Integration Suite:", "39 / 39 Real-World Scenarios Passing"),
        ("End-to-End Recovery:", "20 / 20 Matrix Tests Verified"),
        ("Measured Latency:", "56.45 ms/frame (~18 FPS on CPU)"),
        ("Optical Challenge:", "0 / 13 False Positives (100% Rejection)")
    ]
    for slbl, sval in stats:
        p = c_s3_demo.add_paragraph()
        p.space_after = Pt(1.5)
        r1 = p.add_run()
        r1.text = f"• {slbl} "
        r1.font.size = Pt(8.2)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_TEXT_DARK
        r2 = p.add_run()
        r2.text = sval
        r2.font.size = Pt(8.2)
        r2.font.color.rgb = COLOR_GREEN

    # Real Model Prediction Artifact Image
    img_asset = os.path.join("BPUT-HACKATHON-2026", "assets", "val_batch0_pred.jpg")
    if os.path.exists(img_asset):
        s3.shapes.add_picture(img_asset, Inches(8.95), Inches(3.85), Inches(3.45), Inches(3.05))

    # =========================================================================
    # SLIDE 4 — FEASIBILITY AND VIABILITY
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_header(s4, 4, "FEASIBILITY AND VIABILITY", "Technical Feasibility, Financial Viability, Operational Workflow & Mitigations")

    # Card 1: Technical & Financial Feasibility
    c_s4_tf = add_card(s4, Inches(0.8), Inches(1.7), Inches(5.7), Inches(2.6), "TECHNICAL & FINANCIAL FEASIBILITY")
    p = c_s4_tf.add_paragraph()
    p.text = "TECHNICAL FEASIBILITY (VERIFIED ON REAL HARDWARE)"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(1.5)

    tf_pts = [
        "• AI Model: YOLOv8n (3.2M params) operates at 384x384 input resolution with SHA-256 integrity check.",
        "• Hardware Requirements: Validated on commodity 13th Gen Intel Core i5 CPU without requiring discrete GPUs.",
        "• Camera/Video Compatibility: Ingests standard USB Webcams, HTTP MJPEG, RTSP feeds, and video files.",
        "• Real-Time Capability: Sustains ~56.45 ms latency (17.7 FPS) on CPU with bounded queue depth 1."
    ]
    for b in tf_pts:
        p = c_s4_tf.add_paragraph()
        p.space_after = Pt(1.5)
        p.text = b
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_DARK

    p = c_s4_tf.add_paragraph()
    p.space_before = Pt(3)
    p.text = "FINANCIAL FEASIBILITY"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(1.5)

    p = c_s4_tf.add_paragraph()
    p.text = "• Eliminates Dedicated AI Server Hardware: Runs directly on existing edge or plant PCs.\n• Zero Licensing Costs: 100% open-source software stack (Python, FastAPI, React, SQLite, PyTorch).\n• Retrofit Compatibility: Connects with existing plant CCTV infrastructure without camera re-cabling."
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Card 2: Operational Feasibility
    c_s4_of = add_card(s4, Inches(6.8), Inches(1.7), Inches(5.7), Inches(2.6), "OPERATIONAL FEASIBILITY")
    p = c_s4_of.add_paragraph()
    p.text = "REAL-WORLD INDUSTRIAL CONTROL-ROOM WORKFLOW"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2)

    of_pts = [
        "• CCTV / Video Monitoring: Continuous automated surveillance operates 24/7 without vigilance fatigue.",
        "• Live Operator Dashboard: Real-time multi-camera grid with per-worker Checklist HUD badges.",
        "• Color-Coded Alert HUD: Green (PRESENT), Red (ABSENT violation), and Gray (UNKNOWN non-alerting).",
        "• Human-in-the-Loop Actions: Control room operators can Acknowledge, Resolve, or Dismiss alerts.",
        "• Multi-Camera Thread Isolation: Ingestion failures on one camera thread never crash neighboring feeds."
    ]
    for b in of_pts:
        p = c_s4_of.add_paragraph()
        p.space_after = Pt(2)
        p.text = b
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_DARK

    # Card 3: Challenges / Risks (Challenge -> Solution)
    c_s4_cr = add_card(s4, Inches(0.8), Inches(4.5), Inches(7.5), Inches(2.55), "CHALLENGES / RISKS & VERIFIED MITIGATIONS")
    cr_data = [
        ("False PPE Absences on Occlusion", "Strict UNKNOWN != VIOLATION policy suppresses alerts during boundary clipping or machine obstruction."),
        ("Hair or Clothing Confusion", "Multi-frame debouncing (N_confirm = 3 consecutive frames) filters transient 1-frame misclassifications."),
        ("Steam, Dust & Welding Glare", "Dual-channel 7-stage state machine (N=5) and negative training data; verified 0/13 false positives."),
        ("Limited Edge CPU Resources", "Thread-isolated latest-frame-wins ingestion (Queue depth = 1) avoids buffer growth and memory bloat."),
        ("Camera or Network Disconnections", "Bounded exponential backoff reconnection loop automatically re-establishes dropped video feeds.")
    ]
    for chal, sol in cr_data:
        p = c_s4_cr.add_paragraph()
        p.space_after = Pt(2.5)
        r1 = p.add_run()
        r1.text = f"• Challenge: {chal}\n  → Solution: "
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = sol
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Card 4: Scalability / Future Scope
    c_s4_sc = add_card(s4, Inches(8.5), Inches(4.5), Inches(4.033), Inches(2.55), "SCALABILITY / FUTURE SCOPE")
    p = c_s4_sc.add_paragraph()
    p.text = "Planned Engineering Roadmap:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2.5)

    scope_pts = [
        "• [FUTURE] INT8 TensorRT & ONNX Runtime: Quantization for low-power NVIDIA Jetson Orin edge nodes (>60 FPS).",
        "• [FUTURE] Physical Factory CCTV Pilot: On-site multi-week trial deployment under continuous 72-hour load.",
        "• [FUTURE] Automated PLC Interlocks: Integration with Modbus TCP & MQTT to automatically halt dangerous machinery.",
        "• [FUTURE] Expanded Safety Gear: High-angle safety harnesses, welding face-shields, and hearing protection."
    ]
    for itm in scope_pts:
        p = c_s4_sc.add_paragraph()
        p.space_after = Pt(2.5)
        p.text = itm
        p.font.size = Pt(8.2)
        p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 5 — IMPACT AND BENEFITS
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_header(s5, 5, "IMPACT AND BENEFITS", "Value Proposition, Multi-Sector Real-World Applications & Realistic Impact")

    # Card 1: Target Users & Expected Impact
    c_s5_usr = add_card(s5, Inches(0.8), Inches(1.7), Inches(5.7), Inches(2.55), "TARGET USERS & EXPECTED IMPACT")
    p = c_s5_usr.add_paragraph()
    p.text = "TARGET OPERATIONAL PERSONAS"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(1.5)

    u_pts = [
        "• Industrial Safety Officers & EHS Managers: Centralized real-time compliance oversight.",
        "• Control-Room Operators: Prioritized visual incident alerts and checklist HUDs.",
        "• Plant Operations Directors: Tamper-evident visual audit trails for regulatory defense.",
        "• Industrial Enterprises: Facility-wide monitoring without hiring dedicated surveillance staff."
    ]
    for u in u_pts:
        p = c_s5_usr.add_paragraph()
        p.space_after = Pt(1.5)
        p.text = u
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_TEXT_DARK

    p = c_s5_usr.add_paragraph()
    p.space_before = Pt(3)
    p.text = "EXPECTED OPERATIONAL IMPACT"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(1.5)

    p = c_s5_usr.add_paragraph()
    p.text = "Automated visual safety monitoring eliminates human observer fatigue and spot-check blind spots. By alerting safety teams within seconds of sustained gear removal and detecting incipient flames before physical smoke alarms trigger, SafeSync actively mitigates severe workplace casualties."
    p.font.size = Pt(8.5)
    p.font.color.rgb = COLOR_TEXT_DARK

    # Card 2: Categorized Benefits
    c_s5_ben = add_card(s5, Inches(6.8), Inches(1.7), Inches(5.7), Inches(2.55), "MULTIDIMENSIONAL BENEFITS")
    ben_pts = [
        ("Social Benefits:", "Protects human life and worker physical integrity; upholds worker dignity through zero-biometric anonymous tracking."),
        ("Economic Benefits:", "Reduces catastrophic equipment downtime, lowers workers' compensation liabilities, and prevents regulatory fines."),
        ("Technological Benefits:", "Delivers production-grade edge AI execution on commodity CPU hardware with explainable risk scoring."),
        ("Environmental Benefits:", "Rapid flame and smoke plume detection prevents uncontrolled industrial fires and toxic atmospheric emissions.")
    ]
    for blbl, bdesc in ben_pts:
        p = c_s5_ben.add_paragraph()
        p.space_after = Pt(2.5)
        r1 = p.add_run()
        r1.text = f"• {blbl} "
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = bdesc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Card 3: Real-World Applications & Long-Term Scalability
    c_s5_app = add_card(s5, Inches(0.8), Inches(4.45), Inches(11.733), Inches(2.6), "REAL-WORLD APPLICATIONS & LONG-TERM SCALABILITY")
    p = c_s5_app.add_paragraph()
    p.text = "HIGH-HAZARD INDUSTRIAL SECTORS"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(2.5)

    app_pts = [
        ("Heavy Manufacturing & Fabrication:", "Active overhead crane zones, press bays, and CNC machining lines requiring helmets, vests, and fire vigilance."),
        ("Construction & Infrastructure Sites:", "High-traffic perimeter gates, scaffold zones, and heavy earth-moving equipment pathways."),
        ("Chemical Processing & Storage Hubs:", "Volatile liquid storage, hazardous warehousing, and battery charging bays requiring rapid smoke warning."),
        ("Metal Smelting & Power Plants:", "Turbine floors, boiler halls, and electrical sub-stations requiring high-temperature flame monitoring.")
    ]
    for albl, adesc in app_pts:
        p = c_s5_app.add_paragraph()
        p.space_after = Pt(2)
        r1 = p.add_run()
        r1.text = f"• {albl} "
        r1.font.size = Pt(8.8)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_TEXT_DARK
        r2 = p.add_run()
        r2.text = adesc
        r2.font.size = Pt(8.8)
        r2.font.color.rgb = COLOR_TEXT_MUTED

    p = c_s5_app.add_paragraph()
    p.space_before = Pt(3.5)
    p.text = "LONG-TERM SCALABILITY & EVOLUTION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.space_after = Pt(1.5)

    p = c_s5_app.add_paragraph()
    p.text = "SafeSync is built as a modular edge safety platform. By keeping vision inference decoupled from administrative policy, individual plants can scale from a single standalone camera to enterprise-wide distributed networks with centralized cloud reporting and localized edge autonomy."
    p.font.size = Pt(8.8)
    p.font.color.rgb = COLOR_TEXT_DARK

    # =========================================================================
    # SLIDE 6 — RESEARCH AND REFERENCES
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_header(s6, 6, "RESEARCH AND REFERENCES", "Foundational Research, Verified Datasets, Frameworks & Regulatory Compliance Standards")

    # Card 1: Research Papers / Journals (Inches 0.8 to 6.4)
    c_s6_rp = add_card(s6, Inches(0.8), Inches(1.7), Inches(5.7), Inches(2.65), "RESEARCH PAPERS / JOURNALS")
    papers_data = [
        ("Ultralytics YOLOv8 (2023):", "Anchor-free neural architecture providing efficient real-time multi-task object detection at the edge.\nhttps://github.com/ultralytics/ultralytics"),
        ("ByteTrack Multi-Object Tracking (ECCV 2022):", "Associates both high- and low-confidence detection boxes to maintain robust worker trajectories through occlusions.\nhttps://arxiv.org/abs/2110.06864"),
        ("CPPE-5 Benchmark (CVPR Workshop 2021):", "Challenging Personal Protective Equipment Dataset establishing visual multi-class safety evaluation criteria.\nhttps://arxiv.org/abs/2112.07253"),
        ("D-Fire Combustion Dataset (IEEE Access 2022):", "Benchmark research for optical flame and smoke detection and boundary localization.\nhttps://github.com/gaia-solutions-on-demand/DFireDataset")
    ]
    for ptit, pdesc in papers_data:
        p = c_s6_rp.add_paragraph()
        p.space_after = Pt(3)
        r1 = p.add_run()
        r1.text = f"• {ptit} "
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = pdesc
        r2.font.size = Pt(8)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Card 2: Datasets Actually Used & Referenced (Inches 6.8 to 12.5)
    c_s6_ds = add_card(s6, Inches(6.8), Inches(1.7), Inches(5.7), Inches(2.65), "DATASETS (ACTUALLY USED & REFERENCED)")
    datasets_data = [
        ("Pictor Construction Safety [ACTUALLY USED]:", "1,487 images of real construction personnel, helmets, and vests.\nhttps://github.com/carlosh93/pictor-ppe"),
        ("Hard Hat Workers [ACTUALLY USED]:", "7,035 images covering multi-angle worker headwear and safety vests.\nhttps://public.roboflow.com/object-detection/hard-hat-workers"),
        ("Construction Site Safety [ACTUALLY USED]:", "9,451 images covering helmets, vests, gloves, and protective boots.\nhttps://universe.roboflow.com/roboflow-universe-projects/construction-site-safety"),
        ("D-Fire Combustion Dataset [ACTUALLY USED]:", "4,480 images of active flames and industrial smoke plumes.\nhttps://github.com/gaia-solutions-on-demand/DFireDataset"),
        ("SH17 & Ultralytics PPE [REFERENCED / EVALUATED]:", "Evaluated for benchmark ontology alignment and training hyperparameters.")
    ]
    for dtit, ddesc in datasets_data:
        p = c_s6_ds.add_paragraph()
        p.space_after = Pt(2.5)
        r1 = p.add_run()
        r1.text = f"• {dtit} "
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = ddesc
        r2.font.size = Pt(8)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Card 3: Frameworks, Official Documentation, GitHub & Standards
    c_s6_ref = add_card(s6, Inches(0.8), Inches(4.5), Inches(11.733), Inches(2.55), "FRAMEWORKS, OFFICIAL DOCUMENTATION, GITHUB & SAFETY STANDARDS")
    ref_data = [
        ("FastAPI & Uvicorn:", "High-concurrency asynchronous Python ASGI web framework and WebSockets. https://fastapi.tiangolo.com"),
        ("React 18 & Vite:", "Declarative component-driven frontend architecture with sub-millisecond DOM updates. https://react.dev"),
        ("SQLite WAL Engine:", "ACID-compliant relational persistence operating under Write-Ahead Logging. https://sqlite.org/wal.html"),
        ("Official GitHub Repository:", "https://github.com/SMRU08/SafeSync.git (Live codebase, models & test suites)"),
        ("OSHA Standards:", "29 CFR 1926.100 (Head Protection) & 1926.95 (Personal Protective Equipment). https://www.osha.gov"),
        ("ISO 45001:2018:", "Occupational Health and Safety Management Systems Standard requirements. https://www.iso.org")
    ]
    for rtit, rdesc in ref_data:
        p = c_s6_ref.add_paragraph()
        p.space_after = Pt(2)
        r1 = p.add_run()
        r1.text = f"• {rtit} "
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_PRIMARY
        r2 = p.add_run()
        r2.text = rdesc
        r2.font.size = Pt(8)
        r2.font.color.rgb = COLOR_TEXT_DARK

    # Save to both target locations
    path1 = os.path.join("BPUT-HACKATHON-2026", "SafeSync-BPUT-HACKATHON-2026.pptx")
    path2 = "SafeSync-BPUT-HACKATHON-2026.pptx"

    prs.save(path1)
    prs.save(path2)
    print(f"Presentation successfully created with {len(prs.slides)} slides at:\n  - {path1}\n  - {path2}")

if __name__ == "__main__":
    build_presentation()
