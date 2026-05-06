"""External Auditor — Certify Reports"""
import streamlit as st
import httpx
import json
import hashlib
import hmac
from datetime import datetime
from utils.api_client import API_URL
from styles import (
    _header, _card_header, _alert_box,
    _ICON_SHIELD, _ICON_INFO, _ICON_CHECK, _ICON_WARNING, _ICON_ERROR, _ICON_HISTORY
)

TIMEOUT = 15

def _get_pinned_reports() -> list:
    try:
        r = httpx.get(f"{API_URL}/ipfs/list", timeout=TIMEOUT)
        if r.status_code == 200:
            files = r.json().get("files", [])
            return [f for f in files if "report" in f.get("name","").lower() or "certified" in f.get("name","").lower()]
    except:
        pass
    return []

def _get_report_content(cid: str) -> dict:
    try:
        r = httpx.get(f"{API_URL}/ipfs/get/{cid}", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            return data.get("content", data)
    except:
        pass
    return {}

def _generate_signature(content: str, auditor_id: str) -> str:
    key = f"{auditor_id}-external-auditor-blockml-gov".encode()
    sig = hmac.new(key, content.encode(), hashlib.sha256).hexdigest()
    return f"EA-SIG-{sig[:32].upper()}"

def _certify_report(report: dict, cid: str, auditor_id: str, signature: str, notes: str) -> dict:
    certified = {
        "original_cid":    cid,
        "original_report": report,
        "certified_by":    auditor_id,
        "certified_at":    datetime.utcnow().isoformat(),
        "signature":       signature,
        "notes":           notes,
        "status":          "CERTIFIED",
        "ready_for_regulator": True,
    }
    try:
        r = httpx.post(
            f"{API_URL}/ipfs/pin-json",
            json={"data": certified, "name": f"certified-{cid[:16]}"},
            timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def show(user: dict):
    _header("Report Certification", _ICON_SHIELD)
    st.markdown("""<style>
      .stTabs [data-baseweb="tab-list"] button { color:#1C1C1C!important; font-weight:600!important; }
      .stTabs [data-baseweb="tab-list"] button p { color:#1C1C1C!important; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color:#1F7A5A!important; }
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color:#1F7A5A!important; }
    </style>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Certify Reports", "Certified Reports"])

    with tab1:
        _card_header("Pending Reports — Internal Auditor", _ICON_HISTORY)

        with st.spinner("Loading reports from IPFS..."):
            reports = _get_pinned_reports()

        if not reports:
            _alert_box("INFO", "No reports found on IPFS yet.", _ICON_INFO)
            return

        # Get certified CIDs to check which reports are already certified
        certified_cids = set()
        for r in reports:
            if "certified" in r.get("name","").lower():
                # Extract original CID from certified report name
                orig_cid = r.get("name","").replace("certified-","")[:16]
                certified_cids.add(orig_cid)

        uncertified = [r for r in reports 
                      if "certified" not in r.get("name","").lower()
                      and r.get("cid","")[:16] not in certified_cids]
        if uncertified:
            _alert_box("WARNING", f"{len(uncertified)} report(s) pending certification", _ICON_WARNING)
        else:
            _alert_box("SUCCESS", "All reports are certified!", _ICON_CHECK)

        for rep in reports:
            name = rep.get("name", "")
            cid  = rep.get("cid",  "")
            is_certified = "certified" in name.lower() or cid[:16] in certified_cids
            status_icon = "✅" if is_certified else "⏳"

            with st.expander(f"**{name}** — {'CERTIFIED' if is_certified else 'PENDING'}"):
                st.markdown(f"**CID:** `{cid}`")

                if is_certified:
                    _alert_box("SUCCESS", "Certified — available to Regulator", _ICON_CHECK)
                    continue

                # Load button
                load_key = f"loaded_{cid}"
                if st.button("Load & Verify", key=f"verify_{cid[:8]}"):
                    with st.spinner("Fetching from IPFS..."):
                        content = _get_report_content(cid)
                    if content:
                        st.session_state[load_key] = content
                        _alert_box("SUCCESS", "Report loaded!", _ICON_CHECK)
                    else:
                        _alert_box("ERROR", "Could not retrieve report", _ICON_ERROR)

                # Show certification form if loaded
                if load_key in st.session_state:
                    content = st.session_state[load_key]
                    st.json(content)

                    content_str = json.dumps(content, sort_keys=True)
                    integrity_hash = hashlib.sha256(content_str.encode()).hexdigest()
                    st.code(f"Integrity Hash: {integrity_hash}")

                    st.markdown("---")
                    st.markdown("**Your Decision:**")
                    note = st.text_area(
                        "Notes (required)",
                        placeholder="e.g. Verified all metrics and compliance...",
                        key=f"notes_{cid}",
                        height=80)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Certify & Sign", key=f"certify_{cid[:8]}", type="primary", use_container_width=True):
                            if len(note) < 10:
                                st.error("Min 10 chars required")
                            else:
                                auditor_id = user.get("username", "external.auditor")
                                signature  = _generate_signature(content_str, auditor_id)
                                with st.spinner("Certifying..."):
                                    result = _certify_report(content, cid, auditor_id, signature, note)
                                if result.get("cid"):
                                    _alert_box("SUCCESS", f"Report certified! &nbsp; CID: <code>{result['cid']}</code>", _ICON_CHECK)
                                    del st.session_state[load_key]
                                    st.rerun()
                                else:
                                    _alert_box("ERROR", str(result), _ICON_ERROR)
                    with col2:
                        if st.button("Reject", key=f"reject_{cid[:8]}", use_container_width=True):
                            if len(note) < 10:
                                st.error("Min 10 chars required")
                            else:
                                from datetime import datetime as _dt
                                import httpx as _httpx
                                try:
                                    _httpx.post(f"{API_URL}/ipfs/pin-json",
                                        json={"data": {"original_cid": cid, "status": "REJECTED", "reason": note, "rejected_by": user.get("username",""), "rejected_at": _dt.utcnow().isoformat()},
                                              "name": f"rejected-{name[:30]}"}, timeout=10)
                                except:
                                    pass
                                _alert_box("ERROR", "Report rejected!", _ICON_ERROR)
                                del st.session_state[load_key]
                                st.rerun()
    with tab2:
        _card_header("Certified Reports", _ICON_CHECK)
        with st.spinner("Loading..."):
            all_files = _get_pinned_reports()
            certified = [f for f in all_files if "certified" in f.get("name","").lower()]

        if not certified:
            _alert_box("INFO", "No certified reports yet.", _ICON_INFO)
        else:
            _alert_box("SUCCESS", f"{len(certified)} certified report(s)", _ICON_CHECK)
            for rep in certified:
                st.markdown(
                    f"<span style='color:#16A34A;font-weight:bold;'>&#10003;</span>"
                    f" **{rep.get('name','')}** — CID: `{rep.get('cid','')[:30]}...` — Ready for Regulator",
                    unsafe_allow_html=True)
