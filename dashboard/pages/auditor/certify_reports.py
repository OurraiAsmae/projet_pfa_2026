"""External Auditor — Certify Reports"""
import streamlit as st
import httpx
import json
import hashlib
import hmac
from datetime import datetime
from utils.api_client import API_URL

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
    st.title("🔐 External Auditor — Report Certification")
    st.caption("Verify and certify reports before submission to Regulator")

    tab1, tab2 = st.tabs(["🔐 Certify Reports", "📋 Certified Reports"])

    with tab1:
        st.subheader("📋 Pending Reports — Internal Auditor")

        with st.spinner("Loading reports from IPFS..."):
            reports = _get_pinned_reports()

        if not reports:
            st.info("No reports found on IPFS yet.")
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
            st.warning(f"⚠️ {len(uncertified)} report(s) pending certification")
        else:
            st.success("✅ All reports are certified!")

        for rep in reports:
            name = rep.get("name", "")
            cid  = rep.get("cid",  "")
            is_certified = "certified" in name.lower() or cid[:16] in certified_cids
            status_icon = "✅" if is_certified else "⏳"

            with st.expander(f"{status_icon} **{name}** — {'CERTIFIED' if is_certified else 'PENDING'}"):
                st.markdown(f"**CID:** `{cid}`")

                if is_certified:
                    st.success("✅ Certified — available to Regulator")
                    continue

                # Load button
                load_key = f"loaded_{cid}"
                if st.button("🔍 Load & Verify", key=f"verify_{cid[:8]}"):
                    with st.spinner("Fetching from IPFS..."):
                        content = _get_report_content(cid)
                    if content:
                        st.session_state[load_key] = content
                        st.success("✅ Report loaded!")
                    else:
                        st.error("❌ Could not retrieve report")

                # Show certification form if loaded
                if load_key in st.session_state:
                    content = st.session_state[load_key]
                    st.json(content)

                    content_str = json.dumps(content, sort_keys=True)
                    integrity_hash = hashlib.sha256(content_str.encode()).hexdigest()
                    st.code(f"Integrity Hash: {integrity_hash}")

                    st.markdown("---")
                    st.markdown("**✍️ Certify this Report:**")

                    notes = st.text_area(
                        "Certification Notes",
                        placeholder="e.g. Verified all metrics...",
                        key=f"notes_{cid}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Certify & Sign", key=f"certify_{cid[:8]}", type="primary", use_container_width=True):
                            if len(notes) < 20:
                                st.error("Please provide certification notes (min 20 chars)")
                            else:
                                auditor_id = user.get("username", "external.auditor")
                                signature  = _generate_signature(content_str, auditor_id)
                                with st.spinner("Certifying..."):
                                    result = _certify_report(content, cid, auditor_id, signature, notes)
                                if result.get("cid"):
                                    st.success("✅ Report certified!")
                                    st.code(f"Signature: {signature}\nCertified CID: {result['cid']}")
                                    st.info("📤 Report is now available to the Regulator.")
                                    del st.session_state[load_key]
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result}")
                    with col2:
                        if st.button("❌ Reject", key=f"reject_{cid[:8]}", use_container_width=True):
                            st.error("❌ Report rejected")
                            del st.session_state[load_key]
                            st.rerun()

    with tab2:
        st.subheader("📋 Certified Reports")
        with st.spinner("Loading..."):
            all_files = _get_pinned_reports()
            certified = [f for f in all_files if "certified" in f.get("name","").lower()]

        if not certified:
            st.info("No certified reports yet.")
        else:
            st.success(f"✅ {len(certified)} certified report(s)")
            for rep in certified:
                st.markdown(f"✅ **{rep.get('name','')}** — CID: `{rep.get('cid','')[:30]}...` — Ready for Regulator")
